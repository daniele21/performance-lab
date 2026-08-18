"""Application query projections for browser-facing read paths."""

from __future__ import annotations

import json
from datetime import UTC, datetime
from hashlib import sha256
from typing import Protocol

from performance_lab.domain import (
    EvaluationSuite,
    Measurement,
    MeasurementProvenance,
    Run,
    Score,
    Target,
)
from performance_lab.regression import BaselineBinding, RegressionPolicy
from performance_lab.storage import RunComparisonService

from .ui_models import (
    BaselineSummaryReadModel,
    ComparisonReadModel,
    CompatibilityReasonReadModel,
    DimensionComparisonReadModel,
    EvidenceAvailability,
    IdentitySummary,
    MetricDimension,
    MetricReadModel,
    PolicySummaryReadModel,
    RunDetailReadModel,
    RunEvidenceReadModel,
    RunSummaryReadModel,
    SuiteSummaryReadModel,
    TargetSummaryReadModel,
    TestedModelReadModel,
)


class CompletedRunReader(Protocol):
    def get_completed(self, run_id: str, *, required: bool = True) -> Run | None: ...

    def list_completed(self) -> tuple[Run, ...]: ...


class UIQueryService:
    """Project canonical evidence into stable UI-shaped read models."""

    def __init__(
        self,
        store: CompletedRunReader,
        *,
        targets: tuple[Target, ...] = (),
        suites: tuple[EvaluationSuite, ...] = (),
        baselines: tuple[BaselineBinding, ...] = (),
        policies: tuple[RegressionPolicy, ...] = (),
    ) -> None:
        self.store = store
        self.targets = targets
        self.suites = suites
        self.baselines = baselines
        self.policies = policies
        self.comparisons = RunComparisonService(store)

    def list_runs(self, *, offset: int = 0, limit: int = 50) -> tuple[RunSummaryReadModel, ...]:
        if offset < 0:
            raise ValueError("offset must be >= 0")
        if not 1 <= limit <= 200:
            raise ValueError("limit must be between 1 and 200")
        runs = sorted(
            self.store.list_completed(),
            key=lambda item: (item.completed_at or item.created_at, item.run_id),
            reverse=True,
        )
        return tuple(_run_summary(run) for run in runs[offset : offset + limit])

    def get_run(self, run_id: str) -> RunDetailReadModel:
        run = self.store.get_completed(run_id)
        if run is None:
            raise LookupError(f"completed run not found: {run_id}")
        return RunDetailReadModel(
            summary=_run_summary(run),
            evidence=RunEvidenceReadModel(
                fingerprint=run.fingerprint,
                dataset_count=len(run.fingerprint.dataset_snapshots),
                evaluator_count=len(run.fingerprint.evaluator_versions),
                sample_count=len(run.samples),
            ),
        )

    def list_tested_models(self) -> tuple[TestedModelReadModel, ...]:
        grouped: dict[str, list[Run]] = {}
        for run in self.store.list_completed():
            grouped.setdefault(_cohort_key(run), []).append(run)

        models: list[TestedModelReadModel] = []
        for cohort_key, runs in grouped.items():
            latest = max(
                runs,
                key=lambda item: (item.completed_at or item.created_at, item.run_id),
            )
            models.append(
                TestedModelReadModel(
                    cohort_key=cohort_key,
                    identity=_identity(latest),
                    run_count=len(runs),
                    latest_run_id=latest.run_id,
                    latest_completed_at=latest.completed_at,
                    latest_metrics=_metrics(latest),
                )
            )
        epoch = datetime.min.replace(tzinfo=UTC)
        return tuple(
            sorted(
                models,
                key=lambda item: (item.latest_completed_at or epoch, item.latest_run_id),
                reverse=True,
            )
        )

    def list_targets(self) -> tuple[TargetSummaryReadModel, ...]:
        return tuple(
            TargetSummaryReadModel(
                target_id=target.target_id,
                display_name=target.display_name,
                adapter_type=target.adapter_type,
                endpoint_profile_id=target.endpoint_profile_id,
                endpoint_identity=target.endpoint_identity,
                capabilities=tuple(capability.value for capability in target.declared_capabilities),
            )
            for target in sorted(self.targets, key=lambda item: item.target_id)
        )

    def list_suites(self) -> tuple[SuiteSummaryReadModel, ...]:
        return tuple(
            SuiteSummaryReadModel(
                suite_id=suite.suite_id,
                suite_version=suite.suite_version,
                task_count=len(suite.tasks),
                task_ids=tuple(task.task_id for task in suite.tasks),
            )
            for suite in sorted(self.suites, key=lambda item: (item.suite_id, item.suite_version))
        )

    def list_baselines(self) -> tuple[BaselineSummaryReadModel, ...]:
        return tuple(
            BaselineSummaryReadModel(
                baseline_id=baseline.baseline_id,
                run_id=baseline.run_id,
                fingerprint_id=baseline.fingerprint_id,
                selected_at=baseline.selected_at,
                label=baseline.label,
            )
            for baseline in sorted(self.baselines, key=lambda item: item.baseline_id)
        )

    def list_policies(self) -> tuple[PolicySummaryReadModel, ...]:
        return tuple(
            PolicySummaryReadModel(
                policy_id=policy.policy_id,
                policy_version=policy.policy_version,
                rule_count=len(policy.rules),
            )
            for policy in sorted(
                self.policies, key=lambda item: (item.policy_id, item.policy_version)
            )
        )

    def compare(self, baseline_run_id: str, candidate_run_id: str) -> ComparisonReadModel:
        comparison = self.comparisons.compare(baseline_run_id, candidate_run_id)
        return ComparisonReadModel(
            baseline_run_id=comparison.baseline_run_id,
            candidate_run_id=comparison.candidate_run_id,
            identity_differences=comparison.identity_differences,
            dimensions=tuple(
                DimensionComparisonReadModel(
                    dimension=dimension.dimension,
                    comparable=dimension.compatibility.comparable,
                    reasons=tuple(
                        CompatibilityReasonReadModel(
                            code=reason.code.value,
                            field=reason.field,
                            message=reason.message,
                            baseline=reason.baseline,
                            candidate=reason.candidate,
                        )
                        for reason in dimension.compatibility.reasons
                    ),
                    deltas=dimension.deltas if dimension.compatibility.comparable else (),
                    missing_in_baseline=dimension.missing_in_baseline,
                    missing_in_candidate=dimension.missing_in_candidate,
                )
                for dimension in comparison.dimensions
            ),
        )


def _identity(run: Run) -> IdentitySummary:
    fingerprint = run.fingerprint
    return IdentitySummary(
        model_id=fingerprint.model.model_id,
        revision=fingerprint.model.revision,
        quantization=fingerprint.model.quantization,
        artifact_digest=fingerprint.model.artifact_digest,
        target_id=fingerprint.target_id,
        endpoint_identity=fingerprint.endpoint_identity,
        runtime_name=fingerprint.runtime.name,
        runtime_version=fingerprint.runtime.version,
        hardware_device_id=fingerprint.hardware.device_id,
        hardware_device_class=fingerprint.hardware.device_class,
    )


def _cohort_key(run: Run) -> str:
    payload = {
        "model": run.fingerprint.model.model_dump(mode="json"),
        "runtime": run.fingerprint.runtime.model_dump(mode="json"),
        "hardware": run.fingerprint.hardware.model_dump(mode="json"),
    }
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return sha256(canonical.encode("utf-8")).hexdigest()


def _run_summary(run: Run) -> RunSummaryReadModel:
    return RunSummaryReadModel(
        run_id=run.run_id,
        status=run.status,
        created_at=run.created_at,
        completed_at=run.completed_at,
        suite_id=run.suite.suite_id,
        suite_version=run.suite.suite_version,
        fingerprint_id=run.fingerprint.fingerprint_id,
        identity=_identity(run),
        metrics=_metrics(run),
    )


def _metrics(run: Run) -> tuple[MetricReadModel, ...]:
    quality = tuple(
        sorted((_score_metric(score) for score in run.aggregate_scores), key=lambda x: x.metric_id)
    )
    measurements = tuple(
        sorted(
            (_measurement_metric(item) for item in run.aggregate_measurements),
            key=lambda x: (x.dimension.value, x.metric_id),
        )
    )
    return quality + measurements


def _score_metric(score: Score) -> MetricReadModel:
    return MetricReadModel(
        metric_id=f"{score.metric}|{score.evaluator.evaluator_id}@{score.evaluator.version}",
        label=score.metric,
        dimension=MetricDimension.QUALITY,
        availability=EvidenceAvailability.AVAILABLE,
        value=score.value,
        higher_is_better=score.higher_is_better,
        provenance=f"{score.evaluator.evaluator_id}@{score.evaluator.version}",
    )


def _measurement_metric(measurement: Measurement) -> MetricReadModel:
    dimension = (
        MetricDimension.PERFORMANCE
        if measurement.provenance == MeasurementProvenance.CLIENT
        else MetricDimension.RESOURCES
    )
    return MetricReadModel(
        metric_id=(
            f"{measurement.name}|{measurement.provenance.value}|"
            f"{measurement.protocol_version}|{measurement.unit}"
        ),
        label=measurement.name,
        dimension=dimension,
        availability=EvidenceAvailability.AVAILABLE,
        value=measurement.value,
        unit=measurement.unit,
        provenance=measurement.provenance.value,
        protocol_version=measurement.protocol_version,
    )
