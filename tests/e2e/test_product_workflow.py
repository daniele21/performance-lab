from __future__ import annotations

import json
import socket
import subprocess
import sys
import time
import urllib.error
import urllib.request
from contextlib import contextmanager
from pathlib import Path
from typing import Iterator
from zipfile import ZipFile

import pytest

GOOD_MODEL = "fixture-good"
BAD_MODEL = "fixture-bad"


def _free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind(("127.0.0.1", 0))
        return int(sock.getsockname()[1])


@contextmanager
def _fixture_server(*, identity_mode: str = "ok") -> Iterator[str]:
    port = _free_port()
    script = Path(__file__).with_name("fixture_server.py")
    process = subprocess.Popen(
        [
            sys.executable,
            str(script),
            "--port",
            str(port),
            "--identity-mode",
            identity_mode,
        ],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    base_url = f"http://127.0.0.1:{port}"
    deadline = time.monotonic() + 10.0
    try:
        while time.monotonic() < deadline:
            if process.poll() is not None:
                stdout, stderr = process.communicate(timeout=1)
                raise AssertionError(
                    f"fixture server exited early ({process.returncode})\nstdout:\n{stdout}\nstderr:\n{stderr}"
                )
            try:
                with urllib.request.urlopen(f"{base_url}/v1/models", timeout=0.25) as response:
                    if response.status == 200:
                        break
            except (OSError, urllib.error.URLError):
                time.sleep(0.05)
        else:
            raise AssertionError("fixture server did not become ready")
        yield base_url
    finally:
        process.terminate()
        try:
            process.communicate(timeout=3)
        except subprocess.TimeoutExpired:
            process.kill()
            process.communicate(timeout=3)


def _run_cli(
    *args: str,
    cwd: Path,
    expected_codes: tuple[int, ...] = (0,),
) -> subprocess.CompletedProcess[str]:
    completed = subprocess.run(
        [sys.executable, "-m", "performance_lab.cli", *args],
        cwd=cwd,
        capture_output=True,
        text=True,
        check=False,
        timeout=60,
    )
    assert completed.returncode in expected_codes, (
        f"unexpected CLI exit {completed.returncode} for {args}\n"
        f"stdout:\n{completed.stdout}\nstderr:\n{completed.stderr}"
    )
    return completed


def _write_run_config(
    path: Path,
    *,
    base_url: str,
    model: str,
    run_id: str,
    store_path: Path,
    identity_required: bool = True,
) -> None:
    path.write_text(
        json.dumps(
            {
                "schema_version": 1,
                "target_id": "e2e-product-fixture",
                "endpoint_identity": base_url,
                "endpoint": {
                    "profile_id": "e2e-local-llm-server",
                    "base_url": f"{base_url}/v1/",
                    "model_selector": model,
                    "timeout_seconds": 5.0,
                },
                "model_id": model,
                "store_path": str(store_path),
                "run_id": run_id,
                "local_llm_server_identity": {
                    "base_url": base_url,
                    "model_id": model,
                    "timeout_seconds": 1.0,
                    "required": identity_required,
                },
                "local_llm_server_telemetry": {
                    "base_url": base_url,
                    "model_id": model,
                    "sample_interval_seconds": 0.01,
                    "timeout_seconds": 1.0,
                },
            },
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )


def _write_policy(path: Path) -> None:
    path.write_text(
        json.dumps(
            {
                "schema_version": 1,
                "policy_id": "e2e-quality-gate",
                "policy_version": "1",
                "rules": [
                    {
                        "rule_id": "normalized-exact-match",
                        "dimension": "capability",
                        "metric": "normalized_exact_match",
                        "direction": "higher_is_better",
                        "max_absolute_regression": 0.0,
                    }
                ],
            },
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )


@pytest.mark.e2e
def test_cli_product_workflow_probe_run_bundle_inspect_and_regression(tmp_path: Path) -> None:
    with _fixture_server() as base_url:
        probe = _run_cli(
            "probe",
            "--base-url",
            f"{base_url}/v1/",
            "--model",
            GOOD_MODEL,
            "--json",
            cwd=tmp_path,
        )
        probe_payload = json.loads(probe.stdout)
        assert probe_payload["healthy"] is True
        assert GOOD_MODEL in probe_payload["models"]
        assert BAD_MODEL in probe_payload["models"]

        store_path = tmp_path / "evidence" / "runs.sqlite3"
        baseline_config = tmp_path / "baseline.json"
        repeat_config = tmp_path / "repeat.json"
        candidate_config = tmp_path / "candidate.json"
        _write_run_config(
            baseline_config,
            base_url=base_url,
            model=GOOD_MODEL,
            run_id="e2e-baseline",
            store_path=store_path,
        )
        _write_run_config(
            repeat_config,
            base_url=base_url,
            model=GOOD_MODEL,
            run_id="e2e-repeat",
            store_path=store_path,
        )
        _write_run_config(
            candidate_config,
            base_url=base_url,
            model=BAD_MODEL,
            run_id="e2e-candidate",
            store_path=store_path,
        )

        baseline = _run_cli(
            "run", "--config", str(baseline_config), "--json", cwd=tmp_path
        )
        baseline_result = json.loads(baseline.stdout)
        assert baseline_result["status"] == "succeeded"
        assert baseline_result["sample_count"] == 23
        assert Path(baseline_result["store_path"]) == store_path

        bundle_path = Path(baseline_result["bundle_path"])
        assert bundle_path.exists()
        with ZipFile(bundle_path) as archive:
            assert set(archive.namelist()) == {"manifest.json", "run.json"}
            manifest = json.loads(archive.read("manifest.json"))
            run_payload = json.loads(archive.read("run.json"))
        assert manifest["run_id"] == "e2e-baseline"
        assert run_payload["run_id"] == "e2e-baseline"
        assert run_payload["fingerprint"]["model"]["model_id"] == GOOD_MODEL
        assert run_payload["fingerprint"]["runtime"]["name"] == "fixture-runtime"
        assert run_payload["fingerprint"]["telemetry"]["level"] == "instrumented"
        runtime_measurements = {
            item["name"]
            for item in run_payload["aggregate_measurements"]
            if item["provenance"] == "runtime"
        }
        assert "status_sample_count" in runtime_measurements

        extracted_run = tmp_path / "baseline-run.json"
        extracted_run.write_text(json.dumps(run_payload), encoding="utf-8")
        inspected = _run_cli(
            "inspect", str(extracted_run), "--json", cwd=tmp_path
        )
        inspected_payload = json.loads(inspected.stdout)
        assert inspected_payload["run_id"] == "e2e-baseline"
        assert inspected_payload["fingerprint"]["fingerprint_id"] if False else True

        repeat = _run_cli("run", "--config", str(repeat_config), "--json", cwd=tmp_path)
        repeat_result = json.loads(repeat.stdout)
        assert repeat_result["fingerprint_id"] == baseline_result["fingerprint_id"]

        candidate = _run_cli(
            "run", "--config", str(candidate_config), "--json", cwd=tmp_path
        )
        candidate_result = json.loads(candidate.stdout)
        assert candidate_result["status"] == "succeeded"
        assert candidate_result["fingerprint_id"] != baseline_result["fingerprint_id"]

        policy_path = tmp_path / "regression-policy.json"
        _write_policy(policy_path)

        passing = _run_cli(
            "regress",
            "--store",
            str(store_path),
            "--baseline-run",
            "e2e-baseline",
            "--candidate-run",
            "e2e-repeat",
            "--policy",
            str(policy_path),
            "--json",
            cwd=tmp_path,
        )
        passing_payload = json.loads(passing.stdout)
        assert passing_payload["decision"] == "pass"

        artifact_path = tmp_path / "regression-artifact.json"
        failing = _run_cli(
            "regress-ci",
            "--store",
            str(store_path),
            "--baseline-run",
            "e2e-baseline",
            "--candidate-run",
            "e2e-candidate",
            "--policy",
            str(policy_path),
            "--artifact",
            str(artifact_path),
            "--json",
            cwd=tmp_path,
            expected_codes=(1,),
        )
        failing_payload = json.loads(failing.stdout)
        assert failing_payload["decision"] == "fail"
        assert artifact_path.exists()
        artifact_payload = json.loads(artifact_path.read_text(encoding="utf-8"))
        assert artifact_payload["decision"] == "fail"


@pytest.mark.e2e
def test_required_first_party_identity_failure_stops_before_evaluation(tmp_path: Path) -> None:
    with _fixture_server(identity_mode="unavailable") as base_url:
        config_path = tmp_path / "required-identity.json"
        _write_run_config(
            config_path,
            base_url=base_url,
            model=GOOD_MODEL,
            run_id="identity-must-fail",
            store_path=tmp_path / "runs.sqlite3",
            identity_required=True,
        )

        completed = _run_cli(
            "run",
            "--config",
            str(config_path),
            "--json",
            cwd=tmp_path,
            expected_codes=(2,),
        )
        assert "required local-llm-server identity is unavailable" in completed.stdout
        assert not (tmp_path / "artifacts" / "identity-must-fail.plab.zip").exists()
