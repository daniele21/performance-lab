"""Repeatability/statistics helpers with qualified percentile availability."""

from __future__ import annotations

import math
from statistics import mean, median, pstdev

from pydantic import BaseModel, ConfigDict, Field


class StatisticsModel(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")


class PercentileEstimate(StatisticsModel):
    percentile: int = Field(gt=0, lt=100)
    value: float | None = None
    sample_count: int = Field(ge=0)
    qualified: bool
    qualification: str | None = None


class DistributionSummary(StatisticsModel):
    sample_count: int = Field(gt=0)
    minimum: float
    maximum: float
    mean: float
    median: float
    stddev: float
    coefficient_of_variation: float | None = None
    p90: PercentileEstimate
    p95: PercentileEstimate
    raw_values: tuple[float, ...]


def summarize_distribution(values: list[float] | tuple[float, ...]) -> DistributionSummary:
    """Summarize raw samples without presenting unstable percentiles as authoritative."""

    if not values:
        raise ValueError("at least one sample is required")
    raw = tuple(float(value) for value in values)
    if any(not math.isfinite(value) for value in raw):
        raise ValueError("distribution samples must be finite")
    average = mean(raw)
    deviation = pstdev(raw)
    coefficient = abs(deviation / average) if average != 0 else None
    return DistributionSummary(
        sample_count=len(raw),
        minimum=min(raw),
        maximum=max(raw),
        mean=average,
        median=median(raw),
        stddev=deviation,
        coefficient_of_variation=coefficient,
        p90=_qualified_percentile(raw, percentile=90, minimum_samples=10),
        p95=_qualified_percentile(raw, percentile=95, minimum_samples=20),
        raw_values=raw,
    )


def _qualified_percentile(
    values: tuple[float, ...], *, percentile: int, minimum_samples: int
) -> PercentileEstimate:
    sample_count = len(values)
    if sample_count < minimum_samples:
        return PercentileEstimate(
            percentile=percentile,
            sample_count=sample_count,
            qualified=False,
            qualification=(
                f"requires at least {minimum_samples} samples; only {sample_count} available"
            ),
        )
    ordered = sorted(values)
    rank = (percentile / 100) * (sample_count - 1)
    lower = math.floor(rank)
    upper = math.ceil(rank)
    if lower == upper:
        value = ordered[lower]
    else:
        weight = rank - lower
        value = ordered[lower] * (1 - weight) + ordered[upper] * weight
    return PercentileEstimate(
        percentile=percentile,
        value=value,
        sample_count=sample_count,
        qualified=True,
    )
