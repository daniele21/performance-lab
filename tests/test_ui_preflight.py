from pathlib import Path

from fastapi.testclient import TestClient

from performance_lab.application import (
    EndpointConnectionInput,
    RunPreflightRequest,
    ScenarioKind,
    UIQueryService,
)
from performance_lab.datasets import build_general_starter_suite
from performance_lab.domain import Capability, EndpointProfile, EvidenceMode, Target
from performance_lab.storage import SQLiteRunStore
from performance_lab.ui_api import create_ui_app


def _queries(tmp_path: Path) -> UIQueryService:
    store = SQLiteRunStore(tmp_path / "runs.sqlite3")
    bundle = build_general_starter_suite()
    endpoint = EndpointProfile(
        profile_id="local-openai",
        base_url="http://127.0.0.1:1234/v1",
        model_selector=None,
    )
    target = Target(
        target_id="local-device",
        display_name="Local device",
        adapter_type="openai-compatible",
        endpoint_profile_id=endpoint.profile_id,
        endpoint_identity="loopback:1234",
        declared_capabilities=(Capability.TEXT_GENERATION,),
    )
    snapshots = tuple(dataset.snapshot for dataset in bundle.datasets.values())
    return UIQueryService(
        store,
        targets=(target,),
        endpoint_profiles=(endpoint,),
        suites=(bundle.suite,),
        dataset_snapshots=snapshots,
    )


def test_preflight_freezes_exact_starter_execution_input(tmp_path: Path) -> None:
    queries = _queries(tmp_path)

    result = queries.preflight(
        RunPreflightRequest(
            target_id="local-device",
            model_id="model-a",
            scenario=ScenarioKind.GENERAL_CAPABILITY,
            use_host_telemetry=True,
        )
    )

    assert result.can_run
    assert result.issues == ()
    assert result.preview is not None
    assert result.preview.config.target_id == "local-device"
    assert result.preview.config.model_id == "model-a"
    assert result.preview.config.evidence_mode == EvidenceMode.EVIDENCE_RICH
    assert result.preview.config.use_host_telemetry is True
    assert result.preview.config.suite_id == "general-diagnostic-starter"
    assert len(result.preview.config_digest) == 64
    assert result.preview.load_profile.request_count > 0
    assert result.preview.identity_resolution == "resolved_at_launch"


def test_discovered_session_connection_becomes_executable_target(tmp_path: Path) -> None:
    queries = _queries(tmp_path)
    target = queries.register_session_connection(
        EndpointConnectionInput(
            display_name="Local LLM Server",
            base_url="http://127.0.0.1:1235/v1/",
            server_type="local_llm_server",
        )
    )

    result = queries.preflight(
        RunPreflightRequest(
            target_id=target.target_id,
            model_id="discovered-model",
            scenario=ScenarioKind.GENERAL_CAPABILITY,
        )
    )

    assert result.can_run
    assert result.preview is not None
    assert result.preview.target.target_id == target.target_id
    assert result.preview.config.evidence_mode == EvidenceMode.EVIDENCE_RICH
    assert str(result.preview.config.endpoint.base_url).startswith("http://127.0.0.1:1235/v1")
    assert result.preview.config.local_llm_server_identity is not None
    assert result.preview.config.local_llm_server_identity.model_id == "discovered-model"
    assert result.preview.config.local_llm_server_telemetry is None


def test_preflight_rejects_unwired_scenario_without_faking_support(tmp_path: Path) -> None:
    queries = _queries(tmp_path)

    result = queries.preflight(
        RunPreflightRequest(
            target_id="local-device",
            model_id="model-a",
            scenario=ScenarioKind.PERFORMANCE,
        )
    )

    assert not result.can_run
    assert result.preview is None
    assert result.issues[0].code == "scenario_not_supported"


def test_dataset_and_scenario_catalog_are_explicit(tmp_path: Path) -> None:
    queries = _queries(tmp_path)

    datasets = queries.list_datasets()
    scenarios = queries.list_scenarios()

    assert datasets
    assert all(dataset.sample_count > 0 for dataset in datasets)
    general = next(item for item in scenarios if item.scenario == ScenarioKind.GENERAL_CAPABILITY)
    performance = next(item for item in scenarios if item.scenario == ScenarioKind.PERFORMANCE)
    assert general.supported
    assert not performance.supported
    assert performance.blocked_reason


def test_versioned_preflight_api_returns_frozen_preview(tmp_path: Path) -> None:
    client = TestClient(create_ui_app(_queries(tmp_path)))

    response = client.post(
        "/api/v1/run-preflight",
        json={
            "target_id": "local-device",
            "model_id": "model-a",
            "scenario": "general_capability",
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["can_run"] is True
    assert payload["preview"]["config"]["model_id"] == "model-a"
    assert payload["preview"]["config"]["evidence_mode"] == "evidence_rich"
    assert payload["preview"]["config_digest"]
    assert client.get("/api/v1/datasets").json()
    scenarios = client.get("/api/v1/scenarios").json()
    assert any(
        item["scenario"] == "performance" and item["supported"] is False for item in scenarios
    )
