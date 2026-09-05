from datetime import UTC, datetime, timedelta

from fastapi.testclient import TestClient

from performance_lab.application import RepeatabilityState, UIQueryService
from performance_lab.domain import (
    DatasetSnapshot,
    ErrorInfo,
    EvaluationSuite,
    EvaluatorRef,
    ExecutionFingerprint,
    GenerationConfig,
    LoadProfile,
    Measurement,
    MeasurementProvenance,
    MeasurementScope,
    ModelIdentity,
    Run,
    RunStatus,
    SampleExecution,
    SampleStatus,
    Score,
    TaskSpec,
)
from performance_lab.repeatability_api import attach_repeatability_api
from performance_lab.storage import SQLiteRunStore
from performance_lab.ui_api import create_ui_app


def _evaluator() -> EvaluatorRef:
    return EvaluatorRef(evaluator_id="exact-match", version="1")


def _snapshot() -> DatasetSnapshot:
    return DatasetSnapshot(
        dataset_id="demo",
        dataset_version="1",
        source="fixture",
        split="test",
        content_sha256="a" * 64,
        selection_policy="all",
        sample_count=1,
    )


def _suite() -> EvaluationSuite:
    return EvaluationSuite(
        suite_id="suite",
        suite_version="1",
        tasks=(
            TaskSpec(
                task_id="task",
                dataset_snapshot_id="demo",
                evaluator=_evaluator(),
                metric_names=("accuracy",),
            ),
        ),
        generation=GenerationConfig(max_output_tokens=8, temperature=0.0),
    )


def _fingerprint(*, model_id: str = "model-a") -> ExecutionFingerprint:
    suite = _suite()
    return ExecutionFingerprint(
        target_id="target",
        adapter_type="openai-compatible",
        endpoint_identity="loopback",
        model=ModelIdentity(model_id=model_id),
        generation=suite.generation,
        prompt_template_version="direct-user-v1",
        dataset_snapshots=(_snapshot(),),
        evaluator_versions=(_evaluator(),),
        benchmark_protocol_version="starter-quality-v1",
        load_profile=LoadProfile(concurrency=1, request_count=1, streaming=False),
    )


def _sample(
    run_id: str,
    *,
    status: SampleStatus,
    latency_ms: float | None = None,
) -> SampleExecution:
    now = datetime(2026, 9, 5, 10, 0, tzinfo=UTC)
    measurements = (
        (
            Measurement(
                name="total_latency_ms",
                value=latency_ms,
                unit="ms",
                scope=MeasurementScope.SAMPLE,
                provenance=MeasurementProvenance.CLIENT,
                protocol_version="single-request-v1",
            ),
        )
        if latency_ms is not None
        else ()
    )
    return SampleExecution(
        sample_id=f"sample-{run_id}",
        task_id="task",
        status=status,
        started_at=now,
        completed_at=now + timedelta(milliseconds=latency_ms or 1),
        measurements=measurements,
        error=(
            None
            if status == SampleStatus.SUCCEEDED
            else ErrorInfo(code="fixture_failure", category="inference")
        ),
    )


def _run(
    run_id: str,
    *,
    status: RunStatus = RunStatus.SUCCEEDED,
    model_id: str = "model-a",
    accuracy: float | None = 0.8,
    latency_ms: float | None = 100.0,
) -> Run:
    created = datetime(2026, 9, 5, 10, 0, tzinfo=UTC)
    sample_status = (
        SampleStatus.SUCCEEDED
        if status == RunStatus.SUCCEEDED
        else SampleStatus.CANCELLED
        if status == RunStatus.CANCELLED
        else SampleStatus.FAILED
    )
    aggregate_scores = (
        (
            Score(
                metric="accuracy",
                value=accuracy,
                evaluator=_evaluator(),
                higher_is_better=True,
            ),
        )
        if accuracy is not None and status == RunStatus.SUCCEEDED
        else ()
    )
    return Run(
        run_id=run_id,
        status=status,
        fingerprint=_fingerprint(model_id=model_id),
        suite=_suite(),
        created_at=created,
        completed_at=created + timedelta(seconds=1),
        aggregate_scores=aggregate_scores,
        samples=(
            _sample(
                run_id,
                status=sample_status,
                latency_ms=latency_ms if status == RunStatus.SUCCEEDED else None,
            ),
        ),
    )


def test_repeatability_groups_exact_fingerprint_and_keeps_failure_denominators(tmp_path) -> None:
    store = SQLiteRunStore(tmp_path / "runs.sqlite3")
    store.publish(_run("run-a", accuracy=0.8, latency_ms=100.0))
    store.publish(_run("run-b", accuracy=0.7, latency_ms=120.0))
    store.publish(_run("run-failed", status=RunStatus.FAILED, accuracy=None, latency_ms=None))
    store.publish(_run("different-model", model_id="model-b", accuracy=1.0, latency_ms=1.0))

    result = UIQueryService(store).repeatability("run-a")

    assert result.state == RepeatabilityState.AVAILABLE
    assert result.run_ids == ("run-a", "run-b", "run-failed")
    assert result.run_count == 3
    assert result.succeeded_run_count == 2
    assert result.failed_run_count == 1
    assert result.cancelled_run_count == 0
    assert result.sample_attempt_count == 3
    assert result.succeeded_sample_count == 2
    assert result.failed_sample_count == 1

    quality = next(item for item in result.metrics if item.metric_id.startswith("accuracy|"))
    assert quality.distribution.sample_count == 2
    assert quality.distribution.mean == 0.75

    latency = next(item for item in result.metrics if item.label == "total_latency_ms")
    assert latency.distribution.sample_count == 2
    assert latency.distribution.mean == 110.0
    assert latency.distribution.stddev == 10.0
    assert latency.run_values[0].source_sample_count == 1
    assert latency.distribution.p90.qualified is False
    assert latency.distribution.p95.qualified is False


def test_repeatability_marks_one_exact_run_as_insufficient(tmp_path) -> None:
    store = SQLiteRunStore(tmp_path / "runs.sqlite3")
    store.publish(_run("only-run"))

    result = UIQueryService(store).repeatability("only-run")

    assert result.state == RepeatabilityState.INSUFFICIENT_REPEATS
    assert result.run_count == 1
    assert "Repeat this exact frozen test" in result.note


def test_repeatability_keeps_repeated_failures_without_fabricating_metric_values(tmp_path) -> None:
    store = SQLiteRunStore(tmp_path / "runs.sqlite3")
    store.publish(_run("run-ok", accuracy=0.8, latency_ms=100.0))
    store.publish(_run("run-failed", status=RunStatus.FAILED, accuracy=None, latency_ms=None))

    result = UIQueryService(store).repeatability("run-ok")

    assert result.state == RepeatabilityState.UNAVAILABLE
    assert result.run_count == 2
    assert result.succeeded_run_count == 1
    assert result.failed_run_count == 1
    assert all(metric.distribution.sample_count == 1 for metric in result.metrics)


def test_repeatability_api_returns_versioned_projection_and_404(tmp_path) -> None:
    store = SQLiteRunStore(tmp_path / "runs.sqlite3")
    store.publish(_run("run-a"))
    queries = UIQueryService(store)
    app = create_ui_app(queries)
    attach_repeatability_api(app, queries)
    client = TestClient(app)

    response = client.get("/api/v1/runs/run-a/repeatability")
    assert response.status_code == 200
    payload = response.json()
    assert payload["api_version"] == "v1"
    assert payload["read_model_version"] == 1
    assert payload["anchor_run_id"] == "run-a"
    assert payload["state"] == "insufficient_repeats"

    missing = client.get("/api/v1/runs/missing/repeatability")
    assert missing.status_code == 404
