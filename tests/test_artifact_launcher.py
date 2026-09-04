import json
from pathlib import Path

import pytest

from performance_lab import artifact_launcher


def _artifact(tmp_path: Path) -> Path:
    root = tmp_path / "artifact"
    (root / "python").mkdir(parents=True)
    (root / "runtime-requirements.txt").write_text("pydantic==2.0\n", encoding="utf-8")
    (root / "python" / "performance_lab.whl").write_bytes(b"wheel")
    (root / "build-manifest.json").write_text(
        json.dumps(
            {
                "artifact_stem": "ai-performance-lab-test",
                "source_revision": "abc123",
            }
        ),
        encoding="utf-8",
    )
    return root


def test_artifact_launcher_config_is_optional_for_first_run() -> None:
    args = artifact_launcher.build_parser().parse_args([])

    assert args.config is None
    assert args.port == 8765


def test_runtime_identity_is_bound_to_artifact_inputs(tmp_path: Path) -> None:
    root = _artifact(tmp_path)

    identity = artifact_launcher.runtime_identity(root)

    assert identity["owner"] == artifact_launcher.RUNTIME_OWNER
    assert identity["artifact_stem"] == "ai-performance-lab-test"
    assert identity["source_revision"] == "abc123"
    assert len(identity["requirements_sha256"]) == 64
    assert len(identity["wheel_sha256"]) == 64


def test_prepare_runtime_installs_once_then_reuses_matching_runtime(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    root = _artifact(tmp_path)
    runtime = tmp_path / "runtime"
    calls: list[list[str]] = []

    class FakeBuilder:
        def __init__(self, *, with_pip: bool) -> None:
            assert with_pip is True

        def create(self, path: Path) -> None:
            python = artifact_launcher._runtime_python(Path(path))
            python.parent.mkdir(parents=True, exist_ok=True)
            python.write_text("fake-python", encoding="utf-8")

    def fake_run(command: list[str], *, check: bool) -> None:
        assert check is True
        calls.append(command)

    monkeypatch.setattr(artifact_launcher.venv, "EnvBuilder", FakeBuilder)
    monkeypatch.setattr(artifact_launcher.subprocess, "run", fake_run)

    python = artifact_launcher.prepare_runtime(root, runtime)
    reused = artifact_launcher.prepare_runtime(root, runtime)

    assert python == reused
    assert python.is_file()
    assert len(calls) == 2
    marker = json.loads((runtime / artifact_launcher.RUNTIME_MARKER).read_text(encoding="utf-8"))
    assert marker["state"] == "ready"
    assert marker["owner"] == artifact_launcher.RUNTIME_OWNER
    assert artifact_launcher.runtime_is_current(root, runtime) is True


def test_prepare_runtime_refuses_to_replace_unowned_directory(tmp_path: Path) -> None:
    root = _artifact(tmp_path)
    runtime = tmp_path / "runtime"
    runtime.mkdir()
    (runtime / "user-data.txt").write_text("keep", encoding="utf-8")

    with pytest.raises(RuntimeError, match="refusing to replace unowned runtime directory"):
        artifact_launcher.prepare_runtime(root, runtime)

    assert (runtime / "user-data.txt").read_text(encoding="utf-8") == "keep"


def test_runtime_is_invalidated_when_locked_requirements_change(tmp_path: Path) -> None:
    root = _artifact(tmp_path)
    runtime = tmp_path / "runtime"
    runtime.mkdir()
    identity = artifact_launcher.runtime_identity(root)
    marker = {**identity, "state": "ready"}
    (runtime / artifact_launcher.RUNTIME_MARKER).write_text(
        json.dumps(marker),
        encoding="utf-8",
    )
    python = artifact_launcher._runtime_python(runtime)
    python.parent.mkdir(parents=True)
    python.write_text("fake-python", encoding="utf-8")
    assert artifact_launcher.runtime_is_current(root, runtime) is True

    (root / "runtime-requirements.txt").write_text("pydantic==2.1\n", encoding="utf-8")

    assert artifact_launcher.runtime_is_current(root, runtime) is False
