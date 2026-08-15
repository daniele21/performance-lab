from datetime import UTC, datetime

from performance_lab.domain import (
    ComparisonDimension,
    DatasetSnapshot,
    EvaluationSuite,
    EvaluatorRef,
    ExecutionFingerprint,
    GenerationConfig,
    HardwareIdentity,
    LoadProfile,
    Measurement,
    MeasurementProvenance,
    MeasurementScope,
    ModelIdentity,
    Run,
    RunStatus,
    Score,
    TaskSpec,
)
from performance_lab.storage import RunComparisonService, SQLiteRunStore, compare_runs


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
    ttft_ms: float,
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
        aggregate_measurements=(
            Measurement(
                name="ttft_ms",
                value=ttft_ms,
                unit="ms",
                scope=MeasurementScope.RUN,
                provenance=MeasurementProvenance.CLIENT,
                protocol_version="single-request-v1",
            ),
        ),
    )


def test_model_change_is_visible_before_compatible_deltas() -> None:
    baseline = run("baseline", model_id="model-a", accuracy=0.8, ttft_ms=100)
    candidate = run("candidate", model_id="model-b", accuracy=0.9, ttft_ms=80)
    comparison = compare_runs(baseline, candidate)

    paths = {difference.path for difference in comparison.identity_differences}
    assert "fingerprint.model.model_id" in paths

    capability = comparison.dimension(ComparisonDimension.CAPABILITY)
    assert capability.compatibility.comparable
    assert capability.deltas[0].absolute_delta == 0.1
    assert capability.deltas[0].relative_delta_pct == 12.5
    assert capability.deltas[0].higher_is_better is True

    runtime = comparison.dimension(ComparisonDimension.RUNTIME)
    assert runtime.compatibility.comparable
    assert runtime.deltas[0].absolute_delta == -20.0
    assert runtime.deltas[0].unit == "ms"


def test_incompatible_dataset_blocks_capability_deltas() -> None:
    baseline = run("baseline", model_id="model-a", accuracy=0.8, ttft_ms=100)
    candidate = run(
        "candidate",
        model_id="model-b",
        accuracy=0.9,
        ttft_ms=80,
        snapshot=dataset(version="2", digest="b"),
    )
    capability = compare_runs(baseline, candidate).dimension(ComparisonDimension.CAPABILITY)
    assert not capability.compatibility.comparable
    assert capability.deltas == ()
    assert capability.compatibility.reasons[0].field == "dataset_snapshots"


def test_comparison_service_reads_completed_runs_from_store(tmp_path) -> None:
    store = SQLiteRunStore(tmp_path / "runs.sqlite3")
    store.publish(run("baseline", model_id="model-a", accuracy=0.8, ttft_ms=100))
    store.publish(run("candidate", model_id="model-b", accuracy=0.9, ttft_ms=80))
    result = RunComparisonService(store).compare("baseline", "candidate")
    assert result.baseline_run_id == "baseline"
    assert result.candidate_run_id == "candidate"
