from datetime import UTC, datetime, timedelta

import pytest
from fastapi.testclient import TestClient

from performance_lab.application import (
    EvidenceContentState,
    ExplanationState,
    SampleQualityVerdict,
    UIQueryService,
)
from performance_lab.datasets import DatasetRecord, MaterializedDataset
from performance_lab.domain import (
    DatasetSnapshot,
    ErrorInfo,
    EvaluationSuite,
    ExecutionFingerprint,
    GenerationConfig,
    LoadProfile,
    Measurement,
    MeasurementProvenance,
    MeasurementScope,
    ModelIdentity,
    Run,
    RunStatus,
    SampleContentEvidence,
    SampleExecution,
    SampleStatus,
    Score,
    TaskSpec,
)
from performance_lab.evaluation import ExactMatchEvaluator
from performance_lab.storage import SQLiteRunStore
from performance_lab.ui_api import create_ui_app


def _evidence_fixture(
    tmp_path,
    *,
    inspectable: bool = True,
    evidence_rich: bool = False,
) -> UIQueryService:
    evaluator = ExactMatchEvaluator()
    snapshot = DatasetSnapshot(
        dataset_id="demo",
        dataset_version="1",
        source="builtin:test",
        split="test",
        content_sha256="a" * 64,
        selection_policy="all",
        sample_count=1,
    )
    dataset = MaterializedDataset(
        snapshot=snapshot,
        records=(DatasetRecord(sample_id="sample-1", input="Question", expected="Answer"),),
    )
    generation = GenerationConfig(max_output_tokens=16, temperature=0.0)
    suite = EvaluationSuite(
        suite_id="demo-suite",
        suite_version="1",
        tasks=(
            TaskSpec(
                task_id="qa",
                dataset_snapshot_id="demo",
                evaluator=evaluator.evaluator_ref,
                metric_names=("exact_match",),
            ),
        ),
        generation=generation,
    )
    started = datetime(2026, 8, 30, 12, 0, tzinfo=UTC)
    failed = SampleExecution(
        sample_id="sample-1",
        task_id="qa",
        attempt=1,
        status=SampleStatus.FAILED,
        started_at=started,
        completed_at=started + timedelta(milliseconds=25),
        error=ErrorInfo(code="timeout", category="inference", retryable=True),
    )
    succeeded = SampleExecution(
        sample_id="sample-1",
        task_id="qa",
        attempt=2,
        status=SampleStatus.SUCCEEDED,
        started_at=started + timedelta(seconds=1),
        completed_at=started + timedelta(seconds=1, milliseconds=50),
        input_tokens=3,
        output_tokens=1,
        measurements=(
            Measurement(
                name="request_duration",
                value=48.0,
                unit="ms",
                scope=MeasurementScope.SAMPLE,
                provenance=MeasurementProvenance.CLIENT,
                protocol_version="client-v1",
            ),
        ),
        scores=(
            Score(
                metric="exact_match",
                value=1.0,
                evaluator=evaluator.evaluator_ref,
                higher_is_better=True,
                numerator=1.0,
                denominator=1.0,
            ),
        ),
    )
    fingerprint = ExecutionFingerprint(
        target_id="local",
        adapter_type="openai-compatible",
        endpoint_identity="loopback",
        model=ModelIdentity(model_id="model-a", quantization="Q4_K_M"),
        generation=generation,
        prompt_template_version="direct-user-v1",
        dataset_snapshots=(snapshot,),
        evaluator_versions=(evaluator.evaluator_ref,),
        benchmark_protocol_version="bench-v1",
        load_profile=LoadProfile(request_count=1),
    )
    run = Run(
        run_id="run-1",
        status=RunStatus.SUCCEEDED,
        fingerprint=fingerprint,
        suite=suite,
        created_at=started,
        completed_at=started + timedelta(seconds=2),
        samples=(failed, succeeded),
    )
    store = SQLiteRunStore(tmp_path / "runs.sqlite3")
    if evidence_rich:
        store.save_working(
            run.model_copy(
                update={"status": RunStatus.RUNNING, "completed_at": None, "samples": ()}
            )
        )
        store.save_working_sample_content(
            SampleContentEvidence(
                run_id="run-1",
                task_id="qa",
                sample_id="sample-1",
                attempt=2,
                prompt="Question",
                response="Answer",
            )
        )
    store.publish(run)
    return UIQueryService(
        store,
        suites=(suite,),
        dataset_snapshots=(snapshot,),
        inspectable_datasets=(dataset,) if inspectable else (),
        evaluators=(evaluator,),
    )


def test_sample_list_preserves_attempt_identity_and_typed_outcomes(tmp_path) -> None:
    queries = _evidence_fixture(tmp_path)

    samples = queries.list_run_samples("run-1")

    assert [(item.task_id, item.sample_id, item.attempt) for item in samples] == [
        ("qa", "sample-1", 1),
        ("qa", "sample-1", 2),
    ]
    assert samples[0].status == SampleStatus.FAILED
    assert samples[0].error is not None
    assert samples[0].error.retryable is True
    assert samples[1].status == SampleStatus.SUCCEEDED
    assert samples[1].elapsed_ms == pytest.approx(50.0)
    assert samples[1].score_count == 1
    assert samples[1].measurement_count == 1


def test_sample_detail_keeps_definition_content_separate_from_execution_content(tmp_path) -> None:
    queries = _evidence_fixture(tmp_path)

    detail = queries.get_sample_evidence("run-1", "qa", "sample-1", 2)

    assert detail.run.identity.model_id == "model-a"
    assert detail.run.identity.quantization == "Q4_K_M"
    assert detail.fingerprint.prompt_template_version == "direct-user-v1"
    assert detail.benchmark_case is not None
    assert detail.benchmark_case.input == "Question"
    assert detail.benchmark_case.expected == "Answer"
    assert detail.prompt.state == EvidenceContentState.NOT_RETAINED
    assert detail.prompt.content is None
    assert detail.prompt.reason == "content_not_retained"
    assert detail.response.state == EvidenceContentState.NOT_RETAINED
    assert detail.response.content is None
    assert detail.quality.verdict == SampleQualityVerdict.CORRECT
    assert detail.quality.metric == "exact_match"
    assert detail.quality.value == 1.0
    assert detail.quality.percentage == 100.0
    assert detail.definition_issues == ()

    score = detail.scores[0]
    assert score.metric == "exact_match"
    assert score.value == 1.0
    assert score.evaluator_rule_summary == (
        "Scores 1 when actual and expected values are exactly equal, else 0."
    )
    assert score.explanation_state == ExplanationState.UNAVAILABLE
    assert score.explanation is None

    measurement = detail.measurements[0]
    assert measurement.name == "request_duration"
    assert measurement.provenance == MeasurementProvenance.CLIENT
    assert measurement.protocol_version == "client-v1"


def test_sample_detail_reads_evidence_rich_prompt_and_output_from_local_sidecar(tmp_path) -> None:
    detail = _evidence_fixture(tmp_path, evidence_rich=True).get_sample_evidence(
        "run-1", "qa", "sample-1", 2
    )

    assert detail.prompt.state == EvidenceContentState.RETAINED
    assert detail.prompt.content == "Question"
    assert detail.response.state == EvidenceContentState.RETAINED
    assert detail.response.content == "Answer"
    assert detail.benchmark_case is not None
    assert detail.benchmark_case.expected == "Answer"
    assert detail.quality.verdict == SampleQualityVerdict.CORRECT


def test_sample_detail_does_not_invent_benchmark_content_when_not_inspectable(tmp_path) -> None:
    queries = _evidence_fixture(tmp_path, inspectable=False)

    detail = queries.get_sample_evidence("run-1", "qa", "sample-1", 2)

    assert detail.benchmark_case is None
    assert detail.definition_issues == (
        "Benchmark case content is unavailable under the current dataset inspection policy.",
    )
    assert detail.prompt.state == EvidenceContentState.NOT_RETAINED
    assert detail.response.state == EvidenceContentState.NOT_RETAINED


def test_sample_lookup_requires_exact_attempt_identity(tmp_path) -> None:
    queries = _evidence_fixture(tmp_path)

    with pytest.raises(LookupError, match="sample evidence not found"):
        queries.get_sample_evidence("run-1", "qa", "sample-1", 3)

    with pytest.raises(LookupError, match="completed run not found"):
        queries.list_run_samples("missing")


def test_sample_evidence_api_exposes_attempt_specific_read_models(tmp_path) -> None:
    client = TestClient(create_ui_app(_evidence_fixture(tmp_path)))

    listing = client.get("/api/v1/runs/run-1/samples")
    assert listing.status_code == 200
    assert [(item["sample_id"], item["attempt"]) for item in listing.json()] == [
        ("sample-1", 1),
        ("sample-1", 2),
    ]

    detail = client.get("/api/v1/runs/run-1/samples/qa/sample-1/2")
    assert detail.status_code == 200
    payload = detail.json()
    assert payload["sample"]["attempt"] == 2
    assert payload["benchmark_case"]["expected"] == "Answer"
    assert payload["quality"] == {
        "api_version": "v1",
        "read_model_version": 1,
        "verdict": "correct",
        "metric": "exact_match",
        "value": 1.0,
        "percentage": 100.0,
    }
    assert payload["prompt"] == {
        "api_version": "v1",
        "read_model_version": 1,
        "state": "not_retained",
        "content": None,
        "reason": "content_not_retained",
    }
    assert payload["response"]["state"] == "not_retained"
    assert payload["scores"][0]["explanation_state"] == "unavailable"


def test_sample_evidence_api_keeps_missing_and_invalid_attempts_explicit(tmp_path) -> None:
    client = TestClient(create_ui_app(_evidence_fixture(tmp_path)))

    missing = client.get("/api/v1/runs/run-1/samples/qa/sample-1/3")
    assert missing.status_code == 404
    assert missing.json() == {"detail": "sample evidence not found"}

    invalid = client.get("/api/v1/runs/run-1/samples/qa/sample-1/0")
    assert invalid.status_code == 422

    missing_run = client.get("/api/v1/runs/missing/samples")
    assert missing_run.status_code == 404
    assert missing_run.json() == {"detail": "completed run not found"}
