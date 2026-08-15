"""Compatible run comparison queries backed by domain-owned fingerprint rules."""

from __future__ import annotations

from typing import Protocol

from pydantic import BaseModel, ConfigDict, Field

from performance_lab.domain import (
    ComparisonDimension,
    CompatibilityResult,
    Measurement,
    MeasurementProvenance,
    Run,
    Score,
    compare_fingerprints,
)


class ComparisonModel(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")


class IdentityDifference(ComparisonModel):
    path: str = Field(min_length=1)
    baseline: object | None = None
    candidate: object | None = None


class MetricDelta(ComparisonModel):
    metric: str = Field(min_length=1)
    baseline_value: float
    candidate_value: float
    absolute_delta: float
    relative_delta_pct: float | None = None
    unit: str | None = None
    higher_is_better: bool | None = None


class DimensionComparison(ComparisonModel):
    dimension: ComparisonDimension
    compatibility: CompatibilityResult
    deltas: tuple[MetricDelta, ...] = ()
    missing_in_baseline: tuple[str, ...] = ()
    missing_in_candidate: tuple[str, ...] = ()


class RunComparison(ComparisonModel):
    baseline_run_id: str = Field(min_length=1)
    candidate_run_id: str = Field(min_length=1)
    identity_differences: tuple[IdentityDifference, ...]
    dimensions: tuple[DimensionComparison, ...]

    def dimension(self, dimension: ComparisonDimension) -> DimensionComparison:
        for result in self.dimensions:
            if result.dimension == dimension:
                return result
        raise KeyError(dimension)


class CompletedRunReader(Protocol):
    def get_completed(self, run_id: str, *, required: bool = True) -> Run | None: ...


class RunComparisonService:
    def __init__(self, store: CompletedRunReader) -> None:
        self.store = store

    def compare(self, baseline_run_id: str, candidate_run_id: str) -> RunComparison:
        baseline = self.store.get_completed(baseline_run_id)
        candidate = self.store.get_completed(candidate_run_id)
        if baseline is None or candidate is None:
            raise LookupError("comparison requires two completed runs")
        return compare_runs(baseline, candidate)


def compare_runs(baseline: Run, candidate: Run) -> RunComparison:
    """Surface identity differences first, then deltas only for compatible dimensions."""

    identity_differences = tuple(
        _diff_values(
            baseline.fingerprint.model_dump(mode="json"),
            candidate.fingerprint.model_dump(mode="json"),
        )
    )
    dimensions = tuple(
        _compare_dimension(baseline, candidate, dimension) for dimension in ComparisonDimension
    )
    return RunComparison(
        baseline_run_id=baseline.run_id,
        candidate_run_id=candidate.run_id,
        identity_differences=identity_differences,
        dimensions=dimensions,
    )


def _compare_dimension(
    baseline: Run,
    candidate: Run,
    dimension: ComparisonDimension,
) -> DimensionComparison:
    compatibility = compare_fingerprints(
        baseline.fingerprint,
        candidate.fingerprint,
        dimension,
    )
    if not compatibility.comparable:
        return DimensionComparison(dimension=dimension, compatibility=compatibility)

    if dimension == ComparisonDimension.CAPABILITY:
        baseline_metrics = _score_metrics(baseline.aggregate_scores)
        candidate_metrics = _score_metrics(candidate.aggregate_scores)
    elif dimension == ComparisonDimension.RUNTIME:
        baseline_metrics = _measurement_metrics(
            baseline.aggregate_measurements,
            allowed_provenance={MeasurementProvenance.CLIENT},
        )
        candidate_metrics = _measurement_metrics(
            candidate.aggregate_measurements,
            allowed_provenance={MeasurementProvenance.CLIENT},
        )
    else:
        baseline_metrics = _measurement_metrics(
            baseline.aggregate_measurements,
            allowed_provenance={MeasurementProvenance.HOST, MeasurementProvenance.RUNTIME},
        )
        candidate_metrics = _measurement_metrics(
            candidate.aggregate_measurements,
            allowed_provenance={MeasurementProvenance.HOST, MeasurementProvenance.RUNTIME},
        )

    baseline_keys = set(baseline_metrics)
    candidate_keys = set(candidate_metrics)
    shared = sorted(baseline_keys & candidate_keys)
    deltas = tuple(
        _metric_delta(key, baseline_metrics[key], candidate_metrics[key]) for key in shared
    )
    return DimensionComparison(
        dimension=dimension,
        compatibility=compatibility,
        deltas=deltas,
        missing_in_baseline=tuple(sorted(candidate_keys - baseline_keys)),
        missing_in_candidate=tuple(sorted(baseline_keys - candidate_keys)),
    )


def _score_metrics(scores: tuple[Score, ...]) -> dict[str, tuple[float, str | None, bool | None]]:
    return {
        f"{score.metric}|{score.evaluator.evaluator_id}@{score.evaluator.version}": (
            score.value,
            None,
            score.higher_is_better,
        )
        for score in scores
    }


def _measurement_metrics(
    measurements: tuple[Measurement, ...],
    *,
    allowed_provenance: set[MeasurementProvenance],
) -> dict[str, tuple[float, str | None, bool | None]]:
    return {
        (
            f"{measurement.name}|{measurement.provenance.value}|"
            f"{measurement.protocol_version}|{measurement.unit}"
        ): (measurement.value, measurement.unit, None)
        for measurement in measurements
        if measurement.provenance in allowed_provenance
    }


def _metric_delta(
    key: str,
    baseline: tuple[float, str | None, bool | None],
    candidate: tuple[float, str | None, bool | None],
) -> MetricDelta:
    baseline_value, unit, higher_is_better = baseline
    candidate_value = candidate[0]
    absolute = candidate_value - baseline_value
    relative = absolute / abs(baseline_value) * 100 if baseline_value != 0 else None
    return MetricDelta(
        metric=key,
        baseline_value=baseline_value,
        candidate_value=candidate_value,
        absolute_delta=absolute,
        relative_delta_pct=relative,
        unit=unit,
        higher_is_better=higher_is_better,
    )


def _diff_values(
    baseline: object,
    candidate: object,
    *,
    path: str = "fingerprint",
) -> list[IdentityDifference]:
    if baseline == candidate:
        return []
    if isinstance(baseline, dict) and isinstance(candidate, dict):
        differences: list[IdentityDifference] = []
        for key in sorted(set(baseline) | set(candidate)):
            child_path = f"{path}.{key}"
            if key not in baseline:
                differences.append(
                    IdentityDifference(path=child_path, baseline=None, candidate=candidate[key])
                )
            elif key not in candidate:
                differences.append(
                    IdentityDifference(path=child_path, baseline=baseline[key], candidate=None)
                )
            else:
                differences.extend(_diff_values(baseline[key], candidate[key], path=child_path))
        return differences
    if isinstance(baseline, list) and isinstance(candidate, list):
        if len(baseline) != len(candidate):
            return [IdentityDifference(path=path, baseline=baseline, candidate=candidate)]
        differences = []
        for index, (baseline_item, candidate_item) in enumerate(
            zip(baseline, candidate, strict=True)
        ):
            differences.extend(
                _diff_values(
                    baseline_item,
                    candidate_item,
                    path=f"{path}[{index}]",
                )
            )
        return differences
    return [IdentityDifference(path=path, baseline=baseline, candidate=candidate)]
