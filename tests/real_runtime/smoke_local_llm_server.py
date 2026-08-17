from __future__ import annotations

import argparse
import json
import subprocess
import sys
from datetime import UTC, datetime
from pathlib import Path


def _run_cli(*args: str, cwd: Path) -> subprocess.CompletedProcess[str]:
    completed = subprocess.run(
        [sys.executable, "-m", "performance_lab.cli", *args],
        cwd=cwd,
        capture_output=True,
        text=True,
        check=False,
    )
    if completed.returncode != 0:
        raise RuntimeError(
            f"performance-lab {' '.join(args)} failed with exit {completed.returncode}\n"
            f"stdout:\n{completed.stdout}\nstderr:\n{completed.stderr}"
        )
    return completed


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Run a real Local LLM Server preflight plus the frozen Performance Lab starter suite."
        )
    )
    parser.add_argument("--base-url", default="http://127.0.0.1:1235")
    parser.add_argument("--model", required=True)
    parser.add_argument("--output-dir", type=Path, default=Path(".performance-lab/real-smoke"))
    parser.add_argument("--run-id", default=None)
    args = parser.parse_args()

    output_dir = args.output_dir.expanduser().resolve()
    output_dir.mkdir(parents=True, exist_ok=True)
    base_url = args.base_url.rstrip("/")
    run_id = args.run_id or datetime.now(UTC).strftime("real-smoke-%Y%m%dT%H%M%SZ")

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
    if not probe_payload.get("healthy"):
        raise RuntimeError("endpoint probe did not report healthy")
    if args.model not in probe_payload.get("models", []):
        raise RuntimeError(f"requested model is not advertised by /v1/models: {args.model}")

    store_path = output_dir / "runs.sqlite3"
    config_path = output_dir / f"{run_id}.config.json"
    config = {
        "schema_version": 1,
        "target_id": "local-llm-server-real-smoke",
        "endpoint_identity": base_url,
        "endpoint": {
            "profile_id": "local-llm-server-real-smoke",
            "base_url": f"{base_url}/v1/",
            "model_selector": args.model,
            "timeout_seconds": 120.0,
        },
        "model_id": args.model,
        "store_path": str(store_path),
        "run_id": run_id,
        "local_llm_server_identity": {
            "base_url": base_url,
            "model_id": args.model,
            "timeout_seconds": 5.0,
            "required": True,
        },
        "local_llm_server_telemetry": {
            "base_url": base_url,
            "model_id": args.model,
            "sample_interval_seconds": 0.05,
            "timeout_seconds": 5.0,
        },
    }
    config_path.write_text(
        json.dumps(config, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    run = _run_cli(
        "run",
        "--config",
        str(config_path),
        "--json",
        cwd=output_dir,
    )
    result = json.loads(run.stdout)
    result["config_path"] = str(config_path)
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
