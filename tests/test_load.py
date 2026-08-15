import asyncio

import pytest
from pydantic import ValidationError

from performance_lab.domain import GenerationConfig
from performance_lab.performance.load import LoadAttemptStatus, LoadProfileSpec, run_load_profile
from performance_lab.plugins import (
    AdapterCapabilities,
    ChatMessage,
    InferenceAdapterError,
    InferenceErrorCode,
    InferenceRequest,
    InferenceResponse,
    MessageRole,
    ProbeResult,
    TokenUsage,
)


class LoadFakeAdapter:
    adapter_id = "load-fake"

    async def probe(self) -> ProbeResult:
        return ProbeResult(
            healthy=True,
            adapter_id=self.adapter_id,
            capabilities=AdapterCapabilities(streaming=False, token_usage=True),
        )

    async def generate(self, request: InferenceRequest) -> InferenceResponse:
        sequence = int(request.request_id.rsplit("-", 1)[1])
        await asyncio.sleep(0.002)
        if sequence == 2:
            raise InferenceAdapterError(
                InferenceErrorCode.TIMEOUT,
                "synthetic timeout",
                retryable=True,
            )
        return InferenceResponse(
            request_id=request.request_id,
            text="ok",
            usage=TokenUsage(input_tokens=1, output_tokens=1),
        )

    def stream(self, request: InferenceRequest):
        del request
        raise AssertionError("stream must not be used in this test")

    async def cancel(self, request_id: str) -> bool:
        del request_id
        return False


def request_factory(sequence: int) -> InferenceRequest:
    return InferenceRequest(
        request_id=f"load-{sequence}",
        messages=(ChatMessage(role=MessageRole.USER, content="hello"),),
        generation=GenerationConfig(max_output_tokens=4, temperature=0.0),
    )


def test_fixed_count_profile_captures_throughput_errors_and_queue_delay() -> None:
    result = asyncio.run(
        run_load_profile(
            LoadFakeAdapter(),
            request_factory,
            LoadProfileSpec(concurrency=2, request_count=6, streaming=False),
        )
    )
    assert len(result.attempts) == 6
    assert result.success_count == 5
    assert result.timeout_count == 1
    assert result.error_count == 0
    assert result.requests_per_second > 0
    assert len(result.latency_ms) == 5
    assert max(result.queue_delay_ms) > 0
    assert result.attempts[2].status == LoadAttemptStatus.TIMEOUT


def test_bounded_duration_profile_stops_after_deadline() -> None:
    result = asyncio.run(
        run_load_profile(
            LoadFakeAdapter(),
            request_factory,
            LoadProfileSpec(concurrency=1, duration_seconds=0.01, streaming=False),
        )
    )
    assert len(result.attempts) >= 1
    assert result.duration_ms >= 10
    assert result.protocol_version == "load-v1"


def test_profile_requires_exactly_one_termination_mode() -> None:
    with pytest.raises(ValidationError):
        LoadProfileSpec(concurrency=1)
    with pytest.raises(ValidationError):
        LoadProfileSpec(concurrency=1, request_count=2, duration_seconds=1.0)
