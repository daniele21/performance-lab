from datetime import UTC, datetime, timedelta

from performance_lab.application import MetricDimension, UIQueryService
from performance_lab.domain import (
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
from performance_lab.storage import SQLiteRunStore


def _suite() -> EvaluationSuite:
    evaluator = EvaluatorRef(evaluator_id="exact-match", version="1")
    return EvaluationSuite(
        suite_id="starter",
        suite_version="1",
        tasks=(
            TaskSpec(
                task_id="qa",
                dataset_snapshot_id="demo",
                evaluator=evaluator,
                metric_names=("accuracy",),
            ),
        ),
        generation=GenerationConfig(max_output_tokens=32, temperature=0.0),
    )


def _run(
    run_id: str,
    *,
    completed_at: datetime,
    model_id: str = "model-a",
    hardware_id: str = "device-a",
    accuracy: float = 0.8,
) -> Run:
    evaluator = EvaluatorRef(evaluator_id="exact-match", version="1")
    dataset = DatasetSnapshot(
        dataset_id="demo",
        dataset_version="1",
        source="builtin",
        split="test",
        content_sha256="a" * 64,
        selection_policy="all",
        sample_count=1,
    )
    fingerprint = ExecutionFingerprint(
        target_id="local",
        adapter_type="openai-compatible",
        endpoint_identity="loopback",
        model=ModelIdentity(model_id=model_id, quantization="q4"),
        hardware=HardwareIdentity(device_id=hardware_id, device_class="cpu"),
        generation=GenerationConfig(max_output_tokens=32, temperature=0.0),
        prompt_template_version="chat-v1",
        dataset_snapshots=(dataset,),
        evaluator_versions=(evaluator,),
        benchmark_protocol_version="bench-v1",
        load_profile=LoadProfile(),
    )
    return Run(
        run_id=run_id,
        status=RunStatus.SUCCEEDED,
        fingerprint=fingerprint,
        suite=_suite(),
        created_at=completed_at - timedelta(seconds=2),
        completed_at=completed_at,
        aggregate_scores=(
            Score(
                metric="accuracy",
                value=accuracy,
                evaluator=evaluator,
                higher_is_better=True,
            ),
        ),
        aggregate_measurements=(
            Measurement(
                name="latency",
                value=125.0,
                unit="ms",
                scope=MeasurementScope.RUN,
                provenance=MeasurementProvenance.CLIENT,
                protocol_version="latency-v1",
            ),
            Measurement(
                name="peak_memory",
                value=1024.0,
                unit="MiB",
                scope=MeasurementScope.RUN,
                provenance=MeasurementProvenance.HOST,
                protocol_version="host-v1",
            ),
        ),
    )


def test_run_projection_keeps_metric_dimensions_separate(tmp_path) -> None:
    store = SQLiteRunStore(tmp_path / "runs.sqlite3")
    now = datetime.now(UTC)
    store.publish(_run("run-old", completed_at=now - timedelta(minutes=1)))
    store.publish(_run("run-new", completed_at=now, accuracy=0.9))

    queries = UIQueryService(store)
    runs = queries.list_runs()

    assert [run.run_id for run in runs] == ["run-new", "run-old"]
    assert {metric.dimension for metric in runs[0].metrics} == {
        MetricDimension.QUALITY,
        MetricDimension.PERFORMANCE,
        MetricDimension.RESOURCES,
    }


def test_tested_models_group_identical_model_runtime_hardware_cohort(tmp_path) -> None:
    store = SQLiteRunStore(tmp_path / "runs.sqlite3")
    now = datetime.now(UTC)
    store.publish(_run("run-1", completed_at=now - timedelta(minutes=1)))
    store.publish(_run("run-2", completed_at=now, accuracy=0.9))

    models = UIQueryService(store).list_tested_models()

    assert len(models) == 1
    assert models[0].identity.model_id == "model-a"
    assert models[0].run_count == 2
    assert models[0].latest_run_id == "run-2"


def test_comparison_preserves_not_comparable_and_suppresses_invalid_deltas(tmp_path) -> None:
    store = SQLiteRunStore(tmp_path / "runs.sqlite3")
    now = datetime.now(UTC)
    store.publish(_run("baseline", completed_at=now, hardware_id="device-a"))
    store.publish(
        _run(
            "candidate",
            completed_at=now + timedelta(seconds=1),
            hardware_id="device-b",
        )
    )

    comparison = UIQueryService(store).compare("baseline", "candidate")
    runtime = next(item for item in comparison.dimensions if item.dimension.value == "runtime")

    assert not runtime.comparable
    assert runtime.deltas == ()
    assert runtime.reasons
    assert runtime.reasons[0].code == "hardware_identity_mismatch"
