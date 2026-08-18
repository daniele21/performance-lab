"""Stable UI-shaped read models.

These models are projections for the local browser product. They deliberately reference
canonical domain/storage values instead of redefining benchmark or compatibility semantics.
"""

from __future__ import annotations

from datetime import datetime
from enum import StrEnum
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from performance_lab.domain import ComparisonDimension, ExecutionFingerprint, RunStatus
from performance_lab.storage import IdentityDifference, MetricDelta

UI_READ_MODEL_VERSION: Literal[1] = 1


class UIModel(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    api_version: Literal["v1"] = "v1"
    read_model_version: Literal[1] = UI_READ_MODEL_VERSION


class EvidenceAvailability(StrEnum):
    AVAILABLE = "available"
    UNKNOWN = "unknown"
    UNAVAILABLE = "unavailable"
    NOT_EVALUATED = "not_evaluated"


class MetricDimension(StrEnum):
    QUALITY = "quality"
    PERFORMANCE = "performance"
    RESOURCES = "resources"


class MetricReadModel(UIModel):
    metric_id: str = Field(min_length=1)
    label: str = Field(min_length=1)
    dimension: MetricDimension
    availability: EvidenceAvailability
    value: float | None = None
    unit: str | None = None
    higher_is_better: bool | None = None
    provenance: str | None = None
    protocol_version: str | None = None


class IdentitySummary(UIModel):
    model_id: str = Field(min_length=1)
    revision: str | None = None
    quantization: str | None = None
    artifact_digest: str | None = None
    target_id: str = Field(min_length=1)
    endpoint_identity: str = Field(min_length=1)
    runtime_name: str | None = None
    runtime_version: str | None = None
    hardware_device_id: str | None = None
    hardware_device_class: str | None = None


class RunSummaryReadModel(UIModel):
    run_id: str = Field(min_length=1)
    status: RunStatus
    created_at: datetime
    completed_at: datetime | None = None
    suite_id: str = Field(min_length=1)
    suite_version: str = Field(min_length=1)
    fingerprint_id: str = Field(min_length=1)
    identity: IdentitySummary
    metrics: tuple[MetricReadModel, ...] = ()


class RunEvidenceReadModel(UIModel):
    fingerprint: ExecutionFingerprint
    dataset_count: int = Field(ge=0)
    evaluator_count: int = Field(ge=0)
    sample_count: int = Field(ge=0)


class RunDetailReadModel(UIModel):
    summary: RunSummaryReadModel
    evidence: RunEvidenceReadModel


class TestedModelReadModel(UIModel):
    cohort_key: str = Field(min_length=1)
    identity: IdentitySummary
    run_count: int = Field(gt=0)
    latest_run_id: str = Field(min_length=1)
    latest_completed_at: datetime | None = None
    latest_metrics: tuple[MetricReadModel, ...] = ()


class TargetSummaryReadModel(UIModel):
    target_id: str = Field(min_length=1)
    display_name: str = Field(min_length=1)
    adapter_type: str = Field(min_length=1)
    endpoint_profile_id: str = Field(min_length=1)
    endpoint_identity: str = Field(min_length=1)
    capabilities: tuple[str, ...] = ()


class SuiteSummaryReadModel(UIModel):
    suite_id: str = Field(min_length=1)
    suite_version: str = Field(min_length=1)
    task_count: int = Field(gt=0)
    task_ids: tuple[str, ...]


class BaselineSummaryReadModel(UIModel):
    baseline_id: str = Field(min_length=1)
    run_id: str = Field(min_length=1)
    fingerprint_id: str = Field(min_length=1)
    selected_at: datetime
    label: str | None = None


class PolicySummaryReadModel(UIModel):
    policy_id: str = Field(min_length=1)
    policy_version: str = Field(min_length=1)
    rule_count: int = Field(gt=0)


class CompatibilityReasonReadModel(UIModel):
    code: str = Field(min_length=1)
    field: str = Field(min_length=1)
    message: str = Field(min_length=1)
    baseline: object | None = None
    candidate: object | None = None


class DimensionComparisonReadModel(UIModel):
    dimension: ComparisonDimension
    comparable: bool
    reasons: tuple[CompatibilityReasonReadModel, ...] = ()
    deltas: tuple[MetricDelta, ...] = ()
    missing_in_baseline: tuple[str, ...] = ()
    missing_in_candidate: tuple[str, ...] = ()


class ComparisonReadModel(UIModel):
    baseline_run_id: str = Field(min_length=1)
    candidate_run_id: str = Field(min_length=1)
    identity_differences: tuple[IdentityDifference, ...]
    dimensions: tuple[DimensionComparisonReadModel, ...]
