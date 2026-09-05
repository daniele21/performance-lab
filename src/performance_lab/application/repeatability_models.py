"""Stable browser projection for exact-fingerprint repeatability evidence."""

from __future__ import annotations

from enum import StrEnum

from pydantic import Field, field_validator

from performance_lab.domain import LoadProfile

from .ui_models import MetricDimension, UIModel


class RepeatabilityState(StrEnum):
    AVAILABLE = "available"
    INSUFFICIENT_REPEATS = "insufficient_repeats"
    UNAVAILABLE = "unavailable"


class RepeatabilityPercentileReadModel(UIModel):
    percentile: int = Field(gt=0, lt=100)
    value: float | None = None
    sample_count: int = Field(ge=0)
    qualified: bool
    qualification: str | None = None


class RepeatabilityDistributionReadModel(UIModel):
    sample_count: int = Field(gt=0)
    minimum: float
    maximum: float
    mean: float
    median: float
    stddev: float
    coefficient_of_variation: float | None = None
    p90: RepeatabilityPercentileReadModel
    p95: RepeatabilityPercentileReadModel


class RepeatabilityRunValueReadModel(UIModel):
    run_id: str = Field(min_length=1)
    value: float
    source_sample_count: int | None = Field(default=None, gt=0)


class RepeatabilityMetricReadModel(UIModel):
    metric_id: str = Field(min_length=1)
    label: str = Field(min_length=1)
    dimension: MetricDimension
    unit: str | None = None
    higher_is_better: bool | None = None
    run_values: tuple[RepeatabilityRunValueReadModel, ...]
    distribution: RepeatabilityDistributionReadModel

    @field_validator("dimension")
    @classmethod
    def quality_or_performance_only(cls, value: MetricDimension) -> MetricDimension:
        if value == MetricDimension.RESOURCES:
            raise ValueError("repeatability metrics currently support quality or performance only")
        return value


class RepeatabilityReadModel(UIModel):
    anchor_run_id: str = Field(min_length=1)
    fingerprint_id: str = Field(min_length=1)
    state: RepeatabilityState
    load_profile: LoadProfile
    run_ids: tuple[str, ...]
    run_count: int = Field(gt=0)
    succeeded_run_count: int = Field(ge=0)
    failed_run_count: int = Field(ge=0)
    cancelled_run_count: int = Field(ge=0)
    sample_attempt_count: int = Field(ge=0)
    succeeded_sample_count: int = Field(ge=0)
    failed_sample_count: int = Field(ge=0)
    cancelled_sample_count: int = Field(ge=0)
    metrics: tuple[RepeatabilityMetricReadModel, ...] = ()
    note: str = Field(min_length=1)
