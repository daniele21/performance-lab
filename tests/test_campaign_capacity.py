from pathlib import Path

from performance_lab.application import (
    CampaignPlanPreviewRequest,
    DiscoveredModelReadModel,
    UIQueryService,
)
from performance_lab.application.campaign_jobs import MAX_CAMPAIGN_RUNS
from performance_lab.application.planning_queries import _campaign_capacity_issue
from performance_lab.datasets import build_general_starter_suite
from performance_lab.domain import EndpointProfile, Target
from performance_lab.run_config import StarterRunConfig
from performance_lab.storage import SQLiteRunStore


def _queries(tmp_path: Path) -> UIQueryService:
    starter = build_general_starter_suite()
    endpoint = EndpointProfile(
        profile_id="local-openai",
        base_url="http://127.0.0.1:1234/v1",
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
    )
    return UIQueryService(
        SQLiteRunStore(config.store_path),
        targets=(target,),
        endpoint_profiles=(endpoint,),
        suites=(starter.suite,),
        dataset_snapshots=tuple(dataset.snapshot for dataset in starter.datasets.values()),
        starter_run_template=config,
    )


def test_campaign_capacity_guard_blocks_only_oversized_matrices() -> None:
    assert _campaign_capacity_issue(MAX_CAMPAIGN_RUNS) is None

    issue = _campaign_capacity_issue(MAX_CAMPAIGN_RUNS + 1)

    assert issue is not None
    assert issue.code == "campaign_run_capacity_exceeded"
    assert str(MAX_CAMPAIGN_RUNS + 1) in issue.message
    assert str(MAX_CAMPAIGN_RUNS) in issue.message


def test_plan_preview_blocks_oversized_candidate_configuration_matrix(tmp_path: Path) -> None:
    queries = _queries(tmp_path)
    queries.register_target_probe_result(
        "local-target",
        discovered_models=tuple(
            DiscoveredModelReadModel(model_id=f"model-{index:02d}")
            for index in range(MAX_CAMPAIGN_RUNS)
        ),
    )
    target = queries.campaign_planning_context().targets[0]
    assert len(target.candidates) == MAX_CAMPAIGN_RUNS + 1

    preview = queries.preview_campaign_plan(
        CampaignPlanPreviewRequest(
            use_case_id="general-capability",
            target_id="local-target",
            candidate_ids=tuple(candidate.candidate_id for candidate in target.candidates),
        )
    )

    assert not preview.can_plan
    assert not preview.execution_available
    assert preview.estimate is not None
    assert preview.estimate.planned_run_count == MAX_CAMPAIGN_RUNS + 1
    assert preview.plan_digest is not None
    assert len(preview.issues) == 1
    assert preview.issues[0].code == "campaign_run_capacity_exceeded"
    assert preview.execution_blocked_reason == preview.issues[0].message
