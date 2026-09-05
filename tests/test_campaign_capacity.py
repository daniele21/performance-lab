from performance_lab.application.campaign_jobs import MAX_CAMPAIGN_RUNS
from performance_lab.application.planning_queries import _campaign_capacity_issue


def test_campaign_capacity_guard_allows_single_configuration_max_candidates() -> None:
    assert _campaign_capacity_issue(MAX_CAMPAIGN_RUNS) is None


def test_campaign_capacity_guard_blocks_future_multi_configuration_matrix() -> None:
    candidate_count = (MAX_CAMPAIGN_RUNS // 2) + 1
    configuration_count = 2
    planned_run_count = candidate_count * configuration_count

    assert candidate_count <= MAX_CAMPAIGN_RUNS
    assert planned_run_count > MAX_CAMPAIGN_RUNS

    issue = _campaign_capacity_issue(planned_run_count)

    assert issue is not None
    assert issue.code == "campaign_run_capacity_exceeded"
    assert str(planned_run_count) in issue.message
    assert str(MAX_CAMPAIGN_RUNS) in issue.message
