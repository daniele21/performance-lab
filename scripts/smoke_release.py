#!/usr/bin/env python3
"""Smoke a built artifact and prove graceful zero-residue shutdown."""

from __future__ import annotations

import argparse
import json
import socket
import subprocess
import sys
import tempfile
import time
import urllib.error
import urllib.request
import zipfile
from pathlib import Path

from performance_lab.release_artifacts import read_manifest, sha256_file

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_ARTIFACT_ROOT = ROOT / "build" / "artifacts"
HOST = "127.0.0.1"


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


def verify_payload(extracted: Path) -> dict[str, object]:
    manifest = read_manifest(extracted / "build-manifest.json")
    files = manifest.get("payload_files")
    if not isinstance(files, list) or not files:
        raise RuntimeError("build manifest does not contain payload_files")
    for item in files:
        if not isinstance(item, dict):
            raise RuntimeError("invalid payload_files entry")
        relative = item.get("path")
        expected = item.get("sha256")
        if not isinstance(relative, str) or not isinstance(expected, str):
            raise RuntimeError("invalid payload file identity")
        path = extracted / relative
        if not path.is_file():
            raise RuntimeError(f"manifest payload missing from artifact: {relative}")
        actual = sha256_file(path)
        if actual != expected:
            raise RuntimeError(f"payload checksum mismatch: {relative}")
    if not (extracted / "web" / "index.html").is_file():
        raise RuntimeError("built artifact is missing web/index.html")
    wheels = tuple((extracted / "python").glob("*.whl"))
    if len(wheels) != 1:
        raise RuntimeError(f"expected exactly one packaged wheel, found {len(wheels)}")
    return manifest


def free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as listener:
        listener.bind((HOST, 0))
        return int(listener.getsockname()[1])


def request_text(url: str) -> str:
    with urllib.request.urlopen(url, timeout=1.0) as response:
        if response.status != 200:
            raise RuntimeError(f"unexpected HTTP status {response.status} for {url}")
        return response.read().decode("utf-8")


def wait_ready(port: int, process: subprocess.Popen[str]) -> None:
    deadline = time.monotonic() + 20
    last_error: Exception | None = None
    while time.monotonic() < deadline:
        if process.poll() is not None:
            stdout, stderr = process.communicate()
            raise RuntimeError(
                f"built product exited before readiness ({process.returncode})\n{stdout}\n{stderr}"
            )
        try:
            health = json.loads(request_text(f"http://{HOST}:{port}/api/v1/health"))
            page = request_text(f"http://{HOST}:{port}/")
            if health.get("status") == "ok" and 'id="root"' in page:
                return
        except (OSError, RuntimeError, json.JSONDecodeError, urllib.error.URLError) as exc:
            last_error = exc
        time.sleep(0.1)
    raise RuntimeError(f"built product did not become ready: {last_error}")


def assert_port_released(port: int) -> None:
    deadline = time.monotonic() + 5
    while time.monotonic() < deadline:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as probe:
            probe.settimeout(0.2)
            if probe.connect_ex((HOST, port)) != 0:
                return
        time.sleep(0.1)
    raise RuntimeError(f"project listener still owns {HOST}:{port} after shutdown")


def create_smoke_config(path: Path, store_path: Path) -> None:
    payload = {
        "schema_version": 1,
        "target_id": "release-smoke",
        "endpoint_identity": "release-smoke-loopback",
        "endpoint": {
            "profile_id": "release-smoke-endpoint",
            "base_url": "http://127.0.0.1:9/v1",
            "timeout_seconds": 1,
        },
        "model_id": "release-smoke-model",
        "store_path": str(store_path),
    }
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


def smoke(artifact: Path) -> None:
    if not artifact.is_file():
        raise RuntimeError(f"artifact does not exist: {artifact}")

    with tempfile.TemporaryDirectory(prefix="performance-lab-release-smoke-") as directory:
        root = Path(directory)
        extracted = root / "artifact"
        extracted.mkdir()
        with zipfile.ZipFile(artifact) as archive:
            safe_extract(archive, extracted)
        manifest = verify_payload(extracted)

        environment = root / "venv"
        subprocess.run(
        ["uv", "venv", "--python", sys.executable, "--system-site-packages", str(environment)],
        check=True,
        text=True,
        capture_output=True,
    )
        python = environment / ("Scripts/python.exe" if sys.platform == "win32" else "bin/python")
        wheel = next((extracted / "python").glob("*.whl"))
        subprocess.run(
            ["uv", "pip", "install", "--python", str(python), "--no-deps", str(wheel)],
            check=True,
            text=True,
            capture_output=True,
        )

        config = root / "smoke-config.json"
        create_smoke_config(config, root / "runs.sqlite3")
        port = free_port()
        process = subprocess.Popen(
            [
                str(python),
                "-m",
                "performance_lab.ui_server",
                "--config",
                str(config),
                "--assets",
                str(extracted / "web"),
                "--port",
                str(port),
            ],
            cwd=root,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        try:
            wait_ready(port, process)
        finally:
            if process.poll() is None:
                process.terminate()
                try:
                    process.wait(timeout=5)
                except subprocess.TimeoutExpired as exc:
                    process.kill()
                    process.wait(timeout=5)
                    raise RuntimeError("built product did not stop gracefully") from exc
        if process.returncode not in {0, -15}:
            stdout, stderr = process.communicate()
            raise RuntimeError(
                f"built product shutdown returned {process.returncode}\n{stdout}\n{stderr}"
            )
        assert_port_released(port)
        print(
            "smoke passed: "
            f"build={manifest.get('build_id', 'unknown')} "
            f"source={manifest.get('source_revision', 'unknown')}"
        )


def main() -> int:
    args = parse_args()
    try:
        artifact = (
            args.artifact.resolve()
            if args.artifact is not None
            else latest_artifact(args.artifact_root.resolve())
        )
        smoke(artifact)
    except (OSError, RuntimeError, subprocess.CalledProcessError, zipfile.BadZipFile) as exc:
        print(f"release smoke failed: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
