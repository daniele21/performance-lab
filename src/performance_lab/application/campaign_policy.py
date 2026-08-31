"""Versioned campaign recommendation policy over immutable comparable Run evidence."""

from __future__ import annotations

from dataclasses import dataclass

from performance_lab.domain import ComparisonDimension, Run, compare_fingerprints

from .planning_models import DecisionPolicyReadModel

STRICT_QUALITY_DOMINANCE_POLICY_ID = "strict-quality-dominance"
STRICT_QUALITY_DOMINANCE_POLICY_VERSION = "1.0.0"


@dataclass(frozen=True, slots=True)
class RecommendationDecision:
    candidate_id: str | None
    run_id: str | None
    reason: str


def decision_policy_read_model() -> DecisionPolicyReadModel:
    return DecisionPolicyReadModel(
        policy_id=STRICT_QUALITY_DOMINANCE_POLICY_ID,
        policy_version=STRICT_QUALITY_DOMINANCE_POLICY_VERSION,
        title="Strict quality dominance",
        description=(
            "Recommend a candidate only when comparable quality evidence shows it is no worse "
            "on every reported quality metric and strictly better on at least one metric against "
            "every alternative. Otherwise report the trade-off without inventing a weighted score."
        ),
    )


def recommend_strict_quality_dominance(
    candidates: tuple[tuple[str, Run], ...],
) -> RecommendationDecision:
    """Return a recommendation only for a unique strict quality-dominating candidate.

    No metric weights, normalization or tie-break rules are hidden inside this policy. Runtime and
    resource evidence remain separate result dimensions and do not become an opaque combined score.
    """

    if len(candidates) < 2:
        return RecommendationDecision(
            candidate_id=None,
            run_id=None,
            reason="At least two completed candidates are required for a comparative recommendation.",
        )

    baseline = candidates[0][1]
    for _, run in candidates[1:]:
        compatibility = compare_fingerprints(
            baseline.fingerprint,
            run.fingerprint,
            ComparisonDimension.CAPABILITY,
        )
        if not compatibility.comparable:
            return RecommendationDecision(
                candidate_id=None,
                run_id=None,
                reason=(
                    "Quality evidence is not comparable across every candidate, so the decision "
                    "policy does not rank them."
                ),
            )

    metrics = tuple(_quality_metrics(run) for _, run in candidates)
    metric_keys = set(metrics[0])
    if not metric_keys:
        return RecommendationDecision(
            candidate_id=None,
            run_id=None,
            reason="No aggregate quality metrics are available for recommendation.",
        )
    if any(set(item) != metric_keys for item in metrics[1:]):
        return RecommendationDecision(
            candidate_id=None,
            run_id=None,
            reason=(
                "Candidates do not expose the same aggregate quality metrics, so no weighted or "
                "partial ranking is inferred."
            ),
        )
    for key in metric_keys:
        directions = {item[key][1] for item in metrics}
        if len(directions) != 1:
            return RecommendationDecision(
                candidate_id=None,
                run_id=None,
                reason=f"Quality metric direction is inconsistent across candidates: {key}",
            )

    dominant: list[int] = []
    for candidate_index, candidate_metrics in enumerate(metrics):
        if all(
            _dominates(candidate_metrics, other_metrics)
            for other_index, other_metrics in enumerate(metrics)
            if other_index != candidate_index
        ):
            dominant.append(candidate_index)

    if len(dominant) != 1:
        return RecommendationDecision(
            candidate_id=None,
            run_id=None,
            reason=(
                "No single candidate strictly dominates every alternative across the comparable "
                "quality metrics. Inspect the separate trade-offs instead."
            ),
        )

    index = dominant[0]
    candidate_id, run = candidates[index]
    return RecommendationDecision(
        candidate_id=candidate_id,
        run_id=run.run_id,
        reason=(
            "This candidate is no worse on every comparable quality metric and strictly better "
            "on at least one metric against every alternative."
        ),
    )


def _quality_metrics(run: Run) -> dict[str, tuple[float, bool]]:
    return {
        f"{score.metric}|{score.evaluator.evaluator_id}@{score.evaluator.version}": (
            score.value,
            score.higher_is_better,
        )
        for score in run.aggregate_scores
    }


def _dominates(
    candidate: dict[str, tuple[float, bool]],
    other: dict[str, tuple[float, bool]],
) -> bool:
    no_worse = True
    strictly_better = False
    for key, (candidate_value, higher_is_better) in candidate.items():
        other_value = other[key][0]
        if higher_is_better:
            if candidate_value < other_value:
                no_worse = False
                break
            if candidate_value > other_value:
                strictly_better = True
        else:
            if candidate_value > other_value:
                no_worse = False
                break
            if candidate_value < other_value:
                strictly_better = True
    return no_worse and strictly_better
