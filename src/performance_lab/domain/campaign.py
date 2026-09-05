"""Durable campaign identity and lifecycle contracts.

A Campaign groups immutable Run evidence. It never replaces Run identity and it does not own
model/runtime loading. Mutable campaign progress is allowed until a terminal campaign snapshot is
published by the campaign store.
"""

from __future__ import annotations

from datetime import datetime
from enum import StrEnum

from pydantic import Field, field_validator, model_validator

from .schemas import FrozenModel, NonEmptyStr, VersionedModel


class CampaignStatus(StrEnum):
    QUEUED = "queued"
    RUNNING = "running"
    CANCELLING = "cancelling"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    CANCELLED = "cancelled"
    INTERRUPTED = "interrupted"


class CampaignEntryStatus(StrEnum):
    QUEUED = "queued"
    RUNNING = "running"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    CANCELLED = "cancelled"
    INTERRUPTED = "interrupted"


TERMINAL_CAMPAIGN_STATUSES = frozenset(
    {
        CampaignStatus.SUCCEEDED,
        CampaignStatus.FAILED,
        CampaignStatus.CANCELLED,
        CampaignStatus.INTERRUPTED,
    }
)

TERMINAL_CAMPAIGN_ENTRY_STATUSES = frozenset(
    {
        CampaignEntryStatus.SUCCEEDED,
        CampaignEntryStatus.FAILED,
        CampaignEntryStatus.CANCELLED,
        CampaignEntryStatus.INTERRUPTED,
    }
)


class DecisionPolicyRef(FrozenModel):
    policy_id: NonEmptyStr
    policy_version: NonEmptyStr


class CampaignEntry(VersionedModel):
    entry_id: NonEmptyStr
    candidate_id: NonEmptyStr
    configuration_id: NonEmptyStr = "fixed-1"
    model_id: NonEmptyStr
    config_digest: str = Field(pattern=r"^[0-9a-f]{64}$")
    status: CampaignEntryStatus = CampaignEntryStatus.QUEUED
    run_id: NonEmptyStr | None = None
    completed_samples: int = Field(default=0, ge=0)
    total_samples: int = Field(default=0, ge=0)
    error_code: NonEmptyStr | None = None
    error_message: NonEmptyStr | None = None

    @model_validator(mode="after")
    def validate_failure_shape(self) -> CampaignEntry:
        if self.status in {CampaignEntryStatus.FAILED, CampaignEntryStatus.INTERRUPTED}:
            if self.error_code is None or self.error_message is None:
                raise ValueError("failed/interrupted campaign entries require an error")
        elif self.error_code is not None or self.error_message is not None:
            raise ValueError("only failed/interrupted campaign entries may carry an error")
        return self


class Campaign(VersionedModel):
    campaign_id: NonEmptyStr
    plan_digest: str = Field(pattern=r"^[0-9a-f]{64}$")
    use_case_id: NonEmptyStr
    use_case_version: NonEmptyStr
    target_id: NonEmptyStr
    suite_id: NonEmptyStr
    suite_version: NonEmptyStr
    decision_policy: DecisionPolicyRef
    status: CampaignStatus = CampaignStatus.QUEUED
    revision: int = Field(default=0, ge=0)
    created_at: datetime
    updated_at: datetime
    completed_at: datetime | None = None
    entries: tuple[CampaignEntry, ...]
    error_code: NonEmptyStr | None = None
    error_message: NonEmptyStr | None = None

    @field_validator("created_at", "updated_at", "completed_at")
    @classmethod
    def require_timezone(cls, value: datetime | None) -> datetime | None:
        if value is not None and value.tzinfo is None:
            raise ValueError("campaign timestamps must be timezone-aware")
        return value

    @field_validator("entries")
    @classmethod
    def require_unique_entries(cls, value: tuple[CampaignEntry, ...]) -> tuple[CampaignEntry, ...]:
        if not value:
            raise ValueError("campaign requires at least one entry")
        entry_ids = [entry.entry_id for entry in value]
        candidate_configurations = [(entry.candidate_id, entry.configuration_id) for entry in value]
        if len(entry_ids) != len(set(entry_ids)):
            raise ValueError("campaign entry ids must be unique")
        if len(candidate_configurations) != len(set(candidate_configurations)):
            raise ValueError("campaign candidate/configuration pairs must be unique")
        return value

    @model_validator(mode="after")
    def validate_lifecycle(self) -> Campaign:
        if self.updated_at < self.created_at:
            raise ValueError("updated_at cannot precede created_at")
        terminal = self.status in TERMINAL_CAMPAIGN_STATUSES
        if terminal and self.completed_at is None:
            raise ValueError("terminal campaigns require completed_at")
        if not terminal and self.completed_at is not None:
            raise ValueError("non-terminal campaigns cannot have completed_at")
        if self.completed_at is not None and self.completed_at < self.created_at:
            raise ValueError("completed_at cannot precede created_at")
        if self.status in {CampaignStatus.FAILED, CampaignStatus.INTERRUPTED}:
            if self.error_code is None or self.error_message is None:
                raise ValueError("failed/interrupted campaigns require an error")
        elif self.error_code is not None or self.error_message is not None:
            raise ValueError("only failed/interrupted campaigns may carry an error")
        return self
