import os
from pathlib import Path

import pytest

from performance_lab.release_artifacts import (
    build_delta_markdown,
    payload_manifest,
    previous_successful_manifest,
    prune_successful_artifacts,
    safe_slug,
    sha256_file,
    write_json,
)


def test_payload_manifest_is_stable_and_hashes_every_file(tmp_path: Path) -> None:
    payload = tmp_path / "payload"
    payload.mkdir()
    (payload / "b.txt").write_text("beta", encoding="utf-8")
    nested = payload / "a"
    nested.mkdir()
    (nested / "a.txt").write_text("alpha", encoding="utf-8")

    files, total_bytes = payload_manifest(payload)

    assert [item["path"] for item in files] == ["a/a.txt", "b.txt"]
    assert total_bytes == len("alpha") + len("beta")
    assert files[0]["sha256"] == sha256_file(nested / "a.txt")
    assert files[1]["sha256"] == sha256_file(payload / "b.txt")


def test_previous_successful_manifest_skips_invalid_or_failed_entries(tmp_path: Path) -> None:
    lineage = tmp_path / "lineage"
    lineage.mkdir()
    failed = lineage / "old.build-manifest.json"
    successful = lineage / "new.build-manifest.json"
    invalid = lineage / "invalid.build-manifest.json"
    write_json(
        failed,
        {"schema_version": 1, "publication_status": "failed", "build_id": "failed"},
    )
    write_json(
        successful,
        {"schema_version": 1, "publication_status": "successful", "build_id": "good"},
    )
    invalid.write_text("not-json", encoding="utf-8")
    failed.touch()
    successful.touch()
    invalid.touch()

    result = previous_successful_manifest(lineage)

    assert result is not None
    path, manifest = result
    assert path == successful
    assert manifest["build_id"] == "good"


def test_build_delta_reports_source_inputs_toolchain_and_artifact_changes() -> None:
    previous = {
        "build_id": "build-1",
        "source_revision": "abc",
        "source_dirty": False,
        "inputs": {"frontend/pnpm-lock.yaml": "one"},
        "toolchain": {"node": "v24"},
        "lineage": {"platform": "linux"},
        "payload_file_count": 2,
        "payload_bytes": 10,
        "validation_status": "ci-green",
    }
    current = {
        "build_id": "build-2",
        "source_revision": "def",
        "source_dirty": False,
        "inputs": {"frontend/pnpm-lock.yaml": "two"},
        "toolchain": {"node": "v24"},
        "lineage": {"platform": "linux"},
        "payload_file_count": 3,
        "payload_bytes": 20,
        "validation_status": "ci-green",
    }

    delta = build_delta_markdown(current, previous)

    assert "Previous build: `build-1`" in delta
    assert "Current build: `build-2`" in delta
    assert "`abc` -> `def`" in delta
    assert "frontend/pnpm-lock.yaml: changed" in delta
    assert "node: unchanged" in delta
    assert "file count: `2` -> `3`" in delta


def test_first_build_delta_establishes_comparison_baseline() -> None:
    delta = build_delta_markdown({"build_id": "build-1"}, None)

    assert "No previous successful comparable build exists" in delta
    assert "establishes the comparison baseline" in delta


def test_prune_keeps_latest_successful_artifacts_per_lineage(tmp_path: Path) -> None:
    lineage = tmp_path / "lineage"
    lineage.mkdir()
    for index in range(3):
        stem = f"artifact-{index}"
        manifest_path = lineage / f"{stem}.build-manifest.json"
        write_json(
            manifest_path,
            {
                "schema_version": 1,
                "publication_status": "successful",
                "artifact_stem": stem,
                "build_id": f"build-{index}",
            },
        )
        (lineage / f"{stem}.zip").write_bytes(bytes([index]))
        timestamp = 1_700_000_000 + index
        manifest_path.touch()
        manifest_path.chmod(0o600)
        os.utime(manifest_path, (timestamp, timestamp))

    removed = prune_successful_artifacts(lineage, keep=2)

    assert not (lineage / "artifact-0.zip").exists()
    assert not (lineage / "artifact-0.build-manifest.json").exists()
    assert (lineage / "artifact-1.zip").is_file()
    assert (lineage / "artifact-2.zip").is_file()
    assert any(path.name == "artifact-0.zip" for path in removed)


def test_prune_rejects_zero_retention(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="keep must be at least 1"):
        prune_successful_artifacts(tmp_path, keep=0)


def test_safe_slug_never_returns_empty() -> None:
    assert safe_slug("hello world") == "hello-world"
    assert safe_slug("***") == "unknown"
