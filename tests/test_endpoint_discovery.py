import asyncio

import pytest
from pydantic import ValidationError

from performance_lab.application import EndpointConnectionInput, probe_endpoint_connection
from performance_lab.plugins import AdapterCapabilities, ProbeResult


class _FakeAdapter:
    def __init__(self, profile) -> None:  # noqa: ANN001
        self.profile = profile

    async def probe(self) -> ProbeResult:
        return ProbeResult(
            healthy=True,
            adapter_id="openai-compatible",
            models=("model-a", "model-b"),
            capabilities=AdapterCapabilities(
                streaming=True,
                model_discovery=True,
                token_usage=None,
                seed=None,
                structured_output=None,
                supported_generation_parameters=frozenset(
                    {"max_output_tokens", "temperature", "top_p", "seed"}
                ),
            ),
        )

    async def aclose(self) -> None:
        return None


def test_generic_probe_discovers_models_and_adapter_controls(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        "performance_lab.application.endpoint_discovery.OpenAICompatibleAdapter",
        _FakeAdapter,
    )
    result = asyncio.run(
        probe_endpoint_connection(
            EndpointConnectionInput(
                base_url="http://127.0.0.1:1235/v1/",
                server_type="openai_compatible",
            )
        )
    )

    assert result.healthy
    assert [model.model_id for model in result.models] == ["model-a", "model-b"]
    assert result.supported_generation_parameters == (
        "max_output_tokens",
        "seed",
        "temperature",
        "top_p",
    )
    model_discovery = next(item for item in result.capabilities if item.name == "model_discovery")
    assert model_discovery.state == "supported"
    assert model_discovery.source == "observed"


def test_ui_discovery_rejects_non_loopback_targets() -> None:
    with pytest.raises(ValidationError, match="loopback|localhost"):
        EndpointConnectionInput(base_url="http://example.com/v1/")
