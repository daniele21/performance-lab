"""Deterministic plugin fakes used by orchestration and workstream tests."""

from __future__ import annotations

from collections.abc import AsyncIterator, Mapping, Sequence
from pathlib import Path

from performance_lab.domain import Measurement, Run, Score

from .contracts import (
    AdapterCapabilities,
    ExternalBenchmarkResult,
    InferenceChunk,
    InferenceRequest,
    InferenceResponse,
    ProbeResult,
    TelemetryCollectorCapabilities,
)


class FakeInferenceAdapter:
    adapter_id = "fake-inference"

    def __init__(
        self,
        *,
        response_text: str = "ok",
        stream_deltas: tuple[str, ...] = ("o", "k"),
        models: tuple[str, ...] = ("fake-model",),
    ) -> None:
        self.response_text = response_text
        self.stream_deltas = stream_deltas
        self.models = models
        self.cancelled_request_ids: list[str] = []
        self.requests: list[InferenceRequest] = []

    async def probe(self) -> ProbeResult:
        return ProbeResult(
            healthy=True,
            adapter_id=self.adapter_id,
            models=self.models,
            capabilities=AdapterCapabilities(
                streaming=True,
                model_discovery=True,
                token_usage=False,
            ),
        )

    async def generate(self, request: InferenceRequest) -> InferenceResponse:
        self.requests.append(request)
        return InferenceResponse(
            request_id=request.request_id,
            text=self.response_text,
            model=request.model or self.models[0],
            finish_reason="stop",
        )

    async def _stream(self, request: InferenceRequest) -> AsyncIterator[InferenceChunk]:
        self.requests.append(request)
        for index, delta in enumerate(self.stream_deltas, start=1):
            yield InferenceChunk(
                request_id=request.request_id,
                text_delta=delta,
                emitted_at_ns=index,
                finish_reason="stop" if index == len(self.stream_deltas) else None,
            )

    def stream(self, request: InferenceRequest) -> AsyncIterator[InferenceChunk]:
        return self._stream(request)

    async def cancel(self, request_id: str) -> bool:
        self.cancelled_request_ids.append(request_id)
        return True


class FakeTaskLoader:
    loader_id = "fake-loader"

    def __init__(self, records: Sequence[Mapping[str, object]]) -> None:
        self.records = tuple(records)

    def load(self, source: Path, *, split: str | None = None) -> Sequence[Mapping[str, object]]:
        del source, split
        return self.records


class FakeEvaluator:
    evaluator_id = "fake-evaluator"
    version = "1"

    def __init__(self, scores: tuple[Score, ...]) -> None:
        self.scores = scores

    def evaluate(self, *, actual: object, expected: object) -> tuple[Score, ...]:
        del actual, expected
        return self.scores


class FakeTelemetryCollector:
    collector_id = "fake-telemetry"
    protocol_version = "fake-v1"

    def __init__(self, measurements: tuple[Measurement, ...] = ()) -> None:
        self.measurements = measurements
        self.started_run_id: str | None = None

    def capabilities(self) -> TelemetryCollectorCapabilities:
        return TelemetryCollectorCapabilities(
            metric_names=frozenset(measurement.name for measurement in self.measurements),
            sampling=False,
        )

    async def start(self, run_id: str) -> None:
        self.started_run_id = run_id

    async def stop(self) -> tuple[Measurement, ...]:
        return self.measurements


class FakeResultExporter:
    exporter_id = "fake-exporter"

    def export(self, run: Run, destination: Path) -> Path:
        destination.write_text(run.model_dump_json(indent=2), encoding="utf-8")
        return destination


class FakeExternalBenchmarkRunner:
    runner_id = "fake-external-runner"

    async def run(
        self, *, task_ids: Sequence[str], config: Mapping[str, object]
    ) -> ExternalBenchmarkResult:
        del config
        return ExternalBenchmarkResult(
            runner_id=self.runner_id,
            framework_version="fake-1",
            task_ids=tuple(task_ids),
            metrics={"score": 1.0},
        )
