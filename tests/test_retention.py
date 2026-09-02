from datetime import UTC, datetime

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
from performance_lab.storage import (
    RetentionPolicy,
    RetentionRunSink,
    SampleEvidenceRetention,
    SQLiteRunStore,
    prepare_run_for_publication,
)


def evaluator() -> EvaluatorRef:
    return EvaluatorRef(evaluator_id="exact-match", version="1")


def measurement(name: str, scope: MeasurementScope) -> Measurement:
    return Measurement(
        name=name,
        value=12.0,
        unit="ms",
        scope=scope,
        provenance=MeasurementProvenance.CLIENT,
        protocol_version="test-v1",
    )


def completed_run() -> Run:
    now = datetime.now(UTC)
    dataset = DatasetSnapshot(
        dataset_id="demo",
        dataset_version="1",
        source="fixture",
        split="test",
        content_sha256="a" * 64,
        selection_policy="all",
        sample_count=2,
    )
    generation = GenerationConfig(max_output_tokens=8, temperature=0.0)
    suite = EvaluationSuite(
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
        generation=generation,
    )
    fingerprint = ExecutionFingerprint(
        target_id="target",
        adapter_type="openai-compatible",
        endpoint_identity="local",
        model=ModelIdentity(model_id="model-a"),
        generation=generation,
        prompt_template_version="chat-v1",
        dataset_snapshots=(dataset,),
        evaluator_versions=(evaluator(),),
        benchmark_protocol_version="bench-v1",
        load_profile=LoadProfile(request_count=2),
    )
    score = Score(metric="accuracy", value=1.0, evaluator=evaluator(), higher_is_better=True)
    successful = SampleExecution(
        sample_id="sample-ok",
        task_id="task",
        status=SampleStatus.SUCCEEDED,
        started_at=now,
        completed_at=now,
        measurements=(measurement("latency_ms", MeasurementScope.SAMPLE),),
        scores=(score,),
    )
    failed = SampleExecution(
        sample_id="sample-failed",
        task_id="task",
        status=SampleStatus.FAILED,
        started_at=now,
        completed_at=now,
        measurements=(measurement("latency_ms", MeasurementScope.SAMPLE),),
        error=ErrorInfo(code="server", category="inference", retryable=True),
    )
    return Run(
        run_id="run-1",
        status=RunStatus.SUCCEEDED,
        fingerprint=fingerprint,
        suite=suite,
        created_at=now,
        completed_at=now,
        aggregate_scores=(score,),
        aggregate_measurements=(measurement("latency_ms", MeasurementScope.RUN),),
        samples=(successful, failed),
    )


def test_default_policy_keeps_diagnostic_metadata_but_drops_sample_measurements() -> None:
    original = completed_run()
    retained = prepare_run_for_publication(original)

    assert len(retained.samples) == 2
    assert all(sample.measurements == () for sample in retained.samples)
    assert retained.samples[0].scores == original.samples[0].scores
    assert retained.aggregate_scores == original.aggregate_scores
    assert retained.aggregate_measurements == original.aggregate_measurements
    assert original.samples[0].measurements != ()
    assert "prompt" not in retained.model_dump(mode="json")
    assert "output_text" not in retained.model_dump(mode="json")


def test_policy_can_retain_only_failure_evidence_and_drop_aggregate_telemetry() -> None:
    retained = prepare_run_for_publication(
        completed_run(),
        RetentionPolicy(
            sample_evidence=SampleEvidenceRetention.FAILURES_ONLY,
            retain_aggregate_measurements=False,
        ),
    )

    assert tuple(sample.sample_id for sample in retained.samples) == ("sample-failed",)
    assert retained.aggregate_measurements == ()
    assert retained.aggregate_scores != ()


def test_retention_sink_sanitizes_only_at_immutable_publication(tmp_path) -> None:
    store = SQLiteRunStore(tmp_path / "runs.sqlite3")
    sink = RetentionRunSink(store)
    original = completed_run()

    sink.publish(original)
    stored = store.get_completed("run-1")

    assert stored is not None
    assert stored.samples[0].measurements == ()
    assert original.samples[0].measurements != ()
