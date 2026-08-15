"""Stable plugin contracts shared across independent Performance Lab workstreams."""

from __future__ import annotations

from collections.abc import AsyncIterator, Mapping, Sequence
from enum import StrEnum
from pathlib import Path
from typing import Protocol, runtime_checkable

from pydantic import BaseModel, ConfigDict, Field

from performance_lab.domain import GenerationConfig, Measurement, Run, Score


class ContractModel(BaseModel):
    """Immutable value object used at plugin boundaries."""

    model_config = ConfigDict(frozen=True, extra="forbid")


class PluginKind(StrEnum):
    INFERENCE_ADAPTER = "inference_adapter"
    TASK_LOADER = "task_loader"
    EVALUATOR = "evaluator"
    TELEMETRY_COLLECTOR = "telemetry_collector"
    RESULT_EXPORTER = "result_exporter"
    EXTERNAL_BENCHMARK_RUNNER = "external_benchmark_runner"


class MessageRole(StrEnum):
    SYSTEM = "system"
    USER = "user"
    ASSISTANT = "assistant"


class ChatMessage(ContractModel):
    role: MessageRole
    content: str = Field(min_length=1)


class InferenceRequest(ContractModel):
    request_id: str = Field(min_length=1)
    messages: tuple[ChatMessage, ...]
    generation: GenerationConfig
    model: str | None = None


class TokenUsage(ContractModel):
    input_tokens: int | None = Field(default=None, ge=0)
    output_tokens: int | None = Field(default=None, ge=0)


class AdapterCapabilities(ContractModel):
    streaming: bool | None = None
    model_discovery: bool | None = None
    token_usage: bool | None = None
    seed: bool | None = None
    structured_output: bool | None = None
    supported_generation_parameters: frozenset[str] = frozenset()


class ProbeResult(ContractModel):
    healthy: bool
    adapter_id: str = Field(min_length=1)
    models: tuple[str, ...] = ()
    capabilities: AdapterCapabilities = AdapterCapabilities()
    metadata: Mapping[str, str] = Field(default_factory=dict)


class InferenceChunk(ContractModel):
    request_id: str = Field(min_length=1)
    text_delta: str = ""
    emitted_at_ns: int = Field(ge=0)
    finish_reason: str | None = None
    usage: TokenUsage | None = None


class InferenceResponse(ContractModel):
    request_id: str = Field(min_length=1)
    text: str
    model: str | None = None
    finish_reason: str | None = None
    usage: TokenUsage | None = None
    response_metadata: Mapping[str, str] = Field(default_factory=dict)


class InferenceErrorCode(StrEnum):
    INVALID_REQUEST = "invalid_request"
    UNSUPPORTED_OPTION = "unsupported_option"
    AUTHENTICATION = "authentication"
    CONNECTION = "connection"
    TIMEOUT = "timeout"
    RATE_LIMIT = "rate_limit"
    SERVER = "server"
    CANCELLED = "cancelled"
    PROTOCOL = "protocol"


class InferenceAdapterError(RuntimeError):
    """Normalized adapter failure; raw provider exceptions stay behind the boundary."""

    def __init__(
        self,
        code: InferenceErrorCode,
        message: str,
        *,
        retryable: bool = False,
        status_code: int | None = None,
    ) -> None:
        super().__init__(message)
        self.code = code
        self.retryable = retryable
        self.status_code = status_code


@runtime_checkable
class InferenceAdapter(Protocol):
    adapter_id: str

    async def probe(self) -> ProbeResult: ...

    async def generate(self, request: InferenceRequest) -> InferenceResponse: ...

    def stream(self, request: InferenceRequest) -> AsyncIterator[InferenceChunk]: ...

    async def cancel(self, request_id: str) -> bool: ...


@runtime_checkable
class TaskLoader(Protocol):
    loader_id: str

    def load(self, source: Path, *, split: str | None = None) -> Sequence[Mapping[str, object]]: ...


@runtime_checkable
class Evaluator(Protocol):
    evaluator_id: str
    version: str

    def evaluate(self, *, actual: object, expected: object) -> tuple[Score, ...]: ...


class TelemetryCollectorCapabilities(ContractModel):
    metric_names: frozenset[str] = frozenset()
    sampling: bool = False


@runtime_checkable
class TelemetryCollector(Protocol):
    collector_id: str
    protocol_version: str

    def capabilities(self) -> TelemetryCollectorCapabilities: ...

    async def start(self, run_id: str) -> None: ...

    async def stop(self) -> tuple[Measurement, ...]: ...


@runtime_checkable
class ResultExporter(Protocol):
    exporter_id: str

    def export(self, run: Run, destination: Path) -> Path: ...


class ExternalBenchmarkResult(ContractModel):
    runner_id: str = Field(min_length=1)
    framework_version: str = Field(min_length=1)
    task_ids: tuple[str, ...]
    metrics: Mapping[str, float]
    artifact_paths: tuple[str, ...] = ()


@runtime_checkable
class ExternalBenchmarkRunner(Protocol):
    runner_id: str

    async def run(
        self, *, task_ids: Sequence[str], config: Mapping[str, object]
    ) -> ExternalBenchmarkResult: ...
