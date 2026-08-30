from pathlib import Path

from performance_lab.application import (
    CampaignPlanPreviewRequest,
    CampaignSearchStrategy,
    DiscoveredModelReadModel,
    EndpointConnectionInput,
    UIQueryService,
)
from performance_lab.datasets import build_general_starter_suite, build_workload_pack
from performance_lab.domain import EndpointProfile, HardwareIdentity, Target
from performance_lab.run_config import StarterRunConfig
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


def test_fixed_general_plan_is_frozen_deterministic_and_bounded(tmp_path: Path) -> None:
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
    assert not first.execution_available
    assert first.configuration_search is not None
    assert first.configuration_search.configuration_count_per_candidate == 1
    assert first.configuration_search.bounded_parameter_ranges == ()
    assert first.benchmark_plan is not None
    assert first.benchmark_plan.suite.suite_id == "general-diagnostic-starter"
    assert first.benchmark_plan.case_count_per_run == 23
    assert first.estimate is not None
    assert first.estimate.planned_run_count == 1
    assert first.estimate.estimated_request_count == 23
    assert first.estimate.estimated_duration_seconds is None


def test_workload_use_case_maps_to_its_own_versioned_benchmark_plan(tmp_path: Path) -> None:
    queries = _queries(tmp_path)
    target = queries.campaign_planning_context().targets[0]

    preview = queries.preview_campaign_plan(
        CampaignPlanPreviewRequest(
            use_case_id="structured-document-extraction",
            target_id=target.target.target_id,
            candidate_ids=(target.candidates[0].candidate_id,),
        )
    )

    assert preview.can_plan
    assert preview.use_case is not None
    assert preview.use_case.source == "workload_pack"
    assert preview.benchmark_plan is not None
    assert preview.benchmark_plan.suite.suite_id == "workload-structured-document-extraction"
    assert preview.benchmark_plan.case_count_per_run == 12
    assert preview.estimate is not None
    assert preview.estimate.estimated_request_count == 12


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
