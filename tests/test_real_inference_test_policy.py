from __future__ import annotations

import json
import subprocess
import sys
from importlib import util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REAL_RUNTIME_SCRIPT = ROOT / "tests" / "real_runtime" / "smoke_local_llm_server.py"


def _load_real_runtime_script():
    spec = util.spec_from_file_location("real_runtime_smoke_contract", REAL_RUNTIME_SCRIPT)
    assert spec is not None
    assert spec.loader is not None
    module = util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_runtime_1_requires_real_local_llm_server_environment() -> None:
    contract = json.loads((ROOT / ".engineering" / "e2e.json").read_text(encoding="utf-8"))
    environments = {item["id"]: item for item in contract["execution_environments"]}
    journeys = {item["id"]: item for item in contract["critical_journeys"]}

    real_runtime = environments["real-runtime-device"]
    assert real_runtime["automation"] == "real_environment"
    assert real_runtime["fidelity_class"] == "target_environment"
    assert "Local LLM Server" in real_runtime["artifact_surface"]

    runtime_1 = journeys["RUNTIME-1"]
    assert runtime_1["real_environment_confirmation"] == "required"
    assert "representative-ai-runtime-device" in runtime_1["target_environment_refs"]


def test_real_runtime_smoke_routes_model_inference_through_local_llm_server(
    tmp_path: Path,
    monkeypatch,
) -> None:
    module = _load_real_runtime_script()
    calls: list[tuple[tuple[str, ...], Path]] = []
    model_id = "nvidia/nemotron-3-nano-4b"
    source_revision = "test-source-revision"
    pre_real_manifest = tmp_path / "pre-real-manifest.json"
    pre_real_manifest.write_text(
        json.dumps(
            {
                "gate_id": "PRE_REAL_E2E",
                "status": "PASS",
                "ready_for_real_environment": True,
                "browser_layer": {"source_revision": source_revision},
            }
        ),
        encoding="utf-8",
    )
    bundle_path = tmp_path / "contract-test.plab.zip"

    def fake_run_cli(*args: str, cwd: Path) -> subprocess.CompletedProcess[str]:
        calls.append((args, cwd))
        if args[0] == "probe":
            return subprocess.CompletedProcess(
                args,
                0,
                stdout=json.dumps({"healthy": True, "models": [model_id]}),
                stderr="",
            )
        if args[0] == "run":
            bundle_path.write_bytes(b"portable-bundle-placeholder")
            return subprocess.CompletedProcess(
                args,
                0,
                stdout=json.dumps(
                    {
                        "run_id": "contract-test",
                        "status": "succeeded",
                        "fingerprint_id": "fingerprint-1",
                        "bundle_path": str(bundle_path),
                        "sample_count": 1,
                    }
                ),
                stderr="",
            )
        raise AssertionError(f"unexpected CLI call: {args}")

    monkeypatch.setattr(module, "_run_cli", fake_run_cli)
    monkeypatch.setattr(module, "_git_revision", lambda: source_revision)
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "smoke_local_llm_server.py",
            "--base-url",
            "http://127.0.0.1:1235",
            "--model",
            model_id,
            "--output-dir",
            str(tmp_path),
            "--run-id",
            "contract-test",
            "--pre-real-manifest",
            str(pre_real_manifest),
        ],
    )

    assert module.main() == 0

    assert len(calls) == 2
    probe_args, probe_cwd = calls[0]
    assert probe_args == (
        "probe",
        "--base-url",
        "http://127.0.0.1:1235/v1/",
        "--model",
        model_id,
        "--json",
    )
    assert probe_cwd == tmp_path.resolve()

    config_path = tmp_path / "contract-test.config.json"
    config = json.loads(config_path.read_text(encoding="utf-8"))
    assert config["endpoint"]["base_url"] == "http://127.0.0.1:1235/v1/"
    assert config["endpoint"]["model_selector"] == model_id
    assert config["evidence_mode"] == "evidence_rich"
    assert config["local_llm_server_identity"] == {
        "base_url": "http://127.0.0.1:1235",
        "model_id": model_id,
        "required": True,
        "timeout_seconds": 5.0,
    }
    assert config["local_llm_server_telemetry"]["base_url"] == "http://127.0.0.1:1235"
    assert config["local_llm_server_telemetry"]["model_id"] == model_id

    run_args, run_cwd = calls[1]
    assert run_args == ("run", "--config", str(config_path), "--json")
    assert run_cwd == tmp_path.resolve()

    retained_manifest = json.loads(
        (tmp_path / "contract-test.manifest.json").read_text(encoding="utf-8")
    )
    assert retained_manifest["status"] == "PASS"
    assert retained_manifest["source_revision"] == source_revision
    assert retained_manifest["bundle_path"] == str(bundle_path)
