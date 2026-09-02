from __future__ import annotations

import importlib.util
import json
from pathlib import Path
from types import ModuleType

import pytest

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "tests" / "real_runtime" / "smoke_local_llm_server.py"


def _load_script() -> ModuleType:
    spec = importlib.util.spec_from_file_location("value01_real_smoke", SCRIPT)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_value01_config_requires_identity_telemetry_and_evidence_rich(tmp_path: Path) -> None:
    module = _load_script()
    config = module.build_value01_config(
        base_url="http://127.0.0.1:1235/",
        model="qwen",
        run_id="value01-real",
        store_path=tmp_path / "runs.sqlite3",
    )

    assert config["target_id"] == "local-llm-server-value01"
    assert config["endpoint_identity"] == "http://127.0.0.1:1235"
    assert config["endpoint"]["base_url"] == "http://127.0.0.1:1235/v1/"
    assert config["model_id"] == "qwen"
    assert config["evidence_mode"] == "evidence_rich"
    assert config["suite_id"] == "general-diagnostic-starter"
    assert config["local_llm_server_identity"]["required"] is True
    assert config["local_llm_server_identity"]["model_id"] == "qwen"
    assert config["local_llm_server_telemetry"]["model_id"] == "qwen"


def test_pre_real_manifest_must_match_exact_source_revision(tmp_path: Path) -> None:
    module = _load_script()
    manifest_path = tmp_path / "manifest.json"
    manifest_path.write_text(
        json.dumps(
            {
                "gate_id": "PRE_REAL_E2E",
                "status": "PASS",
                "ready_for_real_environment": True,
                "browser_layer": {"source_revision": "abc123"},
            }
        ),
        encoding="utf-8",
    )

    loaded = module._load_pre_real_manifest(manifest_path, source_revision="abc123")
    assert loaded["ready_for_real_environment"] is True

    with pytest.raises(RuntimeError, match="stale"):
        module._load_pre_real_manifest(manifest_path, source_revision="different")


def test_pre_real_manifest_must_authorize_real_environment(tmp_path: Path) -> None:
    module = _load_script()
    manifest_path = tmp_path / "manifest.json"
    manifest_path.write_text(
        json.dumps(
            {
                "gate_id": "PRE_REAL_E2E",
                "status": "FAIL",
                "ready_for_real_environment": False,
                "browser_layer": {"source_revision": "abc123"},
            }
        ),
        encoding="utf-8",
    )

    with pytest.raises(RuntimeError, match="not PASS"):
        module._load_pre_real_manifest(manifest_path, source_revision="abc123")
