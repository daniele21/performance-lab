"""Standalone launcher shipped with the distributed Performance Lab artifact.

This module intentionally depends only on the Python standard library so the same
source file can be copied to ``launch.py`` beside the packaged wheel and built web
assets. The launcher owns only its local runtime directory; model serving remains
external.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import subprocess
import sys
import venv
from collections.abc import Sequence
from pathlib import Path
from typing import Any

MIN_PYTHON = (3, 12)
RUNTIME_OWNER = "performance-lab-artifact-launcher-v1"
RUNTIME_MARKER = ".performance-lab-runtime.json"


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _load_json(path: Path) -> dict[str, Any]:
    try:
        value: object = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise RuntimeError(f"cannot read launcher metadata: {path}") from exc
    if not isinstance(value, dict):
        raise RuntimeError(f"launcher metadata must contain an object: {path}")
    return value


def _runtime_python(runtime_dir: Path) -> Path:
    if sys.platform == "win32":
        return runtime_dir / "Scripts" / "python.exe"
    return runtime_dir / "bin" / "python"


def _packaged_wheel(root: Path) -> Path:
    wheels = tuple((root / "python").glob("*.whl"))
    if len(wheels) != 1:
        raise RuntimeError(f"expected exactly one packaged wheel, found {len(wheels)}")
    return wheels[0]


def runtime_identity(root: Path) -> dict[str, str]:
    manifest = _load_json(root / "build-manifest.json")
    artifact_stem = manifest.get("artifact_stem")
    source_revision = manifest.get("source_revision")
    if not isinstance(artifact_stem, str) or not artifact_stem:
        raise RuntimeError("build manifest is missing artifact_stem")
    if not isinstance(source_revision, str) or not source_revision:
        raise RuntimeError("build manifest is missing source_revision")

    requirements = root / "runtime-requirements.txt"
    if not requirements.is_file():
        raise RuntimeError("artifact is missing runtime-requirements.txt")
    wheel = _packaged_wheel(root)
    return {
        "owner": RUNTIME_OWNER,
        "artifact_stem": artifact_stem,
        "source_revision": source_revision,
        "requirements_sha256": _sha256(requirements),
        "wheel_sha256": _sha256(wheel),
    }


def _read_runtime_marker(runtime_dir: Path) -> dict[str, Any] | None:
    marker = runtime_dir / RUNTIME_MARKER
    if not marker.is_file():
        return None
    try:
        value: object = json.loads(marker.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    return value if isinstance(value, dict) else None


def runtime_is_current(root: Path, runtime_dir: Path) -> bool:
    marker = _read_runtime_marker(runtime_dir)
    if marker is None or marker.get("state") != "ready":
        return False
    expected = runtime_identity(root)
    return (
        all(marker.get(key) == value for key, value in expected.items())
        and _runtime_python(runtime_dir).is_file()
    )


def _assert_runtime_owned(runtime_dir: Path) -> None:
    if not runtime_dir.exists():
        return
    marker = _read_runtime_marker(runtime_dir)
    if marker is None or marker.get("owner") != RUNTIME_OWNER:
        raise RuntimeError(
            f"refusing to replace unowned runtime directory: {runtime_dir}. "
            "Choose another --runtime-dir or remove it manually."
        )


def _write_runtime_marker(runtime_dir: Path, identity: dict[str, str], *, state: str) -> None:
    payload: dict[str, str] = {**identity, "state": state}
    (runtime_dir / RUNTIME_MARKER).write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def prepare_runtime(root: Path, runtime_dir: Path) -> Path:
    """Create or reuse the launcher-owned isolated runtime for this artifact."""

    root = root.resolve()
    runtime_dir = runtime_dir.resolve()
    if runtime_is_current(root, runtime_dir):
        return _runtime_python(runtime_dir)

    identity = runtime_identity(root)
    _assert_runtime_owned(runtime_dir)
    if runtime_dir.exists():
        shutil.rmtree(runtime_dir)
    runtime_dir.mkdir(parents=True)
    _write_runtime_marker(runtime_dir, identity, state="installing")

    try:
        venv.EnvBuilder(with_pip=True).create(runtime_dir)
        python = _runtime_python(runtime_dir)
        if not python.is_file():
            raise RuntimeError("Python venv was created without an executable")
        subprocess.run(
            [
                str(python),
                "-m",
                "pip",
                "install",
                "--disable-pip-version-check",
                "--no-input",
                "--requirement",
                str(root / "runtime-requirements.txt"),
            ],
            check=True,
        )
        subprocess.run(
            [
                str(python),
                "-m",
                "pip",
                "install",
                "--disable-pip-version-check",
                "--no-input",
                "--no-deps",
                str(_packaged_wheel(root)),
            ],
            check=True,
        )
    except Exception:
        # The marker proves ownership, so removing this partial runtime cannot delete
        # unrelated user state.
        shutil.rmtree(runtime_dir, ignore_errors=True)
        raise

    _write_runtime_marker(runtime_dir, identity, state="ready")
    return python


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="performance-lab-artifact")
    parser.add_argument(
        "--config",
        required=True,
        type=Path,
        help="Versioned StarterRunConfig JSON for the external inference target.",
    )
    parser.add_argument(
        "--runtime-dir",
        type=Path,
        default=None,
        help="Launcher-owned runtime directory. Defaults to .runtime beside launch.py.",
    )
    parser.add_argument("--port", type=int, default=8765)
    parser.add_argument(
        "--prepare-only",
        action="store_true",
        help="Prepare/reuse the isolated runtime without starting the product.",
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    if sys.version_info < MIN_PYTHON:
        print("Performance Lab requires Python 3.12 or newer.", file=sys.stderr)
        return 2

    args = build_parser().parse_args(list(argv) if argv is not None else None)
    root = Path(__file__).resolve().parent
    config = args.config.expanduser().resolve()
    if not config.is_file():
        print(f"error: config does not exist: {config}", file=sys.stderr)
        return 2
    if not (root / "web" / "index.html").is_file():
        print("error: artifact is missing built web assets", file=sys.stderr)
        return 2

    runtime_dir = (
        args.runtime_dir.expanduser().resolve()
        if args.runtime_dir is not None
        else root / ".runtime"
    )
    try:
        python = prepare_runtime(root, runtime_dir)
    except (OSError, RuntimeError, subprocess.CalledProcessError) as exc:
        print(f"error: cannot prepare Performance Lab runtime: {exc}", file=sys.stderr)
        return 2

    if args.prepare_only:
        print(f"Performance Lab runtime ready: {runtime_dir}")
        return 0

    command = [
        str(python),
        "-m",
        "performance_lab.ui_server",
        "--config",
        str(config),
        "--assets",
        str(root / "web"),
        "--port",
        str(args.port),
    ]
    os.execv(str(python), command)
    raise AssertionError("os.execv returned unexpectedly")


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
