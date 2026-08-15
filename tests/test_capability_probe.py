import asyncio
from collections.abc import AsyncIterator

from performance_lab.adapters import (
    CapabilityName,
    EvidenceSource,
    SupportState,
    probe_endpoint_capabilities,
)
from performance_lab.plugins import (
    AdapterCapabilities,
    FakeInferenceAdapter,
    InferenceChunk,
    InferenceRequest,
    InferenceResponse,
    ProbeResult,
    TokenUsage,
)


class CapabilityFake(FakeInferenceAdapter):
    async def probe(self) -> ProbeResult:
        return ProbeResult(
            healthy=True,
            adapter_id=self.adapter_id,
            models=("model-a",),
            capabilities=AdapterCapabilities(
                streaming=True,
                model_discovery=True,
                token_usage=None,
                seed=None,
                structured_output=None,
            ),
        )

    async def generate(self, request: InferenceRequest) -> InferenceResponse:
        text = '{"probe":true}' if request.generation.response_format == "json_object" else "OK"
        return InferenceResponse(
            request_id=request.request_id,
            text=text,
            model=request.model,
            finish_reason="stop",
            usage=TokenUsage(input_tokens=3, output_tokens=2),
        )

    async def _stream(self, request: InferenceRequest) -> AsyncIterator[InferenceChunk]:
        yield InferenceChunk(
            request_id=request.request_id,
            text_delta="OK",
            emitted_at_ns=1,
            finish_reason="stop",
        )

    def stream(self, request: InferenceRequest) -> AsyncIterator[InferenceChunk]:
        return self._stream(request)


def test_passive_probe_keeps_unobserved_capabilities_distinct() -> None:
    report = asyncio.run(probe_endpoint_capabilities(CapabilityFake(), active_checks=False))
    streaming = report.capability(CapabilityName.STREAMING)
    seed = report.capability(CapabilityName.SEED)
    discovery = report.capability(CapabilityName.MODEL_DISCOVERY)

    assert streaming.declared == SupportState.SUPPORTED
    assert streaming.observed == SupportState.UNKNOWN
    assert streaming.effective_source == EvidenceSource.DECLARED
    assert seed.effective == SupportState.UNKNOWN
    assert seed.effective_source == EvidenceSource.NONE
    assert discovery.observed == SupportState.SUPPORTED


def test_active_probe_records_observed_generation_capabilities() -> None:
    report = asyncio.run(
        probe_endpoint_capabilities(CapabilityFake(), model="model-a", active_checks=True)
    )
    for name in (
        CapabilityName.STREAMING,
        CapabilityName.TOKEN_USAGE,
        CapabilityName.SEED,
        CapabilityName.STRUCTURED_OUTPUT,
    ):
        capability = report.capability(name)
        assert capability.observed == SupportState.SUPPORTED
        assert capability.effective == SupportState.SUPPORTED
        assert capability.effective_source == EvidenceSource.OBSERVED
