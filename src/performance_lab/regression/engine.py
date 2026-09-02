"""Explicit immutable baselines and compatibility-first regression comparisons."""

from __future__ import annotations

from datetime import UTC, datetime
from enum import StrEnum
from typing import Protocol

from pydantic import BaseModel, ConfigDict, Field

from performance_lab.domain import ComparisonDimension, CompatibilityResult, Run
from performance_lab.storage import IdentityDifference, MetricDelta, compare_runs


class RegressionModel(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")


class RegressionDimensionState(StrEnum):
    COMPARABLE = "comparable"
    NOT_COMPARABLE = "not_comparable"


class ThresholdState(StrEnum):
    NOT_EVALUATED = "not_evaluated"
    PASS = "pass"
    FAIL = "fail"
    NOT_COMPARABLE = "not_comparable"


class UncertaintyState(StrEnum):
    UNAVAILABLE = "unavailable"
    AVAILABLE = "available"


class BaselineBinding(RegressionModel):
    schema_version: int = 1
    baseline_id: str = Field(min_length=1)
    run_id: str = Field(min_length=1)
    fingerprint_id: str = Field(min_length=1)
    selected_at: datetime
    label: str | None = None


class RegressionMetricResult(RegressionModel):
    delta: MetricDelta
    threshold_state: ThresholdState = ThresholdState.NOT_EVALUATED
    threshold_reason: str = "no regression policy applied"
    uncertainty_state: UncertaintyState = UncertaintyState.UNAVAILABLE
    uncertainty_reason: str = "no compatible uncertainty estimate is available"


class RegressionDimensionResult(RegressionModel):
    dimension: ComparisonDimension
    state: RegressionDimensionState
    compatibility: CompatibilityResult
    metrics: tuple[RegressionMetricResult, ...] = ()
    missing_in_baseline: tuple[str, ...] = ()
    missing_in_candidate: tuple[str, ...] = ()


class RegressionComparison(RegressionModel):
    baseline: BaselineBinding
    candidate_run_id: str = Field(min_length=1)
    candidate_fingerprint_id: str = Field(min_length=1)
    identity_differences: tuple[IdentityDifference, ...]
    dimensions: tuple[RegressionDimensionResult, ...]

    def dimension(self, dimension: ComparisonDimension) -> RegressionDimensionResult:
        for result in self.dimensions:
            if result.dimension == dimension:
                return result
        raise KeyError(dimension)


class BaselineIdentityError(RuntimeError):
    pass


class CompletedRunReader(Protocol):
    def get_completed(self, run_id: str, *, required: bool = True) -> Run | None: ...


def bind_baseline(
    store: CompletedRunReader,
    *,
    baseline_id: str,
    run_id: str,
    label: str | None = None,
    selected_at: datetime | None = None,
) -> BaselineBinding:
    """Bind an explicit run as baseline without any implicit latest-run behavior."""

    run = store.get_completed(run_id)
    if run is None:
        raise LookupError(f"completed baseline run not found: {run_id}")
    return BaselineBinding(
        baseline_id=baseline_id,
        run_id=run.run_id,
        fingerprint_id=run.fingerprint.fingerprint_id,
        selected_at=selected_at or datetime.now(UTC),
        label=label,
    )


class BaselineRegressionEngine:
    def __init__(self, store: CompletedRunReader) -> None:
        self.store = store

    def compare(self, baseline: BaselineBinding, candidate_run_id: str) -> RegressionComparison:
        baseline_run = self.store.get_completed(baseline.run_id)
        candidate_run = self.store.get_completed(candidate_run_id)
        if baseline_run is None:
            raise LookupError(f"completed baseline run not found: {baseline.run_id}")
        if candidate_run is None:
            raise LookupError(f"completed candidate run not found: {candidate_run_id}")
        if baseline_run.fingerprint.fingerprint_id != baseline.fingerprint_id:
            raise BaselineIdentityError(
                "baseline binding fingerprint does not match the immutable completed run"
            )

        comparison = compare_runs(baseline_run, candidate_run)
        dimensions = tuple(_dimension_result(dimension) for dimension in comparison.dimensions)
        return RegressionComparison(
            baseline=baseline,
            candidate_run_id=candidate_run.run_id,
            candidate_fingerprint_id=candidate_run.fingerprint.fingerprint_id,
            identity_differences=comparison.identity_differences,
            dimensions=dimensions,
        )


def _dimension_result(comparison: object) -> RegressionDimensionResult:
    from performance_lab.storage import DimensionComparison

    if not isinstance(comparison, DimensionComparison):
        raise TypeError("expected DimensionComparison")
    if not comparison.compatibility.comparable:
        return RegressionDimensionResult(
            dimension=comparison.dimension,
            state=RegressionDimensionState.NOT_COMPARABLE,
            compatibility=comparison.compatibility,
            missing_in_baseline=comparison.missing_in_baseline,
            missing_in_candidate=comparison.missing_in_candidate,
        )
    return RegressionDimensionResult(
        dimension=comparison.dimension,
        state=RegressionDimensionState.COMPARABLE,
        compatibility=comparison.compatibility,
        metrics=tuple(RegressionMetricResult(delta=delta) for delta in comparison.deltas),
        missing_in_baseline=comparison.missing_in_baseline,
        missing_in_candidate=comparison.missing_in_candidate,
    )
