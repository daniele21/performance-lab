"""Release artifact identity, manifest, delta and bounded-retention helpers."""

from __future__ import annotations

import hashlib
import json
import re
from collections.abc import Iterable, Mapping
from pathlib import Path
from typing import Any

MANIFEST_SCHEMA_VERSION = 1


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def safe_slug(value: str) -> str:
    normalized = re.sub(r"[^A-Za-z0-9._-]+", "-", value.strip()).strip("-._")
    return normalized or "unknown"


def payload_manifest(root: Path) -> tuple[list[dict[str, Any]], int]:
    files: list[dict[str, Any]] = []
    total_bytes = 0
    for path in sorted(item for item in root.rglob("*") if item.is_file()):
        size = path.stat().st_size
        total_bytes += size
        files.append(
            {
                "path": path.relative_to(root).as_posix(),
                "size_bytes": size,
                "sha256": sha256_file(path),
            }
        )
    return files, total_bytes


def read_manifest(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"manifest must be a JSON object: {path}")
    if value.get("schema_version") != MANIFEST_SCHEMA_VERSION:
        raise ValueError(f"unsupported manifest schema in {path}")
    return value


def previous_successful_manifest(lineage_dir: Path) -> tuple[Path, dict[str, Any]] | None:
    candidates = sorted(
        lineage_dir.glob("*.build-manifest.json"),
        key=lambda path: path.stat().st_mtime_ns,
        reverse=True,
    )
    for path in candidates:
        try:
            manifest = read_manifest(path)
        except (OSError, ValueError, json.JSONDecodeError):
            continue
        if manifest.get("publication_status") == "successful":
            return path, manifest
    return None


def _mapping(value: Any) -> Mapping[str, Any]:
    return value if isinstance(value, Mapping) else {}


def build_delta_markdown(
    current: Mapping[str, Any],
    previous: Mapping[str, Any] | None,
) -> str:
    lines = ["# Build delta", ""]
    if previous is None:
        lines.extend(
            [
                "No previous successful comparable build exists for this lineage.",
                "",
                "This artifact establishes the comparison baseline.",
            ]
        )
        return "\n".join(lines) + "\n"

    lines.extend(
        [
            f"Previous build: `{previous.get('build_id', 'unknown')}`",
            f"Current build: `{current.get('build_id', 'unknown')}`",
            "",
            "## Source",
            "",
            f"- revision: `{previous.get('source_revision', 'unknown')}` -> "
            f"`{current.get('source_revision', 'unknown')}`",
            f"- dirty: `{previous.get('source_dirty', 'unknown')}` -> "
            f"`{current.get('source_dirty', 'unknown')}`",
            "",
            "## Dependencies",
            "",
        ]
    )

    current_inputs = _mapping(current.get("inputs"))
    previous_inputs = _mapping(previous.get("inputs"))
    input_names = sorted(set(current_inputs) | set(previous_inputs))
    for name in input_names:
        before = previous_inputs.get(name, "missing")
        after = current_inputs.get(name, "missing")
        marker = "changed" if before != after else "unchanged"
        lines.append(f"- {name}: {marker} (`{before}` -> `{after}`)")

    lines.extend(["", "## Toolchain", ""])
    current_toolchain = _mapping(current.get("toolchain"))
    previous_toolchain = _mapping(previous.get("toolchain"))
    tool_names = sorted(set(current_toolchain) | set(previous_toolchain))
    for name in tool_names:
        before = previous_toolchain.get(name, "missing")
        after = current_toolchain.get(name, "missing")
        marker = "changed" if before != after else "unchanged"
        lines.append(f"- {name}: {marker} (`{before}` -> `{after}`)")

    lines.extend(["", "## Configuration / lineage", ""])
    current_lineage = _mapping(current.get("lineage"))
    previous_lineage = _mapping(previous.get("lineage"))
    for name in sorted(set(current_lineage) | set(previous_lineage)):
        before = previous_lineage.get(name, "missing")
        after = current_lineage.get(name, "missing")
        marker = "changed" if before != after else "unchanged"
        lines.append(f"- {name}: {marker} (`{before}` -> `{after}`)")

    lines.extend(
        [
            "",
            "## Compatibility migrations",
            "",
            "- No automatic compatibility migration claim is inferred by the build pipeline.",
            "",
            "## Artifact metrics",
            "",
            f"- file count: `{previous.get('payload_file_count', 'unknown')}` -> "
            f"`{current.get('payload_file_count', 'unknown')}`",
            f"- payload bytes: `{previous.get('payload_bytes', 'unknown')}` -> "
            f"`{current.get('payload_bytes', 'unknown')}`",
            "",
            "## Validation",
            "",
            f"- previous: `{previous.get('validation_status', 'unknown')}`",
            f"- current: `{current.get('validation_status', 'unknown')}`",
        ]
    )
    return "\n".join(lines) + "\n"


def prune_successful_artifacts(lineage_dir: Path, keep: int = 2) -> list[Path]:
    if keep < 1:
        raise ValueError("keep must be at least 1")
    manifests: list[tuple[Path, dict[str, Any]]] = []
    for path in lineage_dir.glob("*.build-manifest.json"):
        try:
            manifest = read_manifest(path)
        except (OSError, ValueError, json.JSONDecodeError):
            continue
        if manifest.get("publication_status") == "successful":
            manifests.append((path, manifest))
    manifests.sort(key=lambda item: item[0].stat().st_mtime_ns, reverse=True)

    removed: list[Path] = []
    for _manifest_path, manifest in manifests[keep:]:
        stem = manifest.get("artifact_stem")
        if not isinstance(stem, str) or not stem:
            continue
        for path in lineage_dir.glob(f"{stem}*"):
            if path.is_file():
                path.unlink()
                removed.append(path)
    return removed


def write_json(path: Path, payload: Mapping[str, Any]) -> None:
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def combined_hash(paths: Iterable[Path]) -> str:
    digest = hashlib.sha256()
    for path in sorted(paths, key=lambda value: value.as_posix()):
        digest.update(path.as_posix().encode("utf-8"))
        digest.update(b"\0")
        digest.update(sha256_file(path).encode("ascii"))
        digest.update(b"\0")
    return digest.hexdigest()
