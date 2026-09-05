"""Browser-facing Campaign lifecycle and result projections."""

from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import Field

from performance_lab.domain import (
    CampaignEntryStatus,
    CampaignStatus,
    ComparisonDimension,
    MeasurementProvenance,
    MeasurementScope,
)

from .evidence_models import SampleEvidenceDetailReadModel
from .planning_models import DecisionPolicyReadModel
from .ui_models import BenchmarkCaseReadModel, IdentitySummary, MetricReadModel, UIModel


class CampaignCompatibilityReasonReadModel(UIModel):
    baseline_run_id: str = Field(min_length=1)
    candidate_run_id: str = Field(min_length=1)
    code: str = Field(min_length=1)
    field: str = Field(min_length=1)
    message: str = Field(min_length=1)


class CampaignDimensionReadModel(UIModel):
    dimension: ComparisonDimension
    comparable: bool
    evidence_available: bool
    evidence_note: str | None = None
    reasons: tuple[CampaignCompatibilityReasonReadModel, ...] = ()


class CampaignResourceMeasurementReadModel(UIModel):
    name: str = Field(min_length=1)
    value: float
    unit: str = Field(min_length=1)
    scope: MeasurementScope
    provenance: MeasurementProvenance
    protocol_version: str = Field(min_length=1)


class CampaignResourceEvidenceReadModel(UIModel):
    state: Literal["available", "unavailable", "not_comparable"]
    measurements: tuple[CampaignResourceMeasurementReadModel, ...] = ()
    note: str = Field(min_length=1)


class CampaignRecommendationReadModel(UIModel):
    candidate_id: str = Field(min_length=1)
    run_id: str = Field(min_length=1)
    model_id: str = Field(min_length=1)
    rationale: str = Field(min_length=1)


class CampaignResultsReadModel(UIModel):
    state: Literal["pending", "ready", "partial"]
    decision_policy: DecisionPolicyReadModel
    compatibility: tuple[CampaignDimensionReadModel, ...] = ()
    recommendation: CampaignRecommendationReadModel | None = None
    recommendation_reason: str = Field(min_length=1)


class CampaignEntryReadModel(UIModel):
    entry_id: str = Field(min_length=1)
    candidate_id: str = Field(min_length=1)
    configuration_id: str = Field(default="fixed-1", min_length=1)
    model_id: str = Field(min_length=1)
    config_digest: str = Field(pattern=r"^[0-9a-f]{64}$")
    status: CampaignEntryStatus
    run_id: str | None = None
    completed_samples: int = Field(ge=0)
    total_samples: int = Field(ge=0)
    error_code: str | None = None
    error_message: str | None = None
    identity: IdentitySummary | None = None
    metrics: tuple[MetricReadModel, ...] = ()
    resources: CampaignResourceEvidenceReadModel


class CampaignReadModel(UIModel):
    campaign_id: str = Field(min_length=1)
    plan_digest: str = Field(pattern=r"^[0-9a-f]{64}$")
    use_case_id: str = Field(min_length=1)
    use_case_version: str = Field(min_length=1)
    target_id: str = Field(min_length=1)
    suite_id: str = Field(min_length=1)
    suite_version: str = Field(min_length=1)
    status: CampaignStatus
    revision: int = Field(ge=0)
    created_at: datetime
    updated_at: datetime
    completed_at: datetime | None = None
    entries: tuple[CampaignEntryReadModel, ...]
    results: CampaignResultsReadModel
    error_code: str | None = None
    error_message: str | None = None


class CampaignCaseSummaryReadModel(UIModel):
    task_id: str = Field(min_length=1)
    sample_id: str = Field(min_length=1)
    case_id: str | None = None
    candidate_count: int = Field(gt=0)
    available_candidate_count: int = Field(ge=0)


class CampaignCaseCandidateReadModel(UIModel):
    entry_id: str = Field(min_length=1)
    candidate_id: str = Field(min_length=1)
    configuration_id: str = Field(default="fixed-1", min_length=1)
    model_id: str = Field(min_length=1)
    config_digest: str = Field(pattern=r"^[0-9a-f]{64}$")
    entry_status: CampaignEntryStatus
    run_id: str | None = None
    identity: IdentitySummary | None = None
    comparable_to_reference: bool = False
    compatibility_reasons: tuple[CampaignCompatibilityReasonReadModel, ...] = ()
    evidence: SampleEvidenceDetailReadModel | None = None
    resources: CampaignResourceEvidenceReadModel
    unavailable_reason: str | None = None


class CampaignCaseComparisonReadModel(UIModel):
    campaign_id: str = Field(min_length=1)
    suite_id: str = Field(min_length=1)
    suite_version: str = Field(min_length=1)
    task_id: str = Field(min_length=1)
    sample_id: str = Field(min_length=1)
    state: Literal["ready", "partial", "not_comparable"]
    reference_run_id: str | None = None
    benchmark_case: BenchmarkCaseReadModel | None = None
    candidates: tuple[CampaignCaseCandidateReadModel, ...]
    comparable_candidate_count: int = Field(ge=0)
    summary: str = Field(min_length=1)
