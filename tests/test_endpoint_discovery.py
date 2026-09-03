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
from performance_lab.domain import EndpointProfile, Target
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


def test_configured_target_probe_discovers_models_through_owned_endpoint_profile(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path,
) -> None:
    endpoint = EndpointProfile(
        profile_id="configured-profile",
        base_url="http://127.0.0.1:1235/v1/",
        timeout_seconds=7,
    )
    target = Target(
        target_id="configured-target",
        display_name="Configured local runtime",
        adapter_type="openai-compatible",
        endpoint_profile_id=endpoint.profile_id,
        endpoint_identity="127.0.0.1:1235/v1/",
    )

    async def fake_profile_probe(
        profile: EndpointProfile,
        *,
        endpoint_identity_value: str,
    ) -> EndpointProbeReadModel:
        assert profile == endpoint
        assert endpoint_identity_value == target.endpoint_identity
        return EndpointProbeReadModel(
            healthy=True,
            endpoint_identity=endpoint_identity_value,
            models=(
                DiscoveredModelReadModel(model_id="nvidia/nemotron-3-nano-4b"),
                DiscoveredModelReadModel(model_id="model-b"),
            ),
            supported_generation_parameters=("temperature", "top_p"),
        )

    monkeypatch.setattr("performance_lab.ui_api.probe_endpoint_profile", fake_profile_probe)
    queries = UIQueryService(
        SQLiteRunStore(tmp_path / "runs.sqlite3"),
        targets=(target,),
        endpoint_profiles=(endpoint,),
    )
    client = TestClient(create_ui_app(queries))

    response = client.post("/api/v1/targets/configured-target/probe")

    assert response.status_code == 200
    payload = response.json()
    assert payload["target"]["target_id"] == "configured-target"
    assert payload["models"][0]["model_id"] == "nvidia/nemotron-3-nano-4b"
    assert payload["endpoint_identity"] == "127.0.0.1:1235/v1/"

    planning = client.get("/api/v1/campaign-planning")
    assert planning.status_code == 200
    planned_target = planning.json()["targets"][0]
    assert [candidate["model_id"] for candidate in planned_target["candidates"]] == [
        "model-b",
        "nvidia/nemotron-3-nano-4b",
    ]
    assert planned_target["supported_generation_parameters"] == ["temperature", "top_p"]


def test_unhealthy_configured_probe_preserves_last_successful_candidate_inventory(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path,
) -> None:
    endpoint = EndpointProfile(
        profile_id="configured-profile",
        base_url="http://127.0.0.1:1235/v1/",
    )
    target = Target(
        target_id="configured-target",
        display_name="Configured local runtime",
        adapter_type="openai-compatible",
        endpoint_profile_id=endpoint.profile_id,
        endpoint_identity="127.0.0.1:1235/v1/",
    )
    probe_count = 0

    async def fake_profile_probe(
        profile: EndpointProfile,
        *,
        endpoint_identity_value: str,
    ) -> EndpointProbeReadModel:
        nonlocal probe_count
        probe_count += 1
        if probe_count == 1:
            return EndpointProbeReadModel(
                healthy=True,
                endpoint_identity=endpoint_identity_value,
                models=(
                    DiscoveredModelReadModel(model_id="model-a"),
                    DiscoveredModelReadModel(model_id="model-b"),
                ),
                supported_generation_parameters=("temperature",),
            )
        return EndpointProbeReadModel(
            healthy=False,
            endpoint_identity=endpoint_identity_value,
            models=(),
            supported_generation_parameters=(),
        )

    monkeypatch.setattr("performance_lab.ui_api.probe_endpoint_profile", fake_profile_probe)
    queries = UIQueryService(
        SQLiteRunStore(tmp_path / "runs.sqlite3"),
        targets=(target,),
        endpoint_profiles=(endpoint,),
    )
    client = TestClient(create_ui_app(queries))

    first = client.post("/api/v1/targets/configured-target/probe")
    second = client.post("/api/v1/targets/configured-target/probe")

    assert first.json()["healthy"] is True
    assert second.json()["healthy"] is False
    planned_target = client.get("/api/v1/campaign-planning").json()["targets"][0]
    assert [candidate["model_id"] for candidate in planned_target["candidates"]] == [
        "model-a",
        "model-b",
    ]
    assert planned_target["supported_generation_parameters"] == ["temperature"]


def test_configured_target_probe_rejects_unknown_target(tmp_path) -> None:
    queries = UIQueryService(SQLiteRunStore(tmp_path / "runs.sqlite3"))
    client = TestClient(create_ui_app(queries))

    response = client.post("/api/v1/targets/missing/probe")

    assert response.status_code == 404
    assert response.json()["detail"] == "target endpoint not found"


def test_ui_discovery_rejects_non_loopback_targets() -> None:
    with pytest.raises(ValidationError, match=r"loopback|localhost"):
        EndpointConnectionInput(base_url="http://example.com/v1/")
