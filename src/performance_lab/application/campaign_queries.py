"""Campaign lifecycle/result read queries over persisted Campaign and immutable Run evidence."""

from __future__ import annotations

from typing import Literal, Protocol

from performance_lab.domain import (
    TERMINAL_CAMPAIGN_STATUSES,
    Campaign,
    CampaignEntry,
    CampaignEntryStatus,
    CampaignStatus,
    ComparisonDimension,
    MeasurementProvenance,
    Run,
    RunStatus,
    SampleExecution,
    compare_fingerprints,
)

from .campaign_models import (
    CampaignCaseCandidateReadModel,
    CampaignCaseComparisonReadModel,
    CampaignCaseSummaryReadModel,
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
from .device_evidence import resource_measurement_is_decision_eligible
from .evidence_models import SampleEvidenceDetailReadModel
from .ui_models import RunDetailReadModel
from .ui_queries import CompletedRunReader


class CampaignReader(Protocol):
    def get(self, campaign_id: str) -> Campaign: ...

    def list_all(self) -> tuple[Campaign, ...]: ...


class RunProjectionQueries(Protocol):
    store: CompletedRunReader

    def get_run(self, run_id: str) -> RunDetailReadModel: ...

    def get_sample_evidence(
        self,
        run_id: str,
        task_id: str,
        sample_id: str,
        attempt: int,
    ) -> SampleEvidenceDetailReadModel: ...


class CampaignQueryService:
    """Join Campaign progress with immutable Run evidence without changing either owner."""

    def __init__(self, campaigns: CampaignReader, runs: RunProjectionQueries) -> None:
        self._campaigns = campaigns
        self._runs = runs

    def list_campaigns(self) -> tuple[CampaignReadModel, ...]:
        return tuple(self._project(campaign) for campaign in reversed(self._campaigns.list_all()))

    def get(self, campaign_id: str) -> CampaignReadModel:
        return self._project(self._campaigns.get(campaign_id))

    def list_cases(self, campaign_id: str) -> tuple[CampaignCaseSummaryReadModel, ...]:
        """List retained case identities without manufacturing case content or joins in the UI."""
        campaign = self._campaigns.get(campaign_id)
        runs = tuple(
            run
            for entry in campaign.entries
            if entry.run_id is not None
            for run in (self._runs.store.get_completed(entry.run_id, required=False),)
            if run is not None
        )
        identities = sorted(
            {(sample.task_id, sample.sample_id) for run in runs for sample in run.samples}
        )
        summaries: list[CampaignCaseSummaryReadModel] = []
        for task_id, sample_id in identities:
            available = 0
            case_id = None
            for run in runs:
                matches = _matching_samples(run, task_id, sample_id)
                if len(matches) != 1:
                    continue
                available += 1
                if case_id is not None:
                    continue
                try:
                    evidence = self._runs.get_sample_evidence(
                        run.run_id,
                        task_id,
                        sample_id,
                        matches[0].attempt,
                    )
                except LookupError:
                    continue
                if evidence.benchmark_case is not None:
                    case_id = evidence.benchmark_case.case_id
            summaries.append(
                CampaignCaseSummaryReadModel(
                    task_id=task_id,
                    sample_id=sample_id,
                    case_id=case_id,
                    candidate_count=len(campaign.entries),
                    available_candidate_count=available,
                )
            )
        return tuple(summaries)

    def compare_case(
        self,
        campaign_id: str,
        task_id: str,
        sample_id: str,
    ) -> CampaignCaseComparisonReadModel:
        """Compare one exact retained case across Campaign candidates using Python-owned truth."""
        campaign = self._campaigns.get(campaign_id)
        available: dict[
            str,
            tuple[CampaignEntry, Run, SampleEvidenceDetailReadModel],
        ] = {}
        unavailable: dict[str, str] = {}
        raw_runs: dict[str, Run] = {}

        for entry in campaign.entries:
            if entry.run_id is None:
                unavailable[entry.entry_id] = "Campaign entry has no immutable Run identity."
                continue
            run = self._runs.store.get_completed(entry.run_id, required=False)
            if run is None:
                unavailable[entry.entry_id] = "Immutable Run evidence is unavailable."
                continue
            raw_runs[entry.entry_id] = run
            matches = _matching_samples(run, task_id, sample_id)
            if not matches:
                unavailable[entry.entry_id] = (
                    "This exact benchmark case is not retained in this Run."
                )
                continue
            if len(matches) != 1:
                unavailable[entry.entry_id] = (
                    "Multiple retained attempts exist for this case; select an exact attempt "
                    "before comparing."
                )
                continue
            try:
                evidence = self._runs.get_sample_evidence(
                    run.run_id,
                    task_id,
                    sample_id,
                    matches[0].attempt,
                )
            except LookupError:
                unavailable[entry.entry_id] = "Sample evidence projection is unavailable."
                continue
            available[entry.entry_id] = (entry, run, evidence)

        if not available:
            raise LookupError(f"campaign case not found: {campaign_id}/{task_id}/{sample_id}")

        reference_entry, reference_run, reference_evidence = next(iter(available.values()))
        candidates: list[CampaignCaseCandidateReadModel] = []
        for entry in campaign.entries:
            run = raw_runs.get(entry.entry_id)
            identity = self._runs.get_run(run.run_id).summary.identity if run is not None else None
            candidate = available.get(entry.entry_id)
            if candidate is None:
                candidates.append(
                    CampaignCaseCandidateReadModel(
                        entry_id=entry.entry_id,
                        candidate_id=entry.candidate_id,
                        model_id=entry.model_id,
                        config_digest=entry.config_digest,
                        entry_status=entry.status,
                        run_id=entry.run_id,
                        identity=identity,
                        unavailable_reason=unavailable.get(
                            entry.entry_id,
                            "Comparable sample evidence is unavailable.",
                        ),
                    )
                )
                continue

            _, candidate_run, evidence = candidate
            reasons: list[CampaignCompatibilityReasonReadModel] = []
            if entry.entry_id != reference_entry.entry_id:
                compatibility = compare_fingerprints(
                    reference_run.fingerprint,
                    candidate_run.fingerprint,
                    ComparisonDimension.CAPABILITY,
                )
                reasons.extend(
                    CampaignCompatibilityReasonReadModel(
                        baseline_run_id=reference_run.run_id,
                        candidate_run_id=candidate_run.run_id,
                        code=reason.code.value,
                        field=reason.field,
                        message=reason.message,
                    )
                    for reason in compatibility.reasons
                )
                if (
                    reference_evidence.benchmark_case is not None
                    and evidence.benchmark_case is not None
                    and reference_evidence.benchmark_case.case_id != evidence.benchmark_case.case_id
                ):
                    reasons.append(
                        CampaignCompatibilityReasonReadModel(
                            baseline_run_id=reference_run.run_id,
                            candidate_run_id=candidate_run.run_id,
                            code="benchmark_case_mismatch",
                            field="benchmark_case.case_id",
                            message=(
                                "benchmark case identity differs between reference and candidate"
                            ),
                        )
                    )
            candidates.append(
                CampaignCaseCandidateReadModel(
                    entry_id=entry.entry_id,
                    candidate_id=entry.candidate_id,
                    model_id=entry.model_id,
                    config_digest=entry.config_digest,
                    entry_status=entry.status,
                    run_id=candidate_run.run_id,
                    identity=identity,
                    comparable_to_reference=not reasons,
                    compatibility_reasons=tuple(reasons),
                    evidence=evidence,
                )
            )

        comparable_count = sum(
            item.evidence is not None and item.comparable_to_reference for item in candidates
        )
        state: Literal["ready", "partial", "not_comparable"]
        if comparable_count == len(campaign.entries) and comparable_count >= 2:
            state = "ready"
            summary = (
                "All candidate Runs retain this exact case and are capability-compatible under "
                "the frozen benchmark, dataset and evaluator protocol."
            )
        elif comparable_count >= 2:
            state = "partial"
            summary = (
                "At least two candidate Runs can be compared for this exact case. Missing or "
                "incompatible candidates remain explicit and are excluded from conclusions."
            )
        else:
            state = "not_comparable"
            summary = (
                "Fewer than two compatible candidate Runs retain this exact case, so no "
                "cross-candidate conclusion is valid."
            )

        benchmark_case = next(
            (
                item.evidence.benchmark_case
                for item in candidates
                if item.evidence is not None and item.evidence.benchmark_case is not None
            ),
            None,
        )
        return CampaignCaseComparisonReadModel(
            campaign_id=campaign.campaign_id,
            suite_id=campaign.suite_id,
            suite_version=campaign.suite_version,
            task_id=task_id,
            sample_id=sample_id,
            state=state,
            reference_run_id=reference_run.run_id,
            benchmark_case=benchmark_case,
            candidates=tuple(candidates),
            comparable_candidate_count=comparable_count,
            summary=summary,
        )

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


def _matching_samples(
    run: Run,
    task_id: str,
    sample_id: str,
) -> tuple[SampleExecution, ...]:
    return tuple(
        sample
        for sample in run.samples
        if sample.task_id == task_id and sample.sample_id == sample_id
    )


def _compatibility(
    candidates: tuple[tuple[str, Run], ...],
) -> tuple[CampaignDimensionReadModel, ...]:
    runs = tuple(run for _, run in candidates)
    if len(candidates) < 2:
        return tuple(
            CampaignDimensionReadModel(
                dimension=dimension,
                comparable=False,
                evidence_available=bool(runs)
                and all(_has_dimension_evidence(run, dimension) for run in runs),
                evidence_note=_dimension_evidence_note(runs, dimension),
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
                    _has_dimension_evidence(run, dimension) for run in runs
                ),
                evidence_note=_dimension_evidence_note(runs, dimension),
                reasons=tuple(reasons),
            )
        )
    return tuple(dimensions)


def _dimension_evidence_note(
    runs: tuple[Run, ...],
    dimension: ComparisonDimension,
) -> str | None:
    if runs and all(_has_dimension_evidence(run, dimension) for run in runs):
        return None
    if not runs:
        return "No completed candidate Run evidence is available for this dimension."
    if dimension == ComparisonDimension.CAPABILITY:
        return "Comparable aggregate quality evidence is unavailable for one or more candidates."
    if dimension == ComparisonDimension.RUNTIME:
        return "Black-box request performance evidence is unavailable for one or more candidates."
    contextual_resource_telemetry = any(
        item.provenance in {MeasurementProvenance.HOST, MeasurementProvenance.RUNTIME}
        for run in runs
        for item in run.aggregate_measurements
    )
    if contextual_resource_telemetry:
        return (
            "Contextual host/runtime telemetry is retained, but no explicitly attributable "
            "model-resource metric is decision-eligible for every candidate."
        )
    return "No explicitly attributable model-resource evidence is retained for every candidate."


def _has_dimension_evidence(run: Run, dimension: ComparisonDimension) -> bool:
    if dimension == ComparisonDimension.CAPABILITY:
        return bool(run.aggregate_scores)
    if dimension == ComparisonDimension.RUNTIME:
        return any(
            item.provenance == MeasurementProvenance.CLIENT for item in run.aggregate_measurements
        )
    return any(
        resource_measurement_is_decision_eligible(item) for item in run.aggregate_measurements
    )
