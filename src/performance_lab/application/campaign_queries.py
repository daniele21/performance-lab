"""Campaign lifecycle/result read queries over persisted Campaign and immutable Run evidence."""

from __future__ import annotations

from typing import Protocol

from performance_lab.domain import (
    TERMINAL_CAMPAIGN_STATUSES,
    Campaign,
    CampaignEntryStatus,
    CampaignStatus,
    ComparisonDimension,
    MeasurementProvenance,
    Run,
    RunStatus,
    compare_fingerprints,
)

from .campaign_models import (
    CampaignCompatibilityReasonReadModel,
    CampaignDimensionReadModel,
    CampaignEntryReadModel,
    CampaignReadModel,
    CampaignRecommendationReadModel,
    CampaignResultsReadModel,
)
from .campaign_policy import (
    STRICT_QUALITY_DOMINANCE_POLICY_ID,
    STRICT_QUALITY_DOMINANCE_POLICY_VERSION,
    decision_policy_read_model,
    recommend_strict_quality_dominance,
)
from .ui_models import RunDetailReadModel
from .ui_queries import CompletedRunReader


class CampaignReader(Protocol):
    def get(self, campaign_id: str) -> Campaign: ...

    def list_all(self) -> tuple[Campaign, ...]: ...


class RunProjectionQueries(Protocol):
    store: CompletedRunReader

    def get_run(self, run_id: str) -> RunDetailReadModel: ...


class CampaignQueryService:
    """Join Campaign progress with immutable Run evidence without changing either owner."""

    def __init__(self, campaigns: CampaignReader, runs: RunProjectionQueries) -> None:
        self._campaigns = campaigns
        self._runs = runs

    def list_campaigns(self) -> tuple[CampaignReadModel, ...]:
        return tuple(self._project(campaign) for campaign in reversed(self._campaigns.list_all()))

    def get(self, campaign_id: str) -> CampaignReadModel:
        return self._project(self._campaigns.get(campaign_id))

    def _project(self, campaign: Campaign) -> CampaignReadModel:
        raw_runs: dict[str, Run] = {}
        entries: list[CampaignEntryReadModel] = []
        for entry in campaign.entries:
            detail = None
            raw_run = None
            if entry.run_id is not None:
                raw_run = self._runs.store.get_completed(entry.run_id, required=False)
                if raw_run is not None:
                    raw_runs[entry.entry_id] = raw_run
                    detail = self._runs.get_run(entry.run_id)
            entries.append(
                CampaignEntryReadModel(
                    entry_id=entry.entry_id,
                    candidate_id=entry.candidate_id,
                    model_id=entry.model_id,
                    config_digest=entry.config_digest,
                    status=entry.status,
                    run_id=entry.run_id,
                    completed_samples=entry.completed_samples,
                    total_samples=entry.total_samples,
                    error_code=entry.error_code,
                    error_message=entry.error_message,
                    identity=detail.summary.identity if detail is not None else None,
                    metrics=detail.summary.metrics if detail is not None else (),
                )
            )

        results = self._results(campaign, raw_runs)
        return CampaignReadModel(
            campaign_id=campaign.campaign_id,
            plan_digest=campaign.plan_digest,
            use_case_id=campaign.use_case_id,
            use_case_version=campaign.use_case_version,
            target_id=campaign.target_id,
            suite_id=campaign.suite_id,
            suite_version=campaign.suite_version,
            status=campaign.status,
            revision=campaign.revision,
            created_at=campaign.created_at,
            updated_at=campaign.updated_at,
            completed_at=campaign.completed_at,
            entries=tuple(entries),
            results=results,
            error_code=campaign.error_code,
            error_message=campaign.error_message,
        )

    def _results(
        self,
        campaign: Campaign,
        runs_by_entry: dict[str, Run],
    ) -> CampaignResultsReadModel:
        policy = decision_policy_read_model()
        successful = tuple(
            (entry.candidate_id, runs_by_entry[entry.entry_id])
            for entry in campaign.entries
            if entry.status == CampaignEntryStatus.SUCCEEDED
            and entry.entry_id in runs_by_entry
            and runs_by_entry[entry.entry_id].status == RunStatus.SUCCEEDED
        )
        compatibility = _compatibility(successful)

        if campaign.status not in TERMINAL_CAMPAIGN_STATUSES:
            return CampaignResultsReadModel(
                state="pending",
                decision_policy=policy,
                compatibility=compatibility,
                recommendation_reason=(
                    "Recommendation is evaluated only after the campaign reaches a terminal state."
                ),
            )
        if campaign.status != CampaignStatus.SUCCEEDED:
            return CampaignResultsReadModel(
                state="partial",
                decision_policy=policy,
                compatibility=compatibility,
                recommendation_reason=(
                    "The campaign did not complete every planned run successfully. "
                    "Partial evidence remains inspectable, but no best-fit recommendation is "
                    "produced."
                ),
            )
        if len(successful) != len(campaign.entries):
            return CampaignResultsReadModel(
                state="partial",
                decision_policy=policy,
                compatibility=compatibility,
                recommendation_reason=(
                    "Campaign metadata is complete but one or more immutable Run records are "
                    "unavailable, so no recommendation is produced."
                ),
            )
        if (
            campaign.decision_policy.policy_id != STRICT_QUALITY_DOMINANCE_POLICY_ID
            or campaign.decision_policy.policy_version != STRICT_QUALITY_DOMINANCE_POLICY_VERSION
        ):
            return CampaignResultsReadModel(
                state="partial",
                decision_policy=policy,
                compatibility=compatibility,
                recommendation_reason="The persisted campaign decision policy is not supported.",
            )

        decision = recommend_strict_quality_dominance(successful)
        recommendation = None
        if decision.candidate_id is not None and decision.run_id is not None:
            entry = next(
                item for item in campaign.entries if item.candidate_id == decision.candidate_id
            )
            recommendation = CampaignRecommendationReadModel(
                candidate_id=decision.candidate_id,
                run_id=decision.run_id,
                model_id=entry.model_id,
                rationale=decision.reason,
            )
        return CampaignResultsReadModel(
            state="ready",
            decision_policy=policy,
            compatibility=compatibility,
            recommendation=recommendation,
            recommendation_reason=decision.reason,
        )


def _compatibility(
    candidates: tuple[tuple[str, Run], ...],
) -> tuple[CampaignDimensionReadModel, ...]:
    if len(candidates) < 2:
        return tuple(
            CampaignDimensionReadModel(
                dimension=dimension,
                comparable=False,
                evidence_available=all(
                    _has_dimension_evidence(run, dimension) for _, run in candidates
                ),
                reasons=(),
            )
            for dimension in ComparisonDimension
        )

    baseline_run = candidates[0][1]
    dimensions: list[CampaignDimensionReadModel] = []
    for dimension in ComparisonDimension:
        reasons: list[CampaignCompatibilityReasonReadModel] = []
        for _, candidate_run in candidates[1:]:
            result = compare_fingerprints(
                baseline_run.fingerprint,
                candidate_run.fingerprint,
                dimension,
            )
            reasons.extend(
                CampaignCompatibilityReasonReadModel(
                    baseline_run_id=baseline_run.run_id,
                    candidate_run_id=candidate_run.run_id,
                    code=reason.code.value,
                    field=reason.field,
                    message=reason.message,
                )
                for reason in result.reasons
            )
        dimensions.append(
            CampaignDimensionReadModel(
                dimension=dimension,
                comparable=not reasons,
                evidence_available=all(
                    _has_dimension_evidence(run, dimension) for _, run in candidates
                ),
                reasons=tuple(reasons),
            )
        )
    return tuple(dimensions)


def _has_dimension_evidence(run: Run, dimension: ComparisonDimension) -> bool:
    if dimension == ComparisonDimension.CAPABILITY:
        return bool(run.aggregate_scores)
    if dimension == ComparisonDimension.RUNTIME:
        return any(
            item.provenance == MeasurementProvenance.CLIENT for item in run.aggregate_measurements
        )
    return any(
        item.provenance in {MeasurementProvenance.HOST, MeasurementProvenance.RUNTIME}
        for item in run.aggregate_measurements
    )
