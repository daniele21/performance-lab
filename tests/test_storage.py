from datetime import UTC, datetime

import pytest

from performance_lab.domain import (
    DatasetSnapshot,
    EvaluationSuite,
    EvaluatorRef,
    ExecutionFingerprint,
    GenerationConfig,
    LoadProfile,
    ModelIdentity,
    Run,
    RunStatus,
    TaskSpec,
)
from performance_lab.storage import (
    ImmutableRunConflictError,
    InvalidRunStateError,
    SQLiteRunStore,
)


def dataset() -> DatasetSnapshot:
    return DatasetSnapshot(
        dataset_id="demo",
        dataset_version="1",
        source="builtin",
        split="test",
        content_sha256="a" * 64,
        selection_policy="all",
        sample_count=1,
    )


def evaluator() -> EvaluatorRef:
    return EvaluatorRef(evaluator_id="exact-match", version="1")


def generation() -> GenerationConfig:
    return GenerationConfig(max_output_tokens=16, temperature=0.0)


def suite() -> EvaluationSuite:
    return EvaluationSuite(
        suite_id="suite",
        suite_version="1",
        tasks=(
            TaskSpec(
                task_id="task",
                dataset_snapshot_id="demo",
                evaluator=evaluator(),
                metric_names=("accuracy",),
            ),
        ),
        generation=generation(),
    )


def fingerprint(model_id: str = "model-a") -> ExecutionFingerprint:
    return ExecutionFingerprint(
        target_id="target",
        adapter_type="openai-compatible",
        endpoint_identity="local",
        model=ModelIdentity(model_id=model_id),
        generation=generation(),
        prompt_template_version="chat-v1",
        dataset_snapshots=(dataset(),),
        evaluator_versions=(evaluator(),),
        benchmark_protocol_version="bench-v1",
        load_profile=LoadProfile(),
    )


def run(status: RunStatus, *, model_id: str = "model-a") -> Run:
    now = datetime.now(UTC)
    return Run(
        run_id="run-1",
        status=status,
        fingerprint=fingerprint(model_id),
        suite=suite(),
        created_at=now,
        completed_at=now if status in {RunStatus.SUCCEEDED, RunStatus.FAILED} else None,
    )


def test_working_state_is_replaced_by_atomic_publication(tmp_path) -> None:
    store = SQLiteRunStore(tmp_path / "runs.sqlite3")
    working = run(RunStatus.RUNNING)
    store.save_working(working)
    assert store.get("run-1") == working

    completed = run(RunStatus.SUCCEEDED)
    store.publish(completed)
    assert store.get_completed("run-1") == completed
    assert store.get("run-1") == completed
    assert not store.delete_working("run-1")


def test_published_run_is_immutable(tmp_path) -> None:
    store = SQLiteRunStore(tmp_path / "runs.sqlite3")
    store.publish(run(RunStatus.SUCCEEDED, model_id="model-a"))
    with pytest.raises(ImmutableRunConflictError):
        store.publish(run(RunStatus.SUCCEEDED, model_id="model-b"))


def test_nonterminal_run_cannot_be_published(tmp_path) -> None:
    store = SQLiteRunStore(tmp_path / "runs.sqlite3")
    with pytest.raises(InvalidRunStateError):
        store.publish(run(RunStatus.RUNNING))


def test_completed_run_bundle_round_trips_between_stores(tmp_path) -> None:
    first = SQLiteRunStore(tmp_path / "first.sqlite3")
    completed = run(RunStatus.SUCCEEDED)
    first.publish(completed)
    bundle = first.export_bundle("run-1", tmp_path / "run-1.plab.zip")

    second = SQLiteRunStore(tmp_path / "second.sqlite3")
    imported = second.import_bundle(bundle)
    assert imported == completed
    assert second.get_completed("run-1") == completed
