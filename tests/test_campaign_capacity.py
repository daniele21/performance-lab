from performance_lab.application.campaign_jobs import MAX_CAMPAIGN_RUNS
from performance_lab.application.planning_queries import _campaign_capacity_issue


def test_campaign_capacity_guard_blocks_only_oversized_matrices() -> None:
    assert _campaign_capacity_issue(MAX_CAMPAIGN_RUNS) is None

    issue = _campaign_capacity_issue(MAX_CAMPAIGN_RUNS + 1)

    assert issue is not None
    assert issue.code == "campaign_run_capacity_exceeded"
    assert str(MAX_CAMPAIGN_RUNS + 1) in issue.message
    assert str(MAX_CAMPAIGN_RUNS) in issue.message
