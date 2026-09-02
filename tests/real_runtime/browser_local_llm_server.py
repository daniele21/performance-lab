from __future__ import annotations

import argparse
import json
import os
import socket
import subprocess
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
HOST = "127.0.0.1"


def _free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as listener:
        listener.bind((HOST, 0))
        return int(listener.getsockname()[1])


def _wait_ready(url: str, process: subprocess.Popen[str]) -> None:
    deadline = time.monotonic() + 30.0
    last_error: Exception | None = None
    while time.monotonic() < deadline:
        if process.poll() is not None:
            stdout, stderr = process.communicate()
            raise RuntimeError(
                f"Performance Lab exited before readiness ({process.returncode}): "
                f"{(stderr or stdout).strip()[:500]}"
            )
        try:
            with urllib.request.urlopen(url, timeout=0.5) as response:
                if response.status == 200:
                    return
        except (OSError, urllib.error.URLError) as exc:
            last_error = exc
        time.sleep(0.05)
    raise RuntimeError(f"Performance Lab did not become ready: {last_error}")


def _stop_process(process: subprocess.Popen[str] | None) -> None:
    if process is None or process.poll() is not None:
        return
    process.terminate()
    try:
        process.wait(timeout=5)
    except subprocess.TimeoutExpired as exc:
        process.kill()
        process.wait(timeout=5)
        raise RuntimeError("Performance Lab UI did not stop cleanly") from exc


def _assert_port_released(port: int) -> None:
    deadline = time.monotonic() + 5.0
    while time.monotonic() < deadline:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as probe:
            probe.settimeout(0.2)
            if probe.connect_ex((HOST, port)) != 0:
                return
        time.sleep(0.05)
    raise RuntimeError(f"Performance Lab still owns {HOST}:{port} after shutdown")


def build_browser_run_config(
    *,
    base_url: str,
    model: str,
    store_path: Path,
) -> dict[str, Any]:
    normalized_base = base_url.rstrip("/")
    return {
        "schema_version": 1,
        "target_id": "local-llm-server-value01-browser",
        "endpoint_identity": normalized_base,
        "endpoint": {
            "profile_id": "local-llm-server-value01-browser",
            "base_url": f"{normalized_base}/v1/",
            "model_selector": model,
            "timeout_seconds": 120.0,
        },
        "model_id": model,
        "store_path": str(store_path),
        "evidence_mode": "evidence_rich",
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


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run the VALUE-01 built-browser journey against a real Local LLM Server."
    )
    parser.add_argument("--base-url", default="http://127.0.0.1:1235")
    parser.add_argument("--model", required=True)
    parser.add_argument("--assets", type=Path, default=ROOT / "frontend" / "dist")
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path(".performance-lab/value01-real-browser"),
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    output_dir = args.output_dir.expanduser().resolve()
    output_dir.mkdir(parents=True, exist_ok=True)
    assets = args.assets.expanduser().resolve()
    if not (assets / "index.html").is_file():
        print(
            "real browser E2E failed: built frontend assets are missing; "
            "run the canonical build first",
            file=sys.stderr,
        )
        return 1

    config_path = output_dir / "browser-run-config.json"
    store_path = output_dir / "runs.sqlite3"
    config_path.write_text(
        json.dumps(
            build_browser_run_config(
                base_url=args.base_url,
                model=args.model,
                store_path=store_path,
            ),
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )

    ui_port = _free_port()
    product: subprocess.Popen[str] | None = None
    try:
        product = subprocess.Popen(
            [
                sys.executable,
                "-m",
                "performance_lab.ui_server",
                "--config",
                str(config_path),
                "--assets",
                str(assets),
                "--port",
                str(ui_port),
            ],
            cwd=ROOT,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        _wait_ready(f"http://{HOST}:{ui_port}/api/v1/health", product)

        environment = os.environ.copy()
        environment["PERFORMANCE_LAB_REAL_E2E_BASE_URL"] = f"http://{HOST}:{ui_port}"
        environment["PERFORMANCE_LAB_REAL_E2E_MODEL"] = args.model
        environment["PERFORMANCE_LAB_REAL_E2E_OUTPUT_DIR"] = str(output_dir / "artifacts")
        environment["PERFORMANCE_LAB_REAL_E2E_REPORT"] = str(output_dir / "report.json")
        completed = subprocess.run(
            [
                "pnpm",
                "--dir",
                "frontend",
                "exec",
                "playwright",
                "test",
                "--config",
                "playwright.real-runtime.config.ts",
            ],
            cwd=ROOT,
            env=environment,
            text=True,
            check=False,
        )
        if completed.returncode != 0:
            raise RuntimeError(f"real browser Playwright failed with exit {completed.returncode}")
    except (OSError, RuntimeError) as exc:
        print(f"real browser E2E failed: {exc}", file=sys.stderr)
        return 1
    finally:
        try:
            _stop_process(product)
        finally:
            _assert_port_released(ui_port)

    print(
        "real browser E2E passed: real-runtime-device / target_environment; "
        f"evidence retained under {output_dir}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
