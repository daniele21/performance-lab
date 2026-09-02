from __future__ import annotations

import argparse
import json
import subprocess
import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
DEFAULT_PRE_REAL_MANIFEST = ROOT / "build" / "pre-real-e2e" / "manifest.json"


def _run_cli(*args: str, cwd: Path) -> subprocess.CompletedProcess[str]:
    completed = subprocess.run(
        [sys.executable, "-m", "performance_lab.cli", *args],
        cwd=cwd,
        capture_output=True,
        text=True,
        check=False,
    )
    if completed.returncode != 0:
        message = completed.stderr.strip() or completed.stdout.strip() or "no command output"
        raise RuntimeError(
            f"performance-lab {' '.join(args)} failed with exit {completed.returncode}: "
            f"{message[:500]}"
        )
    return completed


def _git_revision() -> str:
    completed = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    revision = completed.stdout.strip()
    if completed.returncode != 0 or not revision:
        raise RuntimeError("cannot resolve Performance Lab source revision")
    return revision


def _load_pre_real_manifest(path: Path, *, source_revision: str) -> dict[str, Any]:
    try:
        raw: object = json.loads(path.read_text(encoding="utf-8"))
    except OSError as exc:
        raise RuntimeError(f"cannot read PRE_REAL manifest: {path}") from exc
    except json.JSONDecodeError as exc:
        raise RuntimeError(f"PRE_REAL manifest is invalid JSON: {path}") from exc
    if not isinstance(raw, dict):
        raise RuntimeError("PRE_REAL manifest must contain an object")
    if raw.get("gate_id") != "PRE_REAL_E2E":
        raise RuntimeError("PRE_REAL manifest has the wrong gate_id")
    if raw.get("status") != "PASS" or raw.get("ready_for_real_environment") is not True:
        raise RuntimeError("PRE_REAL readiness is not PASS/READY_FOR_REAL_ENVIRONMENT")
    browser_layer = raw.get("browser_layer")
    if not isinstance(browser_layer, dict):
        raise RuntimeError("PRE_REAL manifest is missing browser_layer provenance")
    if browser_layer.get("source_revision") != source_revision:
        raise RuntimeError("PRE_REAL evidence is stale for the current Performance Lab revision")
    return raw


def build_value01_config(
    *,
    base_url: str,
    model: str,
    run_id: str,
    store_path: Path,
) -> dict[str, Any]:
    normalized_base = base_url.rstrip("/")
    return {
        "schema_version": 1,
        "target_id": "local-llm-server-value01",
        "endpoint_identity": normalized_base,
        "endpoint": {
            "profile_id": "local-llm-server-value01",
            "base_url": f"{normalized_base}/v1/",
            "model_selector": model,
            "timeout_seconds": 120.0,
        },
        "model_id": model,
        "store_path": str(store_path),
        "run_id": run_id,
        "evidence_mode": "evidence_rich",
        "suite_id": "general-diagnostic-starter",
        "local_llm_server_identity": {
            "base_url": normalized_base,
            "model_id": model,
            "timeout_seconds": 5.0,
            "required": True,
        },
        "local_llm_server_telemetry": {
            "base_url": normalized_base,
            "model_id": model,
            "sample_interval_seconds": 0.05,
            "timeout_seconds": 5.0,
        },
    }


def _record_step(
    manifest: dict[str, Any],
    name: str,
    *,
    status: str,
    detail: str,
) -> None:
    steps = manifest.setdefault("steps", [])
    assert isinstance(steps, list)
    steps.append({"name": name, "status": status, "detail": detail})


def _write_manifest(path: Path, manifest: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Run the bounded VALUE-01 real Local LLM Server evidence loop from a source checkout."
        )
    )
    parser.add_argument("--base-url", default="http://127.0.0.1:1235")
    parser.add_argument(
        "--model",
        required=True,
        help="Local LLM Server runtime key or model id accepted by the inference endpoint.",
    )
    parser.add_argument("--output-dir", type=Path, default=Path(".performance-lab/value01-real"))
    parser.add_argument("--run-id", default=None)
    parser.add_argument(
        "--pre-real-manifest",
        type=Path,
        default=DEFAULT_PRE_REAL_MANIFEST,
        help="Exact-head PRE_REAL_E2E manifest that authorizes entering REAL_ENVIRONMENT.",
    )
    parser.add_argument("--manifest", type=Path, default=None)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    output_dir = args.output_dir.expanduser().resolve()
    output_dir.mkdir(parents=True, exist_ok=True)
    run_id = args.run_id or datetime.now(UTC).strftime("value01-real-%Y%m%dT%H%M%SZ")
    manifest_path = (
        args.manifest.expanduser().resolve()
        if args.manifest is not None
        else output_dir / f"{run_id}.manifest.json"
    )
    config_path = output_dir / f"{run_id}.config.json"
    store_path = output_dir / "runs.sqlite3"
    manifest: dict[str, Any] = {
        "schema_version": 1,
        "gate_id": "VALUE-01C",
        "status": "FAIL",
        "run_id": run_id,
        "model_id": args.model,
        "endpoint_identity": args.base_url.rstrip("/"),
        "config_path": str(config_path),
        "store_path": str(store_path),
        "steps": [],
    }

    try:
        source_revision = _git_revision()
        manifest["source_revision"] = source_revision
        _record_step(
            manifest,
            "source_revision",
            status="PASS",
            detail="current git revision recorded",
        )

        pre_real_path = args.pre_real_manifest.expanduser().resolve()
        _load_pre_real_manifest(pre_real_path, source_revision=source_revision)
        manifest["pre_real_manifest"] = str(pre_real_path)
        _record_step(
            manifest,
            "pre_real_readiness",
            status="PASS",
            detail="exact-head PRE_REAL_E2E authorizes REAL_ENVIRONMENT",
        )

        base_url = args.base_url.rstrip("/")
        probe = _run_cli(
            "probe",
            "--base-url",
            f"{base_url}/v1/",
            "--model",
            args.model,
            "--json",
            cwd=output_dir,
        )
        probe_payload = json.loads(probe.stdout)
        if not isinstance(probe_payload, dict) or not probe_payload.get("healthy"):
            raise RuntimeError("endpoint probe did not report healthy")
        models = probe_payload.get("models")
        if isinstance(models, list) and models and args.model not in models:
            raise RuntimeError("requested model is not present in /v1/models discovery")
        _record_step(
            manifest,
            "endpoint_probe",
            status="PASS",
            detail="real Local LLM Server endpoint and requested model are discoverable",
        )

        config = build_value01_config(
            base_url=base_url,
            model=args.model,
            run_id=run_id,
            store_path=store_path,
        )
        config_path.write_text(
            json.dumps(config, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        _record_step(
            manifest,
            "frozen_config",
            status="PASS",
            detail="exact evidence-rich identity/telemetry config retained",
        )

        run = _run_cli(
            "run",
            "--config",
            str(config_path),
            "--json",
            cwd=output_dir,
        )
        result: object = json.loads(run.stdout)
        if not isinstance(result, dict):
            raise RuntimeError("performance-lab run JSON output is not an object")
        if result.get("run_id") != run_id or result.get("status") != "succeeded":
            raise RuntimeError("real Performance Lab run did not finish successfully")
        bundle_raw = result.get("bundle_path")
        if not isinstance(bundle_raw, str) or not bundle_raw:
            raise RuntimeError("run result did not report a portable bundle path")
        bundle_path = Path(bundle_raw)
        if not bundle_path.is_absolute():
            bundle_path = (output_dir / bundle_path).resolve()
        if not bundle_path.is_file():
            raise RuntimeError("reported portable bundle does not exist")

        manifest["fingerprint_id"] = result.get("fingerprint_id")
        manifest["bundle_path"] = str(bundle_path)
        manifest["sample_count"] = result.get("sample_count")
        _record_step(
            manifest,
            "real_inference_run",
            status="PASS",
            detail="real inference completed and canonical store/bundle were retained",
        )
        manifest["status"] = "PASS"
    except KeyboardInterrupt:
        manifest["error"] = {"type": "KeyboardInterrupt", "message": "operator interrupted run"}
        _record_step(manifest, "operator_run", status="FAIL", detail="operator interrupted run")
        _write_manifest(manifest_path, manifest)
        print(json.dumps(manifest, indent=2, sort_keys=True))
        return 130
    except (OSError, RuntimeError, ValueError, json.JSONDecodeError) as exc:
        manifest["error"] = {"type": type(exc).__name__, "message": str(exc)[:500]}
        _record_step(manifest, "operator_run", status="FAIL", detail=str(exc)[:500])

    _write_manifest(manifest_path, manifest)
    manifest["manifest_path"] = str(manifest_path)
    print(json.dumps(manifest, indent=2, sort_keys=True))
    return 0 if manifest["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
