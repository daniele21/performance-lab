"""Browser execution-policy overrides layered on canonical target/query behavior."""

from __future__ import annotations

from performance_lab.domain import EndpointProfile, EvidenceMode, GenerationConfig
from performance_lab.run_config import StarterRunConfig

from .evidence_models import (
    EvidenceContentReadModel,
    EvidenceContentState,
    SampleEvidenceDetailReadModel,
    SampleQualitySummaryReadModel,
    SampleQualityVerdict,
    SampleScoreReadModel,
)
from .run_jobs import starter_run_config_digest
from .target_queries import UIQueryService as TargetUIQueryService
from .ui_models import RunPreflightReadModel, RunPreflightRequest, TargetSummaryReadModel

_CASE_RESULT_METRICS = {
    "exact_match",
    "normalized_exact_match",
    "accuracy",
    "numeric_match",
    "pattern_valid",
    "json_valid",
    "json_schema_valid",
    "field_accuracy",
}


class UIQueryService(TargetUIQueryService):
    """Apply product-owned retention defaults without changing CLI/campaign safety defaults.

    Direct ``Test a model`` runs are diagnostic and therefore evidence-rich. Campaign-derived
    runs remain aggregate-safe even if the UI server itself was started from a richer template.
    """

    def preflight(self, request: RunPreflightRequest) -> RunPreflightReadModel:
        prepared = super().preflight(request)
        if not prepared.can_run or prepared.preview is None:
            return prepared
        config = prepared.preview.config.model_copy(
            update={"evidence_mode": EvidenceMode.EVIDENCE_RICH}
        )
        preview = prepared.preview.model_copy(
            update={
                "config": config,
                "config_digest": starter_run_config_digest(config),
            }
        )
        return prepared.model_copy(update={"preview": preview})

    def get_sample_evidence(
        self,
        run_id: str,
        task_id: str,
        sample_id: str,
        attempt: int,
    ) -> SampleEvidenceDetailReadModel:
        detail = super().get_sample_evidence(run_id, task_id, sample_id, attempt)
        changes: dict[str, object] = {"quality": _quality_summary(detail)}
        reader = getattr(self.store, "get_sample_content", None)
        if reader is not None:
            content = reader(run_id, task_id, sample_id, attempt)
            if content is not None:
                changes["prompt"] = EvidenceContentReadModel(
                    state=EvidenceContentState.RETAINED,
                    content=content.prompt,
                )
                changes["response"] = (
                    EvidenceContentReadModel(
                        state=EvidenceContentState.RETAINED,
                        content=content.response,
                    )
                    if content.response is not None
                    else EvidenceContentReadModel(
                        state=EvidenceContentState.UNAVAILABLE,
                        reason="model_response_not_produced",
                    )
                )
        return detail.model_copy(update=changes)

    def _campaign_run_config(
        self,
        *,
        target: TargetSummaryReadModel,
        endpoint: EndpointProfile,
        model_id: str,
        generation: GenerationConfig,
        suite_id: str,
        suite_version: str,
    ) -> StarterRunConfig:
        config = super()._campaign_run_config(
            target=target,
            endpoint=endpoint,
            model_id=model_id,
            generation=generation,
            suite_id=suite_id,
            suite_version=suite_version,
        )
        return config.model_copy(update={"evidence_mode": EvidenceMode.AGGREGATE_SAFE})


def _quality_summary(detail: SampleEvidenceDetailReadModel) -> SampleQualitySummaryReadModel:
    if not detail.scores:
        return SampleQualitySummaryReadModel(verdict=SampleQualityVerdict.NOT_EVALUATED)
    score = _primary_score(detail)
    percentage = score.value * 100 if 0.0 <= score.value <= 1.0 else None
    if score.metric not in _CASE_RESULT_METRICS or percentage is None:
        return SampleQualitySummaryReadModel(
            verdict=SampleQualityVerdict.SCORED,
            metric=score.metric,
            value=score.value,
            percentage=percentage,
        )
    if score.value == 1.0:
        verdict = SampleQualityVerdict.CORRECT
    elif score.value == 0.0:
        verdict = SampleQualityVerdict.INCORRECT
    else:
        verdict = SampleQualityVerdict.PARTIAL
    return SampleQualitySummaryReadModel(
        verdict=verdict,
        metric=score.metric,
        value=score.value,
        percentage=percentage,
    )


def _primary_score(detail: SampleEvidenceDetailReadModel) -> SampleScoreReadModel:
    if detail.benchmark_case is not None:
        by_metric = {score.metric: score for score in detail.scores}
        for metric in detail.benchmark_case.metric_names:
            if metric in by_metric:
                return by_metric[metric]
    return detail.scores[0]
