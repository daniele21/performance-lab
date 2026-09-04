from datetime import UTC, datetime

import pytest
from pydantic import ValidationError

from performance_lab.domain import Campaign, CampaignEntry, DecisionPolicyRef


def _campaign(entries: tuple[CampaignEntry, ...]) -> Campaign:
    now = datetime.now(UTC)
    return Campaign(
        campaign_id="campaign-configurations",
        plan_digest="a" * 64,
        use_case_id="general-capability",
        use_case_version="1",
        target_id="target-a",
        suite_id="general-diagnostic-starter",
        suite_version="1",
        decision_policy=DecisionPolicyRef(
            policy_id="strict-quality-dominance",
            policy_version="1.0.0",
        ),
        created_at=now,
        updated_at=now,
        entries=entries,
    )


def test_campaign_entry_defaults_to_the_fixed_configuration_identity() -> None:
    entry = CampaignEntry(
        entry_id="entry-a",
        candidate_id="candidate-a",
        model_id="model-a",
        config_digest="b" * 64,
    )

    assert entry.configuration_id == "fixed-1"


def test_campaign_allows_one_candidate_with_multiple_configuration_identities() -> None:
    campaign = _campaign(
        (
            CampaignEntry(
                entry_id="entry-a",
                candidate_id="candidate-a",
                configuration_id="config-1",
                model_id="model-a",
                config_digest="b" * 64,
            ),
            CampaignEntry(
                entry_id="entry-b",
                candidate_id="candidate-a",
                configuration_id="config-2",
                model_id="model-a",
                config_digest="c" * 64,
            ),
        )
    )

    assert [entry.configuration_id for entry in campaign.entries] == ["config-1", "config-2"]


def test_campaign_rejects_duplicate_candidate_configuration_pair() -> None:
    with pytest.raises(ValidationError, match="candidate/configuration pairs must be unique"):
        _campaign(
            (
                CampaignEntry(
                    entry_id="entry-a",
                    candidate_id="candidate-a",
                    configuration_id="config-1",
                    model_id="model-a",
                    config_digest="b" * 64,
                ),
                CampaignEntry(
                    entry_id="entry-b",
                    candidate_id="candidate-a",
                    configuration_id="config-1",
                    model_id="model-a",
                    config_digest="c" * 64,
                ),
            )
        )
