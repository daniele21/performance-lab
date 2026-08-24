#!/usr/bin/env python3
"""Build, smoke, atomically publish and retain bounded local product artifacts."""

from __future__ import annotations

import argparse
import os
import platform
import shutil
import subprocess
import sys
import tomllib
import uuid
import zipfile
from datetime import UTC, datetime
from pathlib import Path

from performance_lab.release_artifacts import (
    MANIFEST_SCHEMA_VERSION,
    build_delta_markdown,
    payload_manifest,
    previous_successful_manifest,
    prune_successful_artifacts,
    safe_slug,
    sha256_file,
    write_json,
)

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_BUILD_ROOT = ROOT / "build" / "release"
DEFAULT_ARTIFACT_ROOT = ROOT / "build" / "artifacts"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--validated",
        action="store_true",
        help="Skip local validation because the caller already gates this job on green CI checks.",
    )
    parser.add_argument("--build-id", default=None)
    parser.add_argument("--artifact-root", type=Path, default=DEFAULT_ARTIFACT_ROOT)
    return parser.parse_args()


def run(command: list[str], *, capture: bool = False) -> str:
    result = subprocess.run(
        command,
        cwd=ROOT,
        check=True,
        text=True,
        capture_output=capture,
    )
    return result.stdout.strip() if capture else ""


def git(command: list[str]) -> str:
    return run(["git", *command], capture=True)


def source_identity() -> tuple[str, bool]:
    revision = git(["rev-parse", "HEAD"])
    dirty = bool(git(["status", "--porcelain", "--untracked-files=normal"]))
    return revision, dirty


def project_version() -> str:
    payload = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))
    return str(payload["project"]["version"])


def build_id(explicit: str | None) -> str:
    if explicit:
        return safe_slug(explicit)
    configured = os.environ.get("PERFORMANCE_LAB_BUILD_ID")
    if configured:
        return safe_slug(configured)
    github_run = os.environ.get("GITHUB_RUN_ID")
    if github_run:
        attempt = os.environ.get("GITHUB_RUN_ATTEMPT", "1")
        return safe_slug(f"gh-{github_run}-{attempt}")
    stamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
    return f"local-{stamp}-{uuid.uuid4().hex[:8]}"


def input_hashes() -> dict[str, str]:
    paths = {
        "pyproject.toml": ROOT / "pyproject.toml",
        "requirements/ci-constraints.txt": ROOT / "requirements" / "ci-constraints.txt",
        "frontend/package-lock.json": ROOT / "frontend" / "package-lock.json",
    }
    return {name: sha256_file(path) for name, path in paths.items()}


def toolchain() -> dict[str, str]:
    return {
        "python": platform.python_version(),
        "node": run(["node", "--version"], capture=True),
        "npm": run(["npm", "--version"], capture=True),
    }


def validate_before_packaging() -> None:
    run([sys.executable, "scripts/validate.py"])
    run(["npm", "--prefix", "frontend", "run", "check"])
    run(["npm", "--prefix", "frontend", "run", "test"])
    run([sys.executable, "-m", "pytest", "tests/e2e", "-v", "--tb=short"])


def build_payload(staging: Path) -> Path:
    run(["npm", "--prefix", "frontend", "run", "build"])
    web = staging / "web"
    shutil.copytree(ROOT / "frontend" / "dist", web)

    python_dir = staging / "python"
    python_dir.mkdir(parents=True)
    run(
        [
            sys.executable,
            "-m",
            "pip",
            "wheel",
            ".",
            "--no-deps",
            "--wheel-dir",
            str(python_dir),
        ]
    )
    wheels = tuple(python_dir.glob("*.whl"))
    if len(wheels) != 1:
        raise RuntimeError(f"expected exactly one wheel, found {len(wheels)}")
    return wheels[0]


def write_run_instructions(staging: Path, wheel_name: str) -> None:
    (staging / "RUN.md").write_text(
        "# Run this artifact\n\n"
        "1. Extract the ZIP.\n"
        f"2. Install `python/{wheel_name}[ui]` into an isolated Python 3.12+ environment.\n"
        "3. Create a versioned `StarterRunConfig` JSON for the target endpoint.\n"
        "4. Run `performance-lab-ui --config <config.json> --assets web`.\n\n"
        "The product binds to loopback by default. Model serving remains external.\n",
        encoding="utf-8",
    )


def create_zip(staging: Path, output: Path) -> None:
    with zipfile.ZipFile(output, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for path in sorted(item for item in staging.rglob("*") if item.is_file()):
            archive.write(path, path.relative_to(staging).as_posix())


def main() -> int:
    args = parse_args()
    if not args.validated:
        validate_before_packaging()

    revision, dirty = source_identity()
    current_build_id = build_id(args.build_id)
    version = project_version()
    lineage = {
        "project": "performance-lab",
        "platform": safe_slug(sys.platform),
        "architecture": safe_slug(platform.machine() or "unknown"),
        "channel": safe_slug(os.environ.get("PERFORMANCE_LAB_CHANNEL", "local")),
        "variant": safe_slug(os.environ.get("PERFORMANCE_LAB_VARIANT", "browser-ui")),
    }
    lineage_slug = "__".join(lineage.values())
    lineage_dir = args.artifact_root.resolve() / lineage_slug
    lineage_dir.mkdir(parents=True, exist_ok=True)

    artifact_stem = safe_slug(f"ai-performance-lab-{version}-{current_build_id}-{revision[:12]}")
    work_dir = DEFAULT_BUILD_ROOT / current_build_id
    if work_dir.exists():
        shutil.rmtree(work_dir)
    staging = work_dir / "staging"
    staging.mkdir(parents=True)

    previous = previous_successful_manifest(lineage_dir)
    previous_manifest = previous[1] if previous is not None else None

    wheel = build_payload(staging)
    files, payload_bytes = payload_manifest(staging)
    manifest = {
        "schema_version": MANIFEST_SCHEMA_VERSION,
        "publication_status": "successful",
        "product": "ai-performance-lab",
        "product_version": version,
        "build_id": current_build_id,
        "artifact_stem": artifact_stem,
        "source_revision": revision,
        "source_dirty": dirty,
        "created_at": datetime.now(UTC).isoformat(),
        "lineage": lineage,
        "inputs": input_hashes(),
        "toolchain": toolchain(),
        "validation_status": "ci-green" if args.validated else "local-gates-passed",
        "payload_file_count": len(files),
        "payload_bytes": payload_bytes,
        "payload_files": files,
        "checksum_algorithm": "sha256",
        "smoke_required_before_publication": True,
    }
    delta = build_delta_markdown(manifest, previous_manifest)
    (staging / "BUILD_CHANGELOG.md").write_text(delta, encoding="utf-8")
    write_run_instructions(staging, wheel.name)
    write_json(staging / "build-manifest.json", manifest)

    unpublished_zip = work_dir / f"{artifact_stem}.zip"
    create_zip(staging, unpublished_zip)

    run([sys.executable, "scripts/smoke_release.py", str(unpublished_zip)])

    checksum = sha256_file(unpublished_zip)
    final_zip = lineage_dir / unpublished_zip.name
    if final_zip.exists():
        raise RuntimeError(f"refusing to overwrite immutable artifact: {final_zip}")
    unpublished_zip.replace(final_zip)

    manifest_sidecar = lineage_dir / f"{artifact_stem}.build-manifest.json"
    delta_sidecar = lineage_dir / f"{artifact_stem}.BUILD_CHANGELOG.md"
    checksum_sidecar = lineage_dir / f"{artifact_stem}.sha256"
    write_json(manifest_sidecar, manifest)
    delta_sidecar.write_text(delta, encoding="utf-8")
    checksum_sidecar.write_text(f"{checksum}  {final_zip.name}\n", encoding="utf-8")

    removed = prune_successful_artifacts(lineage_dir, keep=2)
    shutil.rmtree(work_dir, ignore_errors=True)

    print(f"published: {final_zip}")
    print(f"sha256: {checksum}")
    print(f"lineage: {lineage_slug}")
    print(f"pruned files: {len(removed)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
