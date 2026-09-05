"""Exact-fingerprint repeatability projection over immutable completed Run evidence."""

from __future__ import annotations

from collections import defaultdict

from performance_lab.domain import (
    MeasurementProvenance,
    MeasurementScope,
    Run,
    RunStatus,
    SampleStatus,
)
from performance_lab.performance import PercentileEstimate, summarize_distribution

from .regression_queries import UIQueryService as RegressionUIQueryService
from .repeatability_models import (
    RepeatabilityDistributionReadModel,
    RepeatabilityMetricReadModel,
    RepeatabilityPercentileReadModel,
    RepeatabilityReadModel,
    RepeatabilityRunValueReadModel,
    RepeatabilityState,
)
from .ui_models import MetricDimension


class UIQueryService(RegressionUIQueryService):
    """Expose repeatability without redefining measurement or statistics semantics."""

    def repeatability(self, run_id: str) -> RepeatabilityReadModel:
        anchor = self.store.get_completed(run_id, required=False)
        if anchor is None:
            raise LookupError(f"completed run not found: {run_id}")

        fingerprint_id = anchor.fingerprint.fingerprint_id
        cohort = tuple(
            sorted(
                (
                    run
                    for run in self.store.list_completed()
                    if run.fingerprint.fingerprint_id == fingerprint_id
                ),
                key=lambda run: (run.completed_at or run.created_at, run.run_id),
            )
        )
        successful = tuple(run for run in cohort if run.status == RunStatus.SUCCEEDED)
        metrics = _repeatability_metrics(successful)

        if len(cohort) < 2:
            state = RepeatabilityState.INSUFFICIENT_REPEATS
            note = (
                "Only one exact-fingerprint Run is retained. Repeat this exact frozen test to "
                "observe run-to-run variability."
            )
        elif any(metric.distribution.sample_count >= 2 for metric in metrics):
            state = RepeatabilityState.AVAILABLE
            note = (
                "Variability is computed across per-Run values from exact-fingerprint repeats. "
                "Failures remain in the cohort denominators and are not converted to zero."
            )
        else:
            state = RepeatabilityState.UNAVAILABLE
            note = (
                "Repeated exact-fingerprint Runs exist, but fewer than two successful Runs retain "
                "a shared quality or client-performance value."
            )

        samples = tuple(sample for run in cohort for sample in run.samples)
        return RepeatabilityReadModel(
            anchor_run_id=anchor.run_id,
            fingerprint_id=fingerprint_id,
            state=state,
            load_profile=anchor.fingerprint.load_profile,
            run_ids=tuple(run.run_id for run in cohort),
            run_count=len(cohort),
            succeeded_run_count=sum(run.status == RunStatus.SUCCEEDED for run in cohort),
            failed_run_count=sum(run.status == RunStatus.FAILED for run in cohort),
            cancelled_run_count=sum(run.status == RunStatus.CANCELLED for run in cohort),
            sample_attempt_count=len(samples),
            succeeded_sample_count=sum(
                sample.status == SampleStatus.SUCCEEDED for sample in samples
            ),
            failed_sample_count=sum(sample.status == SampleStatus.FAILED for sample in samples),
            cancelled_sample_count=sum(
                sample.status == SampleStatus.CANCELLED for sample in samples
            ),
            metrics=metrics,
            note=note,
        )


def _repeatability_metrics(runs: tuple[Run, ...]) -> tuple[RepeatabilityMetricReadModel, ...]:
    quality = _quality_metrics(runs)
    performance = _performance_metrics(runs)
    return tuple(
        sorted((*quality, *performance), key=lambda item: (item.dimension.value, item.metric_id))
    )


def _quality_metrics(runs: tuple[Run, ...]) -> tuple[RepeatabilityMetricReadModel, ...]:
    grouped: dict[
        tuple[str, str, str, bool],
        list[RepeatabilityRunValueReadModel],
    ] = defaultdict(list)
    for run in runs:
        for score in run.aggregate_scores:
            grouped[
                (
                    score.metric,
                    score.evaluator.evaluator_id,
                    score.evaluator.version,
                    score.higher_is_better,
                )
            ].append(RepeatabilityRunValueReadModel(run_id=run.run_id, value=score.value))

    metrics: list[RepeatabilityMetricReadModel] = []
    for (metric, evaluator_id, evaluator_version, higher_is_better), run_values in grouped.items():
        metrics.append(
            RepeatabilityMetricReadModel(
                metric_id=f"{metric}|{evaluator_id}@{evaluator_version}",
                label=metric,
                dimension=MetricDimension.QUALITY,
                higher_is_better=higher_is_better,
                run_values=tuple(run_values),
                distribution=_distribution(tuple(item.value for item in run_values)),
            )
        )
    return tuple(metrics)


def _performance_metrics(runs: tuple[Run, ...]) -> tuple[RepeatabilityMetricReadModel, ...]:
    grouped: dict[
        tuple[str, str, str],
        list[RepeatabilityRunValueReadModel],
    ] = defaultdict(list)

    for run in runs:
        per_run: dict[tuple[str, str, str], list[float]] = defaultdict(list)
        for sample in run.samples:
            for measurement in sample.measurements:
                if measurement.provenance != MeasurementProvenance.CLIENT:
                    continue
                if measurement.scope != MeasurementScope.SAMPLE:
                    continue
                if measurement.unit == "tokens":
                    continue
                per_run[(measurement.name, measurement.protocol_version, measurement.unit)].append(
                    measurement.value
                )
        for identity, values in per_run.items():
            grouped[identity].append(
                RepeatabilityRunValueReadModel(
                    run_id=run.run_id,
                    value=summarize_distribution(values).mean,
                    source_sample_count=len(values),
                )
            )

    metrics: list[RepeatabilityMetricReadModel] = []
    for (name, protocol_version, unit), run_values in grouped.items():
        metrics.append(
            RepeatabilityMetricReadModel(
                metric_id=f"{name}|client|{protocol_version}|{unit}",
                label=name,
                dimension=MetricDimension.PERFORMANCE,
                unit=unit,
                run_values=tuple(run_values),
                distribution=_distribution(tuple(item.value for item in run_values)),
            )
        )
    return tuple(metrics)


def _distribution(values: tuple[float, ...]) -> RepeatabilityDistributionReadModel:
    summary = summarize_distribution(values)
    return RepeatabilityDistributionReadModel(
        sample_count=summary.sample_count,
        minimum=summary.minimum,
        maximum=summary.maximum,
        mean=summary.mean,
        median=summary.median,
        stddev=summary.stddev,
        coefficient_of_variation=summary.coefficient_of_variation,
        p90=_percentile(summary.p90),
        p95=_percentile(summary.p95),
    )


def _percentile(estimate: PercentileEstimate) -> RepeatabilityPercentileReadModel:
    return RepeatabilityPercentileReadModel(
        percentile=estimate.percentile,
        value=estimate.value,
        sample_count=estimate.sample_count,
        qualified=estimate.qualified,
        qualification=estimate.qualification,
    )
