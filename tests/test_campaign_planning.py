from pathlib import Path

import pytest

from performance_lab.application import (
    CampaignPlanDigestMismatchError,
    CampaignPlanPreviewRequest,
    CampaignSearchStrategy,
    DiscoveredModelReadModel,
    EndpointConnectionInput,
    UIQueryService,
)
from performance_lab.datasets import build_general_starter_suite, build_workload_pack
from performance_lab.domain import EndpointProfile, EvidenceMode, HardwareIdentity, Target
from performance_lab.run_config import (
    LocalLLMServerIdentityConfig,
    LocalLLMServerTelemetryConfig,
    StarterRunConfig,
)
from performance_lab.storage import SQLiteRunStore


def _queries(tmp_path: Path) -> UIQueryService:
    starter = build_general_starter_suite()
    workload = build_workload_pack("structured-document-extraction")
    endpoint = EndpointProfile(
        profile_id="local-openai",
        base_url="http://127.0.0.1:1234/v1",
        timeout_seconds=30,
    )
    target = Target(
        target_id="local-target",
        display_name="Local target",
        adapter_type="openai-compatible",
        endpoint_profile_id=endpoint.profile_id,
        endpoint_identity="loopback:1234",
    )
    config = StarterRunConfig(
        target_id=target.target_id,
        endpoint_identity=target.endpoint_identity,
        endpoint=endpoint,
        model_id="configured-model",
        store_path=tmp_path / "runs.sqlite3",
        hardware=HardwareIdentity(device_id="device-a", device_class="laptop"),
        local_llm_server_identity=LocalLLMServerIdentityConfig(
            base_url="http://127.0.0.1:1234",
            model_id="configured-model",
            timeout_seconds=7,
            required=True,
        ),
        local_llm_server_telemetry=LocalLLMServerTelemetryConfig(
            base_url="http://127.0.0.1:1234",
            model_id="configured-model",
            sample_interval_seconds=0.1,
            timeout_seconds=8,
        ),
    )
    return UIQueryService(
        SQLiteRunStore(config.store_path),
        targets=(target,),
        endpoint_profiles=(endpoint,),
        suites=(starter.suite,),
        dataset_snapshots=tuple(dataset.snapshot for dataset in starter.datasets.values()),
        inspectable_datasets=tuple(starter.datasets.values()),
        evaluators=tuple(starter.evaluators.values()),
        starter_run_template=config,
        workload_packs=(workload,),
    )


def test_planning_context_uses_starter_and_versioned_workload_packs(tmp_path: Path) -> None:
    context = _queries(tmp_path).campaign_planning_context()

    assert [item.use_case_id for item in context.use_cases] == [
        "general-capability",
        "structured-document-extraction",
    ]
    target = context.targets[0]
    assert target.target.target_id == "local-target"
    assert target.hardware_device_id == "device-a"
    assert target.hardware_device_class == "laptop"
    assert [candidate.model_id for candidate in target.candidates] == ["configured-model"]
    assert target.candidates[0].quantization is None
    assert target.candidates[0].source == "configured"
    assert target.bounded_generation_parameter_ranges == ()
    assert target.configuration_search_options[0].strategy == CampaignSearchStrategy.FIXED
    assert target.configuration_search_options[0].available
    assert all(not option.available for option in target.configuration_search_options[1:])


def test_fixed_general_plan_is_frozen_deterministic_and_executable(tmp_path: Path) -> None:
    queries = _queries(tmp_path)
    target = queries.campaign_planning_context().targets[0]
    candidate_id = target.candidates[0].candidate_id
    request = CampaignPlanPreviewRequest(
        use_case_id="general-capability",
        target_id=target.target.target_id,
        candidate_ids=(candidate_id,),
        configuration_strategy=CampaignSearchStrategy.FIXED,
    )

    first = queries.preview_campaign_plan(request)
    second = queries.preview_campaign_plan(request)

    assert first.can_plan
    assert first.plan_digest == second.plan_digest
    assert first.plan_digest is not None
    assert first.execution_available
    assert first.execution_blocked_reason is None
    assert first.decision_policy is not None
    assert first.decision_policy.policy_id == "strict-quality-dominance"
    assert first.configuration_search is not None
    assert first.configuration_search.configuration_count_per_candidate == 1
    assert first.configuration_search.bounded_parameter_ranges == ()
    assert len(first.configuration_search.configurations) == 1
    frozen = first.configuration_search.configurations[0]
    assert frozen.configuration_id == "fixed-1"
    assert len(frozen.generation_digest) == 64
    assert frozen.generation == first.configuration_search.base_generation
    assert second.configuration_search is not None
    assert second.configuration_search.configurations == first.configuration_search.configurations
    assert first.benchmark_plan is not None
    assert first.benchmark_plan.suite.suite_id == "general-diagnostic-starter"
    assert first.benchmark_plan.case_count_per_run == 23
    assert first.estimate is not None
    assert first.estimate.planned_run_count == 1
    assert first.estimate.estimated_request_count == 23
    assert first.estimate.estimated_duration_seconds is None

    launch = queries.prepare_campaign_launch(request, expected_plan_digest=first.plan_digest)
    assert launch.plan_digest == first.plan_digest
    assert launch.decision_policy.policy_id == "strict-quality-dominance"
    assert len(launch.runs) == 1
    assert launch.runs[0].configuration_id == frozen.configuration_id
    assert launch.runs[0].config.generation == frozen.generation
    assert launch.runs[0].config.suite_id == "general-diagnostic-starter"
    assert launch.runs[0].config.suite_version == first.benchmark_plan.suite.suite_version
    assert launch.runs[0].config.evidence_mode == EvidenceMode.AGGREGATE_SAFE


def test_launch_revalidates_the_exact_reviewed_digest(tmp_path: Path) -> None:
    queries = _queries(tmp_path)
    target = queries.campaign_planning_context().targets[0]
    request = CampaignPlanPreviewRequest(
        use_case_id="general-capability",
        target_id=target.target.target_id,
        candidate_ids=(target.candidates[0].candidate_id,),
    )

    with pytest.raises(CampaignPlanDigestMismatchError):
        queries.prepare_campaign_launch(request, expected_plan_digest="0" * 64)


def test_workload_use_case_maps_to_its_own_versioned_executable_plan(tmp_path: Path) -> None:
    queries = _queries(tmp_path)
    target = queries.campaign_planning_context().targets[0]
    request = CampaignPlanPreviewRequest(
        use_case_id="structured-document-extraction",
        target_id=target.target.target_id,
        candidate_ids=(target.candidates[0].candidate_id,),
    )

    preview = queries.preview_campaign_plan(request)

    assert preview.can_plan
    assert preview.use_case is not None
    assert preview.use_case.source == "workload_pack"
    assert preview.configuration_search is not None
    assert len(preview.configuration_search.configurations) == 1
    assert preview.benchmark_plan is not None
    assert preview.benchmark_plan.suite.suite_id == "workload-structured-document-extraction"
    assert preview.benchmark_plan.case_count_per_run == 12
    assert preview.estimate is not None
    assert preview.estimate.estimated_request_count == 12
    assert preview.plan_digest is not None

    launch = queries.prepare_campaign_launch(request, expected_plan_digest=preview.plan_digest)
    assert launch.runs[0].configuration_id == "fixed-1"
    assert (
        launch.runs[0].config.generation
        == preview.configuration_search.configurations[0].generation
    )
    assert launch.runs[0].config.suite_id == "workload-structured-document-extraction"
    assert launch.runs[0].config.suite_version == preview.benchmark_plan.suite.suite_version
    assert launch.runs[0].config.evidence_mode == EvidenceMode.AGGREGATE_SAFE


def test_sweep_strategy_is_blocked_without_backend_owned_bounded_ranges(tmp_path: Path) -> None:
    queries = _queries(tmp_path)
    target = queries.campaign_planning_context().targets[0]

    preview = queries.preview_campaign_plan(
        CampaignPlanPreviewRequest(
            use_case_id="general-capability",
            target_id=target.target.target_id,
            candidate_ids=(target.candidates[0].candidate_id,),
            configuration_strategy=CampaignSearchStrategy.QUICK,
        )
    )

    assert not preview.can_plan
    assert not preview.execution_available
    assert preview.issues[0].code == "configuration_strategy_unavailable"
    assert "will not invent sweep domains" in preview.issues[0].message


def test_session_discovery_becomes_candidate_inventory_without_invented_ranges(
    tmp_path: Path,
) -> None:
    queries = _queries(tmp_path)
    target = queries.register_session_connection(
        EndpointConnectionInput(
            display_name="Discovered server",
            base_url="http://127.0.0.1:1235/v1",
            server_type="openai_compatible",
        ),
        discovered_models=(
            DiscoveredModelReadModel(model_id="model-a"),
            DiscoveredModelReadModel(model_id="model-b"),
        ),
        supported_generation_parameters=("temperature", "top_p", "temperature"),
    )

    context = queries.campaign_planning_context()
    session = next(item for item in context.targets if item.target.target_id == target.target_id)

    assert [candidate.model_id for candidate in session.candidates] == ["model-a", "model-b"]
    assert all(candidate.source == "discovered" for candidate in session.candidates)
    assert session.supported_generation_parameters == ("temperature", "top_p")
    assert session.bounded_generation_parameter_ranges == ()
    quick = next(
        option
        for option in session.configuration_search_options
        if option.strategy == CampaignSearchStrategy.QUICK
    )
    assert not quick.available
    assert quick.blocked_reason is not None


def test_configured_target_discovery_plans_multiple_models_with_candidate_bound_evidence(
    tmp_path: Path,
) -> None:
    queries = _queries(tmp_path)
    queries.register_target_probe_result(
        "local-target",
        discovered_models=(
            DiscoveredModelReadModel(model_id="model-a"),
            DiscoveredModelReadModel(model_id="model-b"),
            DiscoveredModelReadModel(model_id="model-a"),
        ),
        supported_generation_parameters=("top_p", "temperature", "top_p"),
    )

    target = queries.campaign_planning_context().targets[0]
    assert [candidate.model_id for candidate in target.candidates] == [
        "configured-model",
        "model-a",
        "model-b",
    ]
    assert target.supported_generation_parameters == ("temperature", "top_p")

    selected = tuple(
        candidate.candidate_id
        for candidate in target.candidates
        if candidate.model_id in {"model-a", "model-b"}
    )
    request = CampaignPlanPreviewRequest(
        use_case_id="general-capability",
        target_id="local-target",
        candidate_ids=selected,
    )
    preview = queries.preview_campaign_plan(request)

    assert preview.can_plan
    assert preview.configuration_search is not None
    assert len(preview.configuration_search.configurations) == 1
    assert preview.estimate is not None
    assert preview.estimate.planned_run_count == 2
    assert preview.plan_digest is not None

    launch = queries.prepare_campaign_launch(request, expected_plan_digest=preview.plan_digest)
    assert [run.model_id for run in launch.runs] == ["model-a", "model-b"]
    assert all(run.configuration_id == "fixed-1" for run in launch.runs)
    for run in launch.runs:
        config = run.config
        assert config.model_id == run.model_id
        assert config.generation == preview.configuration_search.configurations[0].generation
        assert config.local_llm_server_identity is not None
        assert config.local_llm_server_identity.model_id == run.model_id
        assert config.local_llm_server_identity.required is True
        assert config.local_llm_server_identity.timeout_seconds == 7
        assert config.local_llm_server_telemetry is not None
        assert config.local_llm_server_telemetry.model_id == run.model_id
        assert config.local_llm_server_telemetry.sample_interval_seconds == 0.1
        assert config.local_llm_server_telemetry.timeout_seconds == 8
        assert config.hardware.device_id == "device-a"
