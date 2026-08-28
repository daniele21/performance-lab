import asyncio

import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError

from performance_lab.application import (
    DiscoveredModelReadModel,
    EndpointConnectionInput,
    EndpointProbeReadModel,
    UIQueryService,
    probe_endpoint_connection,
)
from performance_lab.plugins import AdapterCapabilities, ProbeResult
from performance_lab.storage import SQLiteRunStore
from performance_lab.ui_api import create_ui_app


class _FakeAdapter:
    def __init__(self, profile) -> None:
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


def test_generic_probe_discovers_models_and_adapter_controls(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
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


def test_endpoint_probe_api_registers_discovered_session_target(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path,
) -> None:
    async def fake_probe(connection: EndpointConnectionInput) -> EndpointProbeReadModel:
        return EndpointProbeReadModel(
            healthy=True,
            endpoint_identity="127.0.0.1:1235/v1/",
            models=(DiscoveredModelReadModel(model_id="model-a"),),
            supported_generation_parameters=("temperature",),
        )

    monkeypatch.setattr("performance_lab.ui_api.probe_endpoint_connection", fake_probe)
    queries = UIQueryService(SQLiteRunStore(tmp_path / "runs.sqlite3"))
    client = TestClient(create_ui_app(queries))

    response = client.post(
        "/api/v1/endpoint-probes",
        json={
            "display_name": "Local LLM Server",
            "base_url": "http://127.0.0.1:1235/v1/",
            "server_type": "local_llm_server",
            "timeout_seconds": 5,
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["models"][0]["model_id"] == "model-a"
    assert payload["target"]["target_id"].startswith("session-")
    targets = client.get("/api/v1/targets").json()
    assert targets[0]["target_id"] == payload["target"]["target_id"]


def test_ui_discovery_rejects_non_loopback_targets() -> None:
    with pytest.raises(ValidationError, match=r"loopback|localhost"):
        EndpointConnectionInput(base_url="http://example.com/v1/")
