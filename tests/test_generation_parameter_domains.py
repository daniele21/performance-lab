from __future__ import annotations

import asyncio

from performance_lab.application import (
    CampaignSearchStrategy,
    DiscoveredModelReadModel,
    EndpointConnectionInput,
    GenerationParameterDomainReadModel,
    UIQueryService,
)
from performance_lab.application.endpoint_discovery import _probe_local_llm_server_registry
from performance_lab.storage import SQLiteRunStore


class _RegistryResponse:
    def __init__(self, payload: object) -> None:
        self._payload = payload

    def raise_for_status(self) -> None:
        return None

    def json(self) -> object:
        return self._payload


class _RegistryClient:
    def __init__(self, payload: object) -> None:
        self._payload = payload

    async def __aenter__(self) -> _RegistryClient:
        return self

    async def __aexit__(self, *_args: object) -> None:
        return None

    async def get(self, _url: str) -> _RegistryResponse:
        return _RegistryResponse(self._payload)


def _patch_registry(monkeypatch, payload: object) -> None:
    monkeypatch.setattr(
        "performance_lab.application.endpoint_discovery.httpx.AsyncClient",
        lambda **_kwargs: _RegistryClient(payload),
    )


def test_local_llm_registry_preserves_declared_model_scoped_domains(monkeypatch) -> None:
    _patch_registry(
        monkeypatch,
        {
            "models": [
                {
                    "key": "demo",
                    "model_id": "org/demo",
                    "config_capabilities": ["n_batch"],
                    "runtime_config": {"n_batch": 512},
                    "generation_parameter_domains": [
                        {
                            "name": "temperature",
                            "kind": "float",
                            "minimum": 0.0,
                            "maximum": 0.8,
                            "step": 0.1,
                            "provenance": "registry_declared",
                        },
                        {
                            "name": "enable_thinking",
                            "kind": "boolean",
                            "values": [False, True],
                            "provenance": "registry_declared",
                        },
                    ],
                }
            ]
        },
    )

    runtime_parameters, domains, warning = asyncio.run(
        _probe_local_llm_server_registry(
            EndpointConnectionInput(
                base_url="http://127.0.0.1:1235/v1",
                server_type="local_llm_server",
            )
        )
    )

    assert warning is None
    assert runtime_parameters["org/demo"][0].scope == "runtime_load"
    assert runtime_parameters["org/demo"][0].name == "n_batch"
    assert [domain.name for domain in domains["org/demo"]] == [
        "enable_thinking",
        "temperature",
    ]
    temperature = domains["org/demo"][1]
    assert temperature.scope == "request_generation"
    assert temperature.source == "local_llm_server"
    assert temperature.provenance == "registry_declared"
    assert temperature.minimum == 0.0
    assert temperature.maximum == 0.8
    assert temperature.step == 0.1


def test_invalid_domain_metadata_is_ignored_without_losing_registry_model(monkeypatch) -> None:
    _patch_registry(
        monkeypatch,
        {
            "models": [
                {
                    "model_id": "org/demo",
                    "generation_parameter_domains": [
                        {
                            "name": "temperature",
                            "kind": "float",
                            "minimum": 1.0,
                            "maximum": 0.0,
                            "provenance": "registry_declared",
                        }
                    ],
                }
            ]
        },
    )

    runtime_parameters, domains, warning = asyncio.run(
        _probe_local_llm_server_registry(
            EndpointConnectionInput(
                base_url="http://127.0.0.1:1235/v1",
                server_type="local_llm_server",
            )
        )
    )

    assert runtime_parameters["org/demo"] == ()
    assert domains["org/demo"] == ()
    assert warning is not None
    assert "invalid generation-domain metadata" in warning


def test_planning_canonicalizes_searchable_domains_without_enabling_sweeps(tmp_path) -> None:
    queries = UIQueryService(SQLiteRunStore(tmp_path / "runs.sqlite3"))
    temperature = GenerationParameterDomainReadModel(
        name="temperature",
        kind="float",
        minimum=0.0,
        maximum=0.8,
        step=0.1,
    )
    max_tokens = GenerationParameterDomainReadModel(
        name="max_tokens",
        kind="integer",
        minimum=64,
        maximum=512,
        step=64,
    )
    top_k = GenerationParameterDomainReadModel(
        name="top_k",
        kind="integer",
        minimum=1,
        maximum=100,
        step=1,
    )
    discovered = DiscoveredModelReadModel(
        model_id="org/demo",
        generation_parameter_domains=(temperature, max_tokens, top_k),
    )
    assert [domain.name for domain in discovered.generation_parameter_domains] == [
        "temperature",
        "max_tokens",
        "top_k",
    ]

    target = queries.register_session_connection(
        EndpointConnectionInput(
            display_name="Declared-domain runtime",
            base_url="http://127.0.0.1:1235/v1",
            server_type="local_llm_server",
        ),
        discovered_models=(discovered,),
        supported_generation_parameters=("max_output_tokens", "temperature"),
    )

    target_context = next(
        item
        for item in queries.campaign_planning_context().targets
        if item.target.target_id == target.target_id
    )

    assert len(target_context.candidates) == 1
    candidate = target_context.candidates[0]
    assert candidate.model_id == "org/demo"
    assert [domain.name for domain in candidate.generation_parameter_domains] == [
        "max_output_tokens",
        "temperature",
    ]
    canonical_max_tokens = candidate.generation_parameter_domains[0]
    assert canonical_max_tokens.kind == "integer"
    assert canonical_max_tokens.minimum == 64
    assert canonical_max_tokens.maximum == 512
    assert canonical_max_tokens.step == 64
    assert canonical_max_tokens.source == "local_llm_server"
    assert canonical_max_tokens.provenance == "registry_declared"
    assert target_context.bounded_generation_parameter_ranges == ()
    quick = next(
        option
        for option in target_context.configuration_search_options
        if option.strategy == CampaignSearchStrategy.QUICK
    )
    assert not quick.available
    assert quick.blocked_reason is not None
