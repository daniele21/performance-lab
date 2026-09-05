"""Evaluation orchestration lifecycle independent from concrete runtimes and stores."""

from __future__ import annotations

import asyncio
import json
from collections.abc import Callable, Mapping
from datetime import UTC, datetime
from enum import StrEnum
from typing import Protocol

from pydantic import BaseModel, ConfigDict, Field

from performance_lab.datasets import MaterializedDataset
from performance_lab.domain import (
    ErrorInfo,
    EvaluationSuite,
    ExecutionFingerprint,
    GenerationConfig,
    Measurement,
    Run,
    RunStatus,
    SampleExecution,
    SampleStatus,
    Score,
)
from performance_lab.performance import MetricAvailability, measure_single_request
from performance_lab.plugins import (
    ChatMessage,
    Evaluator,
    InferenceAdapter,
    InferenceAdapterError,
    InferenceRequest,
    MessageRole,
)
from performance_lab.telemetry import TelemetrySession


class OrchestratorError(ValueError):
    pass


class ResumePolicy(StrEnum):
    NEW_RUN_ONLY = "new_run_only"


class ProgressPhase(StrEnum):
    RUN_STARTED = "run_started"
    SAMPLE_STARTED = "sample_started"
    SAMPLE_COMPLETED = "sample_completed"
    RUN_COMPLETED = "run_completed"


class ProgressEvent(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    phase: ProgressPhase
    run_id: str = Field(min_length=1)
    task_id: str | None = None
    sample_id: str | None = None
    completed_samples: int = Field(ge=0)
    total_samples: int = Field(ge=0)
    sample_status: SampleStatus | None = None


class RunSink(Protocol):
    def save_working(self, run: Run) -> None: ...

    def publish(self, run: Run) -> None: ...


ProgressSink = Callable[[ProgressEvent], None]


class EvaluationOrchestrator:
    """Execute a frozen suite against one adapter and return immutable evidence."""

    def __init__(
        self,
        adapter: InferenceAdapter,
        evaluators: Mapping[str, Evaluator],
        *,
        telemetry: TelemetrySession | None = None,
        run_sink: RunSink | None = None,
        progress_sink: ProgressSink | None = None,
    ) -> None:
        self.adapter = adapter
        self.evaluators = dict(evaluators)
        self.telemetry = telemetry
        self.run_sink = run_sink
        self.progress_sink = progress_sink

    async def run(
        self,
        *,
        run_id: str,
        fingerprint: ExecutionFingerprint,
        suite: EvaluationSuite,
        datasets: Mapping[str, MaterializedDataset],
        resume_policy: ResumePolicy = ResumePolicy.NEW_RUN_ONLY,
    ) -> Run:
        if resume_policy != ResumePolicy.NEW_RUN_ONLY:
            raise OrchestratorError("unsupported resume policy")
        self._validate_inputs(fingerprint=fingerprint, suite=suite, datasets=datasets)
        created_at = datetime.now(UTC)
        total_samples = sum(
            min(len(datasets[task.dataset_snapshot_id].records), task.sample_limit)
            if task.sample_limit is not None
            else len(datasets[task.dataset_snapshot_id].records)
            for task in suite.tasks
        )
        working = Run(
            run_id=run_id,
            status=RunStatus.RUNNING,
            fingerprint=fingerprint,
            suite=suite,
            created_at=created_at,
        )
        self._save_working(working)
        self._emit(
            ProgressEvent(
                phase=ProgressPhase.RUN_STARTED,
                run_id=run_id,
                completed_samples=0,
                total_samples=total_samples,
            )
        )
        if self.telemetry is not None:
            await self.telemetry.start(run_id)

        samples: list[SampleExecution] = []
        completed = 0
        cancelled = False
        try:
            for task in suite.tasks:
                dataset = datasets[task.dataset_snapshot_id]
                records = dataset.records[: task.sample_limit]
                evaluator = self.evaluators[task.evaluator.evaluator_id]
                for record in records:
                    self._emit(
                        ProgressEvent(
                            phase=ProgressPhase.SAMPLE_STARTED,
                            run_id=run_id,
                            task_id=task.task_id,
                            sample_id=record.sample_id,
                            completed_samples=completed,
                            total_samples=total_samples,
                        )
                    )
                    sample = await self._execute_sample(
                        run_id=run_id,
                        task_id=task.task_id,
                        sample_id=record.sample_id,
                        model_id=fingerprint.model.model_id,
                        generation=fingerprint.generation,
                        input_value=record.input,
                        expected=record.expected,
                        evaluator=evaluator,
                    )
                    samples.append(sample)
                    completed += 1
                    self._emit(
                        ProgressEvent(
                            phase=ProgressPhase.SAMPLE_COMPLETED,
                            run_id=run_id,
                            task_id=task.task_id,
                            sample_id=record.sample_id,
                            completed_samples=completed,
                            total_samples=total_samples,
                            sample_status=sample.status,
                        )
                    )
                    self._save_working(working.model_copy(update={"samples": tuple(samples)}))
        except asyncio.CancelledError:
            cancelled = True

        telemetry_measurements: tuple[Measurement, ...] = ()
        if self.telemetry is not None:
            telemetry_result = await self.telemetry.stop()
            telemetry_measurements = telemetry_result.measurements

        aggregate_scores = _aggregate_scores(samples)
        if cancelled:
            status = RunStatus.CANCELLED
        elif samples and all(sample.status != SampleStatus.SUCCEEDED for sample in samples):
            status = RunStatus.FAILED
        else:
            status = RunStatus.SUCCEEDED
        completed_run = Run(
            run_id=run_id,
            status=status,
            fingerprint=fingerprint,
            suite=suite,
            created_at=created_at,
            completed_at=datetime.now(UTC),
            aggregate_scores=aggregate_scores,
            aggregate_measurements=telemetry_measurements,
            samples=tuple(samples),
        )
        if self.run_sink is not None:
            self.run_sink.publish(completed_run)
        self._emit(
            ProgressEvent(
                phase=ProgressPhase.RUN_COMPLETED,
                run_id=run_id,
                completed_samples=completed,
                total_samples=total_samples,
            )
        )
        return completed_run

    def _validate_inputs(
        self,
        *,
        fingerprint: ExecutionFingerprint,
        suite: EvaluationSuite,
        datasets: Mapping[str, MaterializedDataset],
    ) -> None:
        frozen_snapshots = {
            snapshot.dataset_id: snapshot for snapshot in fingerprint.dataset_snapshots
        }
        for task in suite.tasks:
            dataset = datasets.get(task.dataset_snapshot_id)
            if dataset is None:
                raise OrchestratorError(f"dataset not supplied: {task.dataset_snapshot_id}")
            frozen = frozen_snapshots.get(task.dataset_snapshot_id)
            if frozen != dataset.snapshot:
                raise OrchestratorError(
                    f"dataset snapshot differs from frozen fingerprint: {task.dataset_snapshot_id}"
                )
            evaluator = self.evaluators.get(task.evaluator.evaluator_id)
            if evaluator is None:
                raise OrchestratorError(f"evaluator not registered: {task.evaluator.evaluator_id}")
            if evaluator.version != task.evaluator.version:
                raise OrchestratorError(
                    f"evaluator version mismatch: {task.evaluator.evaluator_id}"
                )

    async def _execute_sample(
        self,
        *,
        run_id: str,
        task_id: str,
        sample_id: str,
        model_id: str,
        generation: GenerationConfig,
        input_value: object,
        expected: object,
        evaluator: Evaluator,
    ) -> SampleExecution:
        started_at = datetime.now(UTC)
        request = InferenceRequest(
            request_id=f"{run_id}:{task_id}:{sample_id}",
            messages=(ChatMessage(role=MessageRole.USER, content=_render_input(input_value)),),
            generation=generation,
            model=model_id,
        )
        try:
            measured = await measure_single_request(self.adapter, request, streaming=False)
            response = measured.response
            if response is None:
                raise OrchestratorError("non-streaming measured inference returned no response")
            scores = evaluator.evaluate(actual=response.text, expected=expected)
            measurements = tuple(
                metric.measurement
                for metric in measured.benchmark.metrics
                if metric.availability == MetricAvailability.AVAILABLE
                and metric.measurement is not None
            )
            status = SampleStatus.SUCCEEDED
            error = None
            input_tokens = measured.benchmark.input_tokens
            output_tokens = measured.benchmark.output_tokens
        except InferenceAdapterError as exc:
            scores = ()
            measurements = ()
            status = SampleStatus.FAILED
            error = ErrorInfo(code=exc.code.value, category="inference", retryable=exc.retryable)
            input_tokens = None
            output_tokens = None
        except (ValueError, TypeError) as exc:
            scores = ()
            measurements = ()
            status = SampleStatus.FAILED
            error = ErrorInfo(code=type(exc).__name__, category="evaluation", retryable=False)
            input_tokens = None
            output_tokens = None
        return SampleExecution(
            sample_id=sample_id,
            task_id=task_id,
            status=status,
            started_at=started_at,
            completed_at=datetime.now(UTC),
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            measurements=measurements,
            scores=scores,
            error=error,
        )

    def _save_working(self, run: Run) -> None:
        if self.run_sink is not None:
            self.run_sink.save_working(run)

    def _emit(self, event: ProgressEvent) -> None:
        if self.progress_sink is not None:
            self.progress_sink(event)


def _render_input(value: object) -> str:
    if isinstance(value, str):
        return value
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def _aggregate_scores(samples: list[SampleExecution]) -> tuple[Score, ...]:
    groups: dict[tuple[str, str, str, bool], list[Score]] = {}
    for sample in samples:
        for score in sample.scores:
            key = (
                score.metric,
                score.evaluator.evaluator_id,
                score.evaluator.version,
                score.higher_is_better,
            )
            groups.setdefault(key, []).append(score)
    aggregates: list[Score] = []
    for scores in groups.values():
        first = scores[0]
        aggregates.append(
            Score(
                metric=first.metric,
                value=sum(score.value for score in scores) / len(scores),
                evaluator=first.evaluator,
                higher_is_better=first.higher_is_better,
            )
        )
    return tuple(aggregates)
