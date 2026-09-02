#!/usr/bin/env python3
"""Exercise the published package through Chromium and the real local UI/API stack."""

from __future__ import annotations

import argparse
import json
import os
import socket
import subprocess
import sys
import tempfile
import time
import urllib.error
import urllib.request
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_ARTIFACT_ROOT = ROOT / "build" / "artifacts"
HOST = "127.0.0.1"
GOOD_MODEL = "fixture-good"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("artifact", type=Path, nargs="?", default=None)
    parser.add_argument("--artifact-root", type=Path, default=DEFAULT_ARTIFACT_ROOT)
    return parser.parse_args()


def latest_artifact(root: Path) -> Path:
    candidates = sorted(
        root.glob("**/*.zip"),
        key=lambda path: path.stat().st_mtime_ns,
        reverse=True,
    )
    if not candidates:
        raise RuntimeError(f"no built release artifact found under {root}")
    return candidates[0]


def safe_extract(archive: zipfile.ZipFile, destination: Path) -> None:
    root = destination.resolve()
    for member in archive.infolist():
        target = (destination / member.filename).resolve()
        if root != target and root not in target.parents:
            raise RuntimeError(f"unsafe ZIP member: {member.filename}")
    archive.extractall(destination)


def free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as listener:
        listener.bind((HOST, 0))
        return int(listener.getsockname()[1])


def wait_ready(url: str, process: subprocess.Popen[str], label: str) -> None:
    deadline = time.monotonic() + 20.0
    last_error: Exception | None = None
    while time.monotonic() < deadline:
        if process.poll() is not None:
            stdout, stderr = process.communicate()
            raise RuntimeError(
                f"{label} exited before readiness ({process.returncode})\n{stdout}\n{stderr}"
            )
        try:
            with urllib.request.urlopen(url, timeout=0.5) as response:
                if response.status == 200:
                    return
        except (OSError, urllib.error.URLError) as exc:
            last_error = exc
        time.sleep(0.05)
    raise RuntimeError(f"{label} did not become ready: {last_error}")


def assert_port_released(port: int, label: str) -> None:
    deadline = time.monotonic() + 5.0
    while time.monotonic() < deadline:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as probe:
            probe.settimeout(0.2)
            if probe.connect_ex((HOST, port)) != 0:
                return
        time.sleep(0.05)
    raise RuntimeError(f"{label} still owns {HOST}:{port} after shutdown")


def stop_process(process: subprocess.Popen[str] | None, label: str) -> None:
    if process is None or process.poll() is not None:
        return
    process.terminate()
    try:
        process.wait(timeout=5)
    except subprocess.TimeoutExpired as exc:
        process.kill()
        process.wait(timeout=5)
        raise RuntimeError(f"{label} did not stop cleanly") from exc


def install_wheel(extracted: Path, root: Path) -> Path:
    wheels = tuple((extracted / "python").glob("*.whl"))
    if len(wheels) != 1:
        raise RuntimeError(f"expected exactly one packaged wheel, found {len(wheels)}")

    environment = root / "venv"
    subprocess.run(
        ["uv", "venv", "--python", sys.executable, str(environment)],
        check=True,
        text=True,
        capture_output=True,
    )
    python = environment / ("Scripts/python.exe" if sys.platform == "win32" else "bin/python")

    requirements = root / "runtime-requirements.txt"
    subprocess.run(
        [
            "uv",
            "export",
            "--locked",
            "--extra",
            "ui",
            "--no-dev",
            "--no-emit-project",
            "--format",
            "requirements-txt",
            "--output-file",
            str(requirements),
        ],
        cwd=ROOT,
        check=True,
        text=True,
        capture_output=True,
    )
    subprocess.run(
        ["uv", "pip", "sync", "--python", str(python), str(requirements)],
        cwd=ROOT,
        check=True,
        text=True,
        capture_output=True,
    )
    subprocess.run(
        ["uv", "pip", "install", "--python", str(python), "--no-deps", str(wheels[0])],
        check=True,
        text=True,
        capture_output=True,
    )
    return python


def write_run_config(path: Path, *, fixture_port: int, store_path: Path) -> None:
    base_url = f"http://{HOST}:{fixture_port}"
    payload = {
        "schema_version": 1,
        "target_id": "packaged-product-fixture",
        "endpoint_identity": base_url,
        "endpoint": {
            "profile_id": "packaged-product-fixture",
            "base_url": f"{base_url}/v1/",
            "model_selector": GOOD_MODEL,
            "timeout_seconds": 5.0,
        },
        "model_id": GOOD_MODEL,
        "store_path": str(store_path),
        "local_llm_server_identity": {
            "base_url": base_url,
            "model_id": GOOD_MODEL,
            "timeout_seconds": 1.0,
            "required": True,
        },
        "local_llm_server_telemetry": {
            "base_url": base_url,
            "model_id": GOOD_MODEL,
            "sample_interval_seconds": 0.01,
            "timeout_seconds": 1.0,
        },
    }
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def run_full_product_e2e(artifact: Path) -> None:
    if not artifact.is_file():
        raise RuntimeError(f"artifact does not exist: {artifact}")

    with tempfile.TemporaryDirectory(prefix="performance-lab-full-e2e-") as directory:
        root = Path(directory)
        extracted = root / "artifact"
        extracted.mkdir()
        with zipfile.ZipFile(artifact) as archive:
            safe_extract(archive, extracted)
        if not (extracted / "web" / "index.html").is_file():
            raise RuntimeError("packaged artifact is missing web/index.html")

        python = install_wheel(extracted, root)
        fixture_port = free_port()
        ui_port = free_port()
        config = root / "run-config.json"
        write_run_config(config, fixture_port=fixture_port, store_path=root / "runs.sqlite3")

        fixture: subprocess.Popen[str] | None = None
        product: subprocess.Popen[str] | None = None
        try:
            fixture = subprocess.Popen(
                [
                    sys.executable,
                    "tests/e2e/fixture_server.py",
                    "--port",
                    str(fixture_port),
                ],
                cwd=ROOT,
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )
            wait_ready(
                f"http://{HOST}:{fixture_port}/v1/models",
                fixture,
                "inference fixture",
            )

            product = subprocess.Popen(
                [
                    str(python),
                    "-m",
                    "performance_lab.ui_server",
                    "--config",
                    str(config),
                    "--assets",
                    str(extracted / "web"),
                    "--port",
                    str(ui_port),
                ],
                cwd=root,
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )
            wait_ready(f"http://{HOST}:{ui_port}/api/v1/health", product, "packaged product")

            environment = os.environ.copy()
            environment["PERFORMANCE_LAB_E2E_BASE_URL"] = f"http://{HOST}:{ui_port}"
            environment["PERFORMANCE_LAB_E2E_INFERENCE_BASE_URL"] = (
                f"http://{HOST}:{fixture_port}/v1/"
            )
            subprocess.run(
                ["pnpm", "--dir", "frontend", "run", "test:e2e:full-product"],
                cwd=ROOT,
                env=environment,
                check=True,
                text=True,
            )
        finally:
            stop_process(product, "packaged product")
            stop_process(fixture, "inference fixture")
            assert_port_released(ui_port, "packaged product")
            assert_port_released(fixture_port, "inference fixture")


def main() -> int:
    args = parse_args()
    try:
        artifact = (
            args.artifact.resolve()
            if args.artifact is not None
            else latest_artifact(args.artifact_root.resolve())
        )
        run_full_product_e2e(artifact)
    except (OSError, RuntimeError, subprocess.CalledProcessError, zipfile.BadZipFile) as exc:
        print(f"full-product E2E failed: {exc}", file=sys.stderr)
        return 1
    print("full-product E2E passed: packaged-product-fixture / representative_virtual")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
