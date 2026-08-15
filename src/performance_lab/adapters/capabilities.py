"""Evidence-based endpoint capability probing."""

from __future__ import annotations

import json
from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field

from performance_lab.domain import GenerationConfig
from performance_lab.plugins import (
    ChatMessage,
    InferenceAdapter,
    InferenceAdapterError,
    InferenceErrorCode,
    InferenceRequest,
    MessageRole,
    ProbeResult,
)


class CapabilityProbeModel(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")


class CapabilityName(StrEnum):
    STREAMING = "streaming"
    MODEL_DISCOVERY = "model_discovery"
    TOKEN_USAGE = "token_usage"
    SEED = "seed"
    STRUCTURED_OUTPUT = "structured_output"


class SupportState(StrEnum):
    SUPPORTED = "supported"
    UNSUPPORTED = "unsupported"
    UNKNOWN = "unknown"


class EvidenceSource(StrEnum):
    DECLARED = "declared"
    OBSERVED = "observed"
    NONE = "none"


class CapabilityEvidence(CapabilityProbeModel):
    capability: CapabilityName
    declared: SupportState = SupportState.UNKNOWN
    observed: SupportState = SupportState.UNKNOWN
    effective: SupportState = SupportState.UNKNOWN
    effective_source: EvidenceSource = EvidenceSource.NONE
    detail: str | None = None


class EndpointCapabilityReport(CapabilityProbeModel):
    adapter_id: str = Field(min_length=1)
    healthy: bool
    models: tuple[str, ...] = ()
    active_checks: bool
    capabilities: tuple[CapabilityEvidence, ...]

    def capability(self, name: CapabilityName) -> CapabilityEvidence:
        for capability in self.capabilities:
            if capability.capability == name:
                return capability
        raise KeyError(name)


async def probe_endpoint_capabilities(
    adapter: InferenceAdapter,
    *,
    model: str | None = None,
    active_checks: bool = False,
) -> EndpointCapabilityReport:
    """Build capability evidence without converting absence of evidence into unsupported."""

    passive = await adapter.probe()
    declared = _declared_states(passive)
    observed: dict[CapabilityName, SupportState] = {
        CapabilityName.MODEL_DISCOVERY: (
            SupportState.SUPPORTED if passive.healthy else SupportState.UNKNOWN
        )
    }
    details: dict[CapabilityName, str] = {}

    if active_checks and passive.healthy:
        selected_model = model or (passive.models[0] if passive.models else None)
        await _active_generation_checks(
            adapter,
            selected_model=selected_model,
            observed=observed,
            details=details,
        )

    evidence = tuple(
        _merge_evidence(
            name, declared.get(name, SupportState.UNKNOWN), observed.get(name), details
        )
        for name in CapabilityName
    )
    return EndpointCapabilityReport(
        adapter_id=passive.adapter_id,
        healthy=passive.healthy,
        models=passive.models,
        active_checks=active_checks,
        capabilities=evidence,
    )


def _declared_states(probe: ProbeResult) -> dict[CapabilityName, SupportState]:
    capabilities = probe.capabilities
    return {
        CapabilityName.STREAMING: _state(capabilities.streaming),
        CapabilityName.MODEL_DISCOVERY: _state(capabilities.model_discovery),
        CapabilityName.TOKEN_USAGE: _state(capabilities.token_usage),
        CapabilityName.SEED: _state(capabilities.seed),
        CapabilityName.STRUCTURED_OUTPUT: _state(capabilities.structured_output),
    }


async def _active_generation_checks(
    adapter: InferenceAdapter,
    *,
    selected_model: str | None,
    observed: dict[CapabilityName, SupportState],
    details: dict[CapabilityName, str],
) -> None:
    base_generation = GenerationConfig(max_output_tokens=8, temperature=0.0)
    base_request = InferenceRequest(
        request_id="capability-probe:base",
        messages=(ChatMessage(role=MessageRole.USER, content="Reply with OK."),),
        generation=base_generation,
        model=selected_model,
    )

    try:
        response = await adapter.generate(base_request)
    except InferenceAdapterError as exc:
        details[CapabilityName.TOKEN_USAGE] = f"base generation failed: {exc.code.value}"
    else:
        if response.usage is not None:
            observed[CapabilityName.TOKEN_USAGE] = SupportState.SUPPORTED
        else:
            details[CapabilityName.TOKEN_USAGE] = "generation succeeded but returned no usage"

    streaming_request = base_request.model_copy(update={"request_id": "capability-probe:stream"})
    try:
        saw_chunk = False
        async for _ in adapter.stream(streaming_request):
            saw_chunk = True
    except InferenceAdapterError as exc:
        observed[CapabilityName.STREAMING] = _error_state(exc)
        details[CapabilityName.STREAMING] = exc.code.value
    else:
        if saw_chunk:
            observed[CapabilityName.STREAMING] = SupportState.SUPPORTED
        else:
            details[CapabilityName.STREAMING] = "stream completed without chunks"

    seed_request = base_request.model_copy(
        update={
            "request_id": "capability-probe:seed",
            "generation": base_generation.model_copy(update={"seed": 7}),
        }
    )
    try:
        await adapter.generate(seed_request)
    except InferenceAdapterError as exc:
        observed[CapabilityName.SEED] = _error_state(exc)
        details[CapabilityName.SEED] = exc.code.value
    else:
        observed[CapabilityName.SEED] = SupportState.SUPPORTED
        details[CapabilityName.SEED] = "seed parameter accepted by endpoint"

    structured_request = base_request.model_copy(
        update={
            "request_id": "capability-probe:structured",
            "messages": (
                ChatMessage(
                    role=MessageRole.USER,
                    content='Return exactly {"probe":true} as JSON.',
                ),
            ),
            "generation": base_generation.model_copy(update={"response_format": "json_object"}),
        }
    )
    try:
        response = await adapter.generate(structured_request)
    except InferenceAdapterError as exc:
        observed[CapabilityName.STRUCTURED_OUTPUT] = _error_state(exc)
        details[CapabilityName.STRUCTURED_OUTPUT] = exc.code.value
    else:
        try:
            parsed = json.loads(response.text)
        except json.JSONDecodeError:
            details[CapabilityName.STRUCTURED_OUTPUT] = (
                "response-format request succeeded but returned invalid JSON"
            )
        else:
            if isinstance(parsed, dict):
                observed[CapabilityName.STRUCTURED_OUTPUT] = SupportState.SUPPORTED
            else:
                details[CapabilityName.STRUCTURED_OUTPUT] = (
                    "response-format request returned non-object JSON"
                )


def _merge_evidence(
    name: CapabilityName,
    declared: SupportState,
    observed: SupportState | None,
    details: dict[CapabilityName, str],
) -> CapabilityEvidence:
    observed_state = observed or SupportState.UNKNOWN
    if observed_state != SupportState.UNKNOWN:
        effective = observed_state
        source = EvidenceSource.OBSERVED
    elif declared != SupportState.UNKNOWN:
        effective = declared
        source = EvidenceSource.DECLARED
    else:
        effective = SupportState.UNKNOWN
        source = EvidenceSource.NONE
    return CapabilityEvidence(
        capability=name,
        declared=declared,
        observed=observed_state,
        effective=effective,
        effective_source=source,
        detail=details.get(name),
    )


def _state(value: bool | None) -> SupportState:
    if value is True:
        return SupportState.SUPPORTED
    if value is False:
        return SupportState.UNSUPPORTED
    return SupportState.UNKNOWN


def _error_state(error: InferenceAdapterError) -> SupportState:
    if error.code in {InferenceErrorCode.UNSUPPORTED_OPTION, InferenceErrorCode.INVALID_REQUEST}:
        return SupportState.UNSUPPORTED
    return SupportState.UNKNOWN
