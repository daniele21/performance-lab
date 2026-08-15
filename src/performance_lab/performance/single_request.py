"""Single-request endpoint latency protocol with explicit metric availability."""

from __future__ import annotations

from enum import StrEnum
from time import perf_counter_ns

from pydantic import BaseModel, ConfigDict, Field

from performance_lab.domain import Measurement, MeasurementProvenance, MeasurementScope
from performance_lab.plugins import InferenceAdapter, InferenceRequest, TokenUsage


class PerformanceModel(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")


class RunTemperature(StrEnum):
    COLD = "cold"
    WARMUP = "warmup"
    MEASURED_WARM = "measured_warm"


class MetricAvailability(StrEnum):
    AVAILABLE = "available"
    UNAVAILABLE = "unavailable"


class RuntimeMetric(PerformanceModel):
    name: str = Field(min_length=1)
    availability: MetricAvailability
    measurement: Measurement | None = None
    reason: str | None = None


class SingleRequestBenchmark(PerformanceModel):
    request_id: str = Field(min_length=1)
    protocol_version: str = "single-request-v1"
    run_temperature: RunTemperature
    streaming: bool
    metrics: tuple[RuntimeMetric, ...]
    input_tokens: int | None = Field(default=None, ge=0)
    output_tokens: int | None = Field(default=None, ge=0)
    finish_reason: str | None = None

    def metric(self, name: str) -> RuntimeMetric:
        for metric in self.metrics:
            if metric.name == name:
                return metric
        raise KeyError(name)


async def benchmark_single_request(
    adapter: InferenceAdapter,
    request: InferenceRequest,
    *,
    run_temperature: RunTemperature = RunTemperature.MEASURED_WARM,
    streaming: bool = True,
) -> SingleRequestBenchmark:
    """Measure one inference call strictly at the Performance Lab client boundary."""

    protocol_version = "single-request-v1"
    request_started_ns = perf_counter_ns()
    setup_started_ns = request_started_ns
    first_token_ns: int | None = None
    usage: TokenUsage | None = None
    finish_reason: str | None = None

    if streaming:
        stream = adapter.stream(request)
        setup_completed_ns = perf_counter_ns()
        async for chunk in stream:
            if first_token_ns is None and chunk.text_delta:
                first_token_ns = chunk.emitted_at_ns
            if chunk.usage is not None:
                usage = chunk.usage
            if chunk.finish_reason is not None:
                finish_reason = chunk.finish_reason
    else:
        setup_completed_ns = perf_counter_ns()
        response = await adapter.generate(request)
        usage = response.usage
        finish_reason = response.finish_reason

    completed_ns = perf_counter_ns()
    metrics: list[RuntimeMetric] = [
        _available_ms(
            "request_setup_ms",
            setup_completed_ns - setup_started_ns,
            protocol_version,
        ),
        _available_ms(
            "total_latency_ms",
            completed_ns - request_started_ns,
            protocol_version,
        ),
    ]

    if streaming and first_token_ns is not None:
        metrics.append(
            _available_ms(
                "ttft_ms",
                max(0, first_token_ns - request_started_ns),
                protocol_version,
            )
        )
    elif streaming:
        metrics.append(_unavailable("ttft_ms", "stream emitted no text token"))
    else:
        metrics.append(
            _unavailable("ttft_ms", "non-streaming endpoint has no observable first token")
        )

    input_tokens = usage.input_tokens if usage is not None else None
    output_tokens = usage.output_tokens if usage is not None else None
    if input_tokens is not None:
        metrics.append(_available_count("input_tokens", input_tokens, protocol_version))
    else:
        metrics.append(_unavailable("input_tokens", "endpoint did not report input token usage"))
    if output_tokens is not None:
        metrics.append(_available_count("output_tokens", output_tokens, protocol_version))
    else:
        metrics.append(_unavailable("output_tokens", "endpoint did not report output token usage"))

    if output_tokens is None or output_tokens == 0:
        metrics.append(
            _unavailable("output_tokens_per_second", "output token count is unavailable or zero")
        )
    elif streaming and first_token_ns is not None and completed_ns > first_token_ns:
        seconds = (completed_ns - first_token_ns) / 1_000_000_000
        metrics.append(
            _available_rate(
                "output_tokens_per_second",
                output_tokens / seconds,
                protocol_version,
            )
        )
    else:
        seconds = (completed_ns - request_started_ns) / 1_000_000_000
        if seconds > 0:
            metrics.append(
                _available_rate(
                    "output_tokens_per_second",
                    output_tokens / seconds,
                    protocol_version,
                )
            )
        else:
            metrics.append(_unavailable("output_tokens_per_second", "timing window is zero"))

    return SingleRequestBenchmark(
        request_id=request.request_id,
        run_temperature=run_temperature,
        streaming=streaming,
        metrics=tuple(metrics),
        input_tokens=input_tokens,
        output_tokens=output_tokens,
        finish_reason=finish_reason,
    )


def _available_ms(name: str, nanoseconds: int, protocol_version: str) -> RuntimeMetric:
    return RuntimeMetric(
        name=name,
        availability=MetricAvailability.AVAILABLE,
        measurement=Measurement(
            name=name,
            value=nanoseconds / 1_000_000,
            unit="ms",
            scope=MeasurementScope.SAMPLE,
            provenance=MeasurementProvenance.CLIENT,
            protocol_version=protocol_version,
        ),
    )


def _available_count(name: str, value: int, protocol_version: str) -> RuntimeMetric:
    return RuntimeMetric(
        name=name,
        availability=MetricAvailability.AVAILABLE,
        measurement=Measurement(
            name=name,
            value=float(value),
            unit="tokens",
            scope=MeasurementScope.SAMPLE,
            provenance=MeasurementProvenance.CLIENT,
            protocol_version=protocol_version,
        ),
    )


def _available_rate(name: str, value: float, protocol_version: str) -> RuntimeMetric:
    return RuntimeMetric(
        name=name,
        availability=MetricAvailability.AVAILABLE,
        measurement=Measurement(
            name=name,
            value=value,
            unit="tokens/s",
            scope=MeasurementScope.SAMPLE,
            provenance=MeasurementProvenance.CLIENT,
            protocol_version=protocol_version,
        ),
    )


def _unavailable(name: str, reason: str) -> RuntimeMetric:
    return RuntimeMetric(
        name=name,
        availability=MetricAvailability.UNAVAILABLE,
        reason=reason,
    )
