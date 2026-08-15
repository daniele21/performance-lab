from datetime import UTC, datetime

import pytest
from pydantic import ValidationError

from performance_lab.domain import (
    ComparisonDimension,
    DatasetSnapshot,
    EvaluationSuite,
    EvaluatorRef,
    ExecutionFingerprint,
    GenerationConfig,
    HardwareIdentity,
    LoadProfile,
    ModelIdentity,
    Run,
    RunStatus,
    Score,
    TaskSpec,
)
from performance_lab.regression import (
    BaselineBinding,
    BaselineIdentityError,
    BaselineRegressionEngine,
    RegressionDimensionState,
    ThresholdState,
    bind_baseline,
)
from performance_lab.storage import SQLiteRunStore


def dataset(version: str = "1", digest: str = "a") -> DatasetSnapshot:
    return DatasetSnapshot(
        dataset_id="demo",
        dataset_version=version,
        source="fixture",
        split="test",
        content_sha256=digest * 64,
        selection_policy="all",
        sample_count=1,
    )


def evaluator() -> EvaluatorRef:
    return EvaluatorRef(evaluator_id="exact-match", version="1")


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
        generation=GenerationConfig(max_output_tokens=8, temperature=0.0),
    )


def run(
    run_id: str,
    *,
    model_id: str,
    accuracy: float,
    snapshot: DatasetSnapshot | None = None,
) -> Run:
    active_dataset = snapshot or dataset()
    fingerprint = ExecutionFingerprint(
        target_id="target",
        adapter_type="openai-compatible",
        endpoint_identity="local",
        model=ModelIdentity(model_id=model_id),
        hardware=HardwareIdentity(device_id="device-a", os="linux"),
        generation=suite().generation,
        prompt_template_version="chat-v1",
        dataset_snapshots=(active_dataset,),
        evaluator_versions=(evaluator(),),
        benchmark_protocol_version="bench-v1",
        load_profile=LoadProfile(concurrency=1, request_count=1),
    )
    now = datetime.now(UTC)
    return Run(
        run_id=run_id,
        status=RunStatus.SUCCEEDED,
        fingerprint=fingerprint,
        suite=suite(),
        created_at=now,
        completed_at=now,
        aggregate_scores=(
            Score(
                metric="accuracy",
                value=accuracy,
                evaluator=evaluator(),
                higher_is_better=True,
            ),
        ),
    )


def test_baseline_binding_is_explicit_and_frozen(tmp_path) -> None:
    store = SQLiteRunStore(tmp_path / "runs.sqlite3")
    baseline_run = run("baseline", model_id="model-a", accuracy=0.8)
    store.publish(baseline_run)

    binding = bind_baseline(store, baseline_id="release-baseline", run_id="baseline")

    assert binding.run_id == "baseline"
    assert binding.fingerprint_id == baseline_run.fingerprint.fingerprint_id
    with pytest.raises(ValidationError):
        setattr(binding, "run_id", "another-run")


def test_compatible_regression_exposes_delta_without_inventing_threshold_result(tmp_path) -> None:
    store = SQLiteRunStore(tmp_path / "runs.sqlite3")
    store.publish(run("baseline", model_id="model-a", accuracy=0.8))
    store.publish(run("candidate", model_id="model-b", accuracy=0.9))
    binding = bind_baseline(store, baseline_id="release-baseline", run_id="baseline")

    result = BaselineRegressionEngine(store).compare(binding, "candidate")
    capability = result.dimension(ComparisonDimension.CAPABILITY)

    assert capability.state == RegressionDimensionState.COMPARABLE
    assert capability.metrics[0].delta.absolute_delta == pytest.approx(0.1)
    assert capability.metrics[0].threshold_state == ThresholdState.NOT_EVALUATED
    assert result.baseline == binding


def test_incompatible_dimension_returns_not_comparable_before_thresholds(tmp_path) -> None:
    store = SQLiteRunStore(tmp_path / "runs.sqlite3")
    store.publish(run("baseline", model_id="model-a", accuracy=0.8))
    store.publish(
        run(
            "candidate",
            model_id="model-b",
            accuracy=0.9,
            snapshot=dataset(version="2", digest="b"),
        )
    )
    binding = bind_baseline(store, baseline_id="release-baseline", run_id="baseline")

    capability = (
        BaselineRegressionEngine(store)
        .compare(binding, "candidate")
        .dimension(ComparisonDimension.CAPABILITY)
    )

    assert capability.state == RegressionDimensionState.NOT_COMPARABLE
    assert capability.metrics == ()
    assert capability.compatibility.reasons[0].field == "dataset_snapshots"


def test_engine_rejects_a_binding_that_does_not_match_baseline_identity(tmp_path) -> None:
    store = SQLiteRunStore(tmp_path / "runs.sqlite3")
    store.publish(run("baseline", model_id="model-a", accuracy=0.8))
    store.publish(run("candidate", model_id="model-b", accuracy=0.9))
    binding = BaselineBinding(
        baseline_id="release-baseline",
        run_id="baseline",
        fingerprint_id="wrong-fingerprint",
        selected_at=datetime.now(UTC),
    )

    with pytest.raises(BaselineIdentityError):
        BaselineRegressionEngine(store).compare(binding, "candidate")
