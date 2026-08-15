import asyncio
from collections.abc import AsyncIterator
from time import perf_counter_ns

from performance_lab.domain import GenerationConfig
from performance_lab.performance import MetricAvailability, RunTemperature, benchmark_single_request
from performance_lab.plugins import (
    AdapterCapabilities,
    ChatMessage,
    InferenceChunk,
    InferenceRequest,
    InferenceResponse,
    MessageRole,
    ProbeResult,
    TokenUsage,
)


class UsageAdapter:
    adapter_id = "usage-fake"

    async def probe(self) -> ProbeResult:
        return ProbeResult(
            healthy=True,
            adapter_id=self.adapter_id,
            capabilities=AdapterCapabilities(streaming=True, token_usage=True),
        )

    async def generate(self, request: InferenceRequest) -> InferenceResponse:
        return InferenceResponse(
            request_id=request.request_id,
            text="hello",
            finish_reason="stop",
            usage=TokenUsage(input_tokens=4, output_tokens=2),
        )

    async def _stream(self, request: InferenceRequest) -> AsyncIterator[InferenceChunk]:
        await asyncio.sleep(0)
        yield InferenceChunk(
            request_id=request.request_id,
            text_delta="hel",
            emitted_at_ns=perf_counter_ns(),
        )
        await asyncio.sleep(0.001)
        yield InferenceChunk(
            request_id=request.request_id,
            text_delta="lo",
            emitted_at_ns=perf_counter_ns(),
            finish_reason="stop",
            usage=TokenUsage(input_tokens=4, output_tokens=2),
        )

    def stream(self, request: InferenceRequest) -> AsyncIterator[InferenceChunk]:
        return self._stream(request)

    async def cancel(self, request_id: str) -> bool:
        del request_id
        return False


def request() -> InferenceRequest:
    return InferenceRequest(
        request_id="request-1",
        messages=(ChatMessage(role=MessageRole.USER, content="hello"),),
        generation=GenerationConfig(max_output_tokens=8, temperature=0.0),
    )


def test_streaming_protocol_reports_ttft_and_token_rate() -> None:
    result = asyncio.run(
        benchmark_single_request(
            UsageAdapter(),
            request(),
            run_temperature=RunTemperature.MEASURED_WARM,
            streaming=True,
        )
    )
    assert result.metric("ttft_ms").availability == MetricAvailability.AVAILABLE
    assert result.metric("ttft_ms").measurement is not None
    assert result.metric("total_latency_ms").measurement is not None
    assert result.metric("output_tokens_per_second").measurement is not None
    assert result.output_tokens == 2


def test_non_streaming_ttft_is_explicitly_unavailable() -> None:
    result = asyncio.run(benchmark_single_request(UsageAdapter(), request(), streaming=False))
    ttft = result.metric("ttft_ms")
    assert ttft.availability == MetricAvailability.UNAVAILABLE
    assert ttft.measurement is None
    assert "non-streaming" in (ttft.reason or "")
    assert result.metric("output_tokens_per_second").availability == MetricAvailability.AVAILABLE


def test_run_temperature_is_preserved() -> None:
    result = asyncio.run(
        benchmark_single_request(
            UsageAdapter(),
            request(),
            run_temperature=RunTemperature.WARMUP,
        )
    )
    assert result.run_temperature == RunTemperature.WARMUP
    assert result.protocol_version == "single-request-v1"
