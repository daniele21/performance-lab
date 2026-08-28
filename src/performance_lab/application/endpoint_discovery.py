"""Bounded endpoint discovery for the local browser product."""

from __future__ import annotations

from collections.abc import Mapping

import httpx

from performance_lab.adapters import OpenAICompatibleAdapter
from performance_lab.domain import EndpointProfile
from performance_lab.plugins import AdapterCapabilities

from .ui_models import (
    CapabilitySupportReadModel,
    DiscoveredModelReadModel,
    EndpointConnectionInput,
    EndpointProbeReadModel,
    RuntimeParameterReadModel,
)


def endpoint_identity(connection: EndpointConnectionInput) -> str:
    """Return a persistence-safe local endpoint identity without credentials."""
    url = connection.base_url
    host = url.host or "localhost"
    port = f":{url.port}" if url.port is not None else ""
    path = url.path or "/"
    return f"{host}{port}{path}"


def local_server_root(connection: EndpointConnectionInput) -> str:
    """Resolve the first-party server root from an OpenAI-compatible /v1 base URL."""
    value = str(connection.base_url).rstrip("/")
    return value[:-3] if value.endswith("/v1") else value


async def probe_endpoint_connection(connection: EndpointConnectionInput) -> EndpointProbeReadModel:
    """Discover models/capabilities without letting the browser call the runtime directly."""
    profile = EndpointProfile(
        profile_id="session-probe",
        base_url=connection.base_url,
        timeout_seconds=connection.timeout_seconds,
    )
    adapter = OpenAICompatibleAdapter(profile)
    try:
        passive = await adapter.probe()
    finally:
        await adapter.aclose()

    capabilities = _capability_evidence(passive.capabilities, healthy=passive.healthy)
    runtime_parameters: dict[str, tuple[RuntimeParameterReadModel, ...]] = {}
    warning: str | None = None
    if passive.healthy and connection.server_type == "local_llm_server":
        runtime_parameters, warning = await _probe_local_llm_server_registry(connection)

    models = tuple(
        DiscoveredModelReadModel(
            model_id=model_id,
            runtime_parameters=runtime_parameters.get(model_id, ()),
        )
        for model_id in passive.models
    )
    error_code = passive.metadata.get("error_code")
    if not passive.healthy and isinstance(error_code, str):
        warning = f"Endpoint probe failed: {error_code}"

    return EndpointProbeReadModel(
        healthy=passive.healthy,
        endpoint_identity=endpoint_identity(connection),
        models=models,
        capabilities=capabilities,
        supported_generation_parameters=tuple(
            sorted(passive.capabilities.supported_generation_parameters)
        ),
        warning=warning,
    )


def _capability_evidence(
    capabilities: AdapterCapabilities,
    *,
    healthy: bool,
) -> tuple[CapabilitySupportReadModel, ...]:
    values: list[CapabilitySupportReadModel] = [
        CapabilitySupportReadModel(
            name="model_discovery",
            state="supported" if healthy else "unknown",
            source="observed" if healthy else "none",
            detail="GET /v1/models responded successfully" if healthy else None,
        )
    ]
    for name, value in (
        ("streaming", capabilities.streaming),
        ("token_usage", capabilities.token_usage),
        ("seed", capabilities.seed),
        ("structured_output", capabilities.structured_output),
    ):
        state = "supported" if value is True else "unsupported" if value is False else "unknown"
        values.append(
            CapabilitySupportReadModel(
                name=name,
                state=state,
                source="declared" if value is not None else "none",
            )
        )
    return tuple(values)


async def _probe_local_llm_server_registry(
    connection: EndpointConnectionInput,
) -> tuple[dict[str, tuple[RuntimeParameterReadModel, ...]], str | None]:
    """Best-effort first-party enrichment; generic OpenAI discovery stays authoritative."""
    url = f"{local_server_root(connection)}/api/v1/models/registry"
    try:
        async with httpx.AsyncClient(timeout=connection.timeout_seconds) as client:
            response = await client.get(url)
        response.raise_for_status()
        payload = response.json()
    except (httpx.HTTPError, ValueError, TypeError):
        return {}, "Model discovery succeeded, but Local LLM Server runtime details are unavailable."

    if not isinstance(payload, Mapping):
        return {}, "Local LLM Server returned an invalid runtime registry response."
    raw_models = payload.get("models")
    if not isinstance(raw_models, list):
        return {}, "Local LLM Server runtime registry did not include a model list."

    result: dict[str, tuple[RuntimeParameterReadModel, ...]] = {}
    for raw_model in raw_models:
        if not isinstance(raw_model, Mapping):
            continue
        model_id = _model_id(raw_model)
        if model_id is None:
            continue
        raw_capabilities = raw_model.get("config_capabilities")
        runtime_config = raw_model.get("runtime_config")
        config = runtime_config if isinstance(runtime_config, Mapping) else {}
        names = raw_capabilities if isinstance(raw_capabilities, list) else []
        parameters = tuple(
            RuntimeParameterReadModel(
                name=name,
                current_value=config.get(name),
            )
            for name in names
            if isinstance(name, str) and name
        )
        result[model_id] = parameters
    return result, None


def _model_id(raw_model: Mapping[object, object]) -> str | None:
    for key in ("model_id", "id", "key"):
        value = raw_model.get(key)
        if isinstance(value, str) and value:
            return value
    return None
