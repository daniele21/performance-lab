#!/usr/bin/env python3
"""Exercise the distributed artifact through its real launcher and Chromium."""

from __future__ import annotations

import argparse
import hashlib
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
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_ARTIFACT_ROOT = ROOT / "build" / "artifacts"
DEFAULT_EVIDENCE_PATH = (
    ROOT / "frontend" / "test-results-full-product" / "distributed-artifact-evidence.json"
)
HOST = "127.0.0.1"
RUNTIME_MARKER = ".performance-lab-runtime.json"
RUNTIME_OWNER = "performance-lab-artifact-launcher-v1"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("artifact", type=Path, nargs="?", default=None)
    parser.add_argument("--artifact-root", type=Path, default=DEFAULT_ARTIFACT_ROOT)
    parser.add_argument("--evidence-output", type=Path, default=DEFAULT_EVIDENCE_PATH)
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


def wait_ready(
    url: str,
    process: subprocess.Popen[str],
    label: str,
    *,
    timeout_seconds: float = 20.0,
) -> None:
    deadline = time.monotonic() + timeout_seconds
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


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def read_json_object(path: Path, label: str) -> dict[str, Any]:
    try:
        payload: object = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise RuntimeError(f"cannot read {label}: {path}") from exc
    if not isinstance(payload, dict):
        raise RuntimeError(f"{label} must contain a JSON object: {path}")
    return payload


def verify_launcher_identity(extracted: Path) -> tuple[dict[str, Any], dict[str, Any]]:
    manifest = read_json_object(extracted / "build-manifest.json", "build manifest")
    marker = read_json_object(extracted / ".runtime" / RUNTIME_MARKER, "runtime marker")
    source_revision = manifest.get("source_revision")
    artifact_stem = manifest.get("artifact_stem")
    if not isinstance(source_revision, str) or not source_revision:
        raise RuntimeError("build manifest is missing source_revision")
    if not isinstance(artifact_stem, str) or not artifact_stem:
        raise RuntimeError("build manifest is missing artifact_stem")
    expected = {
        "owner": RUNTIME_OWNER,
        "source_revision": source_revision,
        "artifact_stem": artifact_stem,
        "state": "ready",
    }
    mismatched = {key: (value, marker.get(key)) for key, value in expected.items() if marker.get(key) != value}
    if mismatched:
        raise RuntimeError(f"launcher runtime identity does not match artifact: {mismatched}")
    return manifest, marker


def write_evidence(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def run_full_product_e2e(artifact: Path, *, evidence_output: Path) -> None:
    if not artifact.is_file():
        raise RuntimeError(f"artifact does not exist: {artifact}")

    artifact_checksum = sha256_file(artifact)
    evidence: dict[str, Any] = {
        "schema_version": 1,
        "gate_id": "VALUE-08C",
        "status": "FAIL",
        "environment": "packaged-product-fixture",
        "fidelity": "representative_virtual",
        "artifact": {
            "filename": artifact.name,
            "sha256": artifact_checksum,
        },
        "launcher": {
            "entrypoint": "launch.py",
            "configless": True,
        },
        "journey": "extract -> launch -> connect -> Find best setup -> bounded evaluation",
        "cleanup": {
            "product_port_released": False,
            "fixture_port_released": False,
        },
    }

    try:
        with tempfile.TemporaryDirectory(prefix="performance-lab-full-e2e-") as directory:
            root = Path(directory)
            extracted = root / "artifact"
            extracted.mkdir()
            with zipfile.ZipFile(artifact) as archive:
                safe_extract(archive, extracted)
            if not (extracted / "web" / "index.html").is_file():
                raise RuntimeError("packaged artifact is missing web/index.html")
            if not (extracted / "launch.py").is_file():
                raise RuntimeError("packaged artifact is missing launch.py")

            fixture_port = free_port()
            ui_port = free_port()
            fixture: subprocess.Popen[str] | None = None
            product: subprocess.Popen[str] | None = None
            product_released = False
            fixture_released = False
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
                        sys.executable,
                        str(extracted / "launch.py"),
                        "--port",
                        str(ui_port),
                    ],
                    cwd=extracted,
                    text=True,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                )
                wait_ready(
                    f"http://{HOST}:{ui_port}/api/v1/health",
                    product,
                    "distributed product",
                    timeout_seconds=180.0,
                )

                manifest, marker = verify_launcher_identity(extracted)
                evidence["artifact"].update(
                    {
                        "artifact_stem": manifest["artifact_stem"],
                        "build_id": manifest.get("build_id"),
                        "source_revision": manifest["source_revision"],
                    }
                )
                evidence["launcher"].update(
                    {
                        "runtime_owner": marker["owner"],
                        "runtime_state": marker["state"],
                        "runtime_source_revision": marker["source_revision"],
                        "runtime_requirements_sha256": marker.get("requirements_sha256"),
                        "runtime_wheel_sha256": marker.get("wheel_sha256"),
                    }
                )

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
                evidence["browser_report"] = "frontend/test-results-full-product/report.json"
            finally:
                stop_process(product, "distributed product")
                stop_process(fixture, "inference fixture")
                assert_port_released(ui_port, "distributed product")
                product_released = True
                assert_port_released(fixture_port, "inference fixture")
                fixture_released = True
                evidence["cleanup"] = {
                    "product_port_released": product_released,
                    "fixture_port_released": fixture_released,
                }

            evidence["status"] = "PASS"
    except Exception as exc:
        evidence["error"] = f"{type(exc).__name__}: {exc}"
        write_evidence(evidence_output, evidence)
        raise

    write_evidence(evidence_output, evidence)


def main() -> int:
    args = parse_args()
    evidence_output = args.evidence_output.resolve()
    try:
        artifact = (
            args.artifact.resolve()
            if args.artifact is not None
            else latest_artifact(args.artifact_root.resolve())
        )
        run_full_product_e2e(artifact, evidence_output=evidence_output)
    except (OSError, RuntimeError, subprocess.CalledProcessError, zipfile.BadZipFile) as exc:
        print(f"full-product E2E failed: {exc}", file=sys.stderr)
        return 1
    print("full-product E2E passed: VALUE-08C / packaged-product-fixture / representative_virtual")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
