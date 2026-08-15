import asyncio

from performance_lab.datasets import DatasetRecord, MaterializedDataset
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
    Score,
    TaskSpec,
)
from performance_lab.engine import EvaluationOrchestrator, ProgressEvent, ProgressPhase
from performance_lab.plugins import (
    FakeInferenceAdapter,
    InferenceAdapterError,
    InferenceErrorCode,
    InferenceRequest,
    InferenceResponse,
)


class SimpleEvaluator:
    evaluator_id = "simple"
    version = "1"

    def evaluate(self, *, actual: object, expected: object) -> tuple[Score, ...]:
        value = float(actual == expected)
        return (
            Score(
                metric="accuracy",
                value=value,
                evaluator=EvaluatorRef(evaluator_id=self.evaluator_id, version=self.version),
                higher_is_better=True,
                numerator=value,
                denominator=1.0,
            ),
        )


class SelectiveFailureAdapter(FakeInferenceAdapter):
    async def generate(self, request: InferenceRequest) -> InferenceResponse:
        if request.messages[0].content == "fail":
            raise InferenceAdapterError(
                InferenceErrorCode.SERVER,
                "synthetic endpoint failure",
                retryable=True,
            )
        return InferenceResponse(request_id=request.request_id, text="ok", finish_reason="stop")


class MemoryRunSink:
    def __init__(self) -> None:
        self.working: list[Run] = []
        self.published: list[Run] = []

    def save_working(self, run: Run) -> None:
        self.working.append(run)

    def publish(self, run: Run) -> None:
        self.published.append(run)


def dataset(records: tuple[DatasetRecord, ...]) -> MaterializedDataset:
    snapshot = DatasetSnapshot(
        dataset_id="demo",
        dataset_version="1",
        source="test",
        split="test",
        content_sha256="a" * 64,
        selection_policy="fixture-v1",
        sample_count=len(records),
    )
    return MaterializedDataset(snapshot=snapshot, records=records)


def suite() -> EvaluationSuite:
    return EvaluationSuite(
        suite_id="suite",
        suite_version="1",
        tasks=(
            TaskSpec(
                task_id="task",
                dataset_snapshot_id="demo",
                evaluator=EvaluatorRef(evaluator_id="simple", version="1"),
                metric_names=("accuracy",),
            ),
        ),
        generation=GenerationConfig(max_output_tokens=8, temperature=0.0),
    )


def fingerprint(snapshot: DatasetSnapshot) -> ExecutionFingerprint:
    return ExecutionFingerprint(
        target_id="target",
        adapter_type="fake",
        endpoint_identity="fixture",
        model=ModelIdentity(model_id="model-a"),
        generation=suite().generation,
        prompt_template_version="chat-v1",
        dataset_snapshots=(snapshot,),
        evaluator_versions=(EvaluatorRef(evaluator_id="simple", version="1"),),
        benchmark_protocol_version="bench-v1",
        load_profile=LoadProfile(),
    )


def test_orchestrator_completes_and_emits_content_safe_progress() -> None:
    materialized = dataset(
        (
            DatasetRecord(sample_id="1", input="hello", expected="ok"),
            DatasetRecord(sample_id="2", input="world", expected="ok"),
        )
    )
    sink = MemoryRunSink()
    events: list[ProgressEvent] = []
    orchestrator = EvaluationOrchestrator(
        FakeInferenceAdapter(response_text="ok"),
        {"simple": SimpleEvaluator()},
        run_sink=sink,
        progress_sink=events.append,
    )
    result = asyncio.run(
        orchestrator.run(
            run_id="run-1",
            fingerprint=fingerprint(materialized.snapshot),
            suite=suite(),
            datasets={"demo": materialized},
        )
    )
    assert result.status == RunStatus.SUCCEEDED
    assert len(result.samples) == 2
    assert result.aggregate_scores[0].value == 1.0
    assert sink.published == [result]
    assert events[0].phase == ProgressPhase.RUN_STARTED
    assert events[-1].phase == ProgressPhase.RUN_COMPLETED
    serialized_events = " ".join(event.model_dump_json() for event in events)
    assert "hello" not in serialized_events
    assert "world" not in serialized_events
    assert "ok" not in serialized_events


def test_partial_endpoint_failure_is_typed_without_aborting_run() -> None:
    materialized = dataset(
        (
            DatasetRecord(sample_id="1", input="fail", expected="ok"),
            DatasetRecord(sample_id="2", input="pass", expected="ok"),
        )
    )
    result = asyncio.run(
        EvaluationOrchestrator(
            SelectiveFailureAdapter(response_text="ok"),
            {"simple": SimpleEvaluator()},
        ).run(
            run_id="run-2",
            fingerprint=fingerprint(materialized.snapshot),
            suite=suite(),
            datasets={"demo": materialized},
        )
    )
    assert result.status == RunStatus.SUCCEEDED
    assert result.samples[0].error is not None
    assert result.samples[0].error.category == "inference"
    assert result.samples[0].error.retryable
    assert result.samples[1].error is None


def test_total_endpoint_failure_marks_run_failed() -> None:
    materialized = dataset((DatasetRecord(sample_id="1", input="fail", expected="ok"),))
    result = asyncio.run(
        EvaluationOrchestrator(
            SelectiveFailureAdapter(response_text="ok"),
            {"simple": SimpleEvaluator()},
        ).run(
            run_id="run-3",
            fingerprint=fingerprint(materialized.snapshot),
            suite=suite(),
            datasets={"demo": materialized},
        )
    )
    assert result.status == RunStatus.FAILED
    assert result.samples[0].error is not None
    assert result.samples[0].error.code == InferenceErrorCode.SERVER.value
