from datetime import UTC, datetime
from pathlib import Path

import pytest

from performance_lab.domain import (
    Campaign,
    CampaignEntry,
    CampaignEntryStatus,
    CampaignStatus,
    DecisionPolicyRef,
)
from performance_lab.storage import ImmutableCampaignConflictError, SQLiteCampaignStore


def _campaign(*, status: CampaignStatus = CampaignStatus.QUEUED) -> Campaign:
    now = datetime.now(UTC)
    terminal = status in {
        CampaignStatus.SUCCEEDED,
        CampaignStatus.FAILED,
        CampaignStatus.CANCELLED,
        CampaignStatus.INTERRUPTED,
    }
    entry_status = (
        CampaignEntryStatus.SUCCEEDED if status == CampaignStatus.SUCCEEDED else CampaignEntryStatus.QUEUED
    )
    return Campaign(
        campaign_id="campaign-a",
        plan_digest="a" * 64,
        use_case_id="general-capability",
        use_case_version="1",
        target_id="target-a",
        suite_id="general-diagnostic-starter",
        suite_version="2026-08-15-v1",
        decision_policy=DecisionPolicyRef(
            policy_id="strict-quality-dominance",
            policy_version="1.0.0",
        ),
        status=status,
        created_at=now,
        updated_at=now,
        completed_at=now if terminal else None,
        entries=(
            CampaignEntry(
                entry_id="entry-1",
                candidate_id="candidate-a",
                model_id="model-a",
                config_digest="b" * 64,
                status=entry_status,
                run_id="run-a" if entry_status == CampaignEntryStatus.SUCCEEDED else None,
            ),
        ),
        error_code="failed" if status == CampaignStatus.FAILED else None,
        error_message="failed" if status == CampaignStatus.FAILED else None,
    )


def test_campaign_store_persists_mutable_progress_then_freezes_terminal_snapshot(tmp_path: Path) -> None:
    store = SQLiteCampaignStore(tmp_path / "runs.sqlite3")
    queued = _campaign()
    store.save(queued)

    running = Campaign.model_validate(
        {
            **queued.model_dump(mode="python"),
            "status": CampaignStatus.RUNNING,
            "revision": 1,
        }
    )
    store.save(running)
    assert store.get("campaign-a").status == CampaignStatus.RUNNING

    completed = _campaign(status=CampaignStatus.SUCCEEDED)
    store.save(completed)
    store.save(completed)

    changed = Campaign.model_validate(
        {
            **completed.model_dump(mode="python"),
            "revision": 2,
        }
    )
    with pytest.raises(ImmutableCampaignConflictError):
        store.save(changed)
