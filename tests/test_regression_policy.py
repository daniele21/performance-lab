from datetime import UTC, datetime

from performance_lab.domain import ComparisonDimension, CompatibilityResult
from performance_lab.regression import (
    BaselineBinding,
    MetricDirection,
    MetricThresholdRule,
    RegressionComparison,
    RegressionDecision,
    RegressionDimensionResult,
    RegressionDimensionState,
    RegressionMetricResult,
    RegressionPolicy,
    ThresholdState,
    apply_regression_policy,
    load_regression_policy,
)
from performance_lab.storage import MetricDelta


def comparison(
    *,
    dimension: ComparisonDimension = ComparisonDimension.CAPABILITY,
    metric: str = "accuracy|exact-match@1",
    absolute_delta: float = -0.1,
    relative_delta_pct: float | None = -10.0,
    higher_is_better: bool | None = True,
    comparable: bool = True,
) -> RegressionComparison:
    compatibility = CompatibilityResult(dimension=dimension, comparable=comparable)
    metric_results = (
        (
            RegressionMetricResult(
                delta=MetricDelta(
                    metric=metric,
                    baseline_value=1.0,
                    candidate_value=1.0 + absolute_delta,
                    absolute_delta=absolute_delta,
                    relative_delta_pct=relative_delta_pct,
                    higher_is_better=higher_is_better,
                )
            ),
        )
        if comparable
        else ()
    )
    return RegressionComparison(
        baseline=BaselineBinding(
            baseline_id="baseline",
            run_id="run-a",
            fingerprint_id="fp-a",
            selected_at=datetime.now(UTC),
        ),
        candidate_run_id="run-b",
        candidate_fingerprint_id="fp-b",
        identity_differences=(),
        dimensions=(
            RegressionDimensionResult(
                dimension=dimension,
                state=(
                    RegressionDimensionState.COMPARABLE
                    if comparable
                    else RegressionDimensionState.NOT_COMPARABLE
                ),
                compatibility=compatibility,
                metrics=metric_results,
            ),
        ),
    )


def test_higher_is_better_metric_fails_when_regression_exceeds_tolerance() -> None:
    policy = RegressionPolicy(
        policy_id="release-gate",
        policy_version="1",
        rules=(
            MetricThresholdRule(
                rule_id="accuracy",
                dimension=ComparisonDimension.CAPABILITY,
                metric="accuracy|exact-match@1",
                max_absolute_regression=0.05,
            ),
        ),
    )

    result = apply_regression_policy(comparison(), policy)

    assert result.decision == RegressionDecision.FAIL
    metric = result.comparison.dimension(ComparisonDimension.CAPABILITY).metrics[0]
    assert metric.threshold_state == ThresholdState.FAIL
    assert "exceeds" in metric.threshold_reason


def test_lower_is_better_runtime_metric_passes_with_explicit_direction() -> None:
    runtime_metric = "ttft_ms|client|single-request-v1|ms"
    policy = RegressionPolicy(
        policy_id="runtime-gate",
        policy_version="1",
        rules=(
            MetricThresholdRule(
                rule_id="ttft",
                dimension=ComparisonDimension.RUNTIME,
                metric=runtime_metric,
                direction=MetricDirection.LOWER_IS_BETTER,
                max_absolute_regression=10.0,
            ),
        ),
    )

    result = apply_regression_policy(
        comparison(
            dimension=ComparisonDimension.RUNTIME,
            metric=runtime_metric,
            absolute_delta=5.0,
            relative_delta_pct=5.0,
            higher_is_better=None,
        ),
        policy,
    )

    assert result.decision == RegressionDecision.PASS
    assert result.rule_results[0].state == ThresholdState.PASS


def test_unknown_direction_is_not_evaluated_instead_of_assumed() -> None:
    runtime_metric = "throughput|client|load-v1|requests/s"
    policy = RegressionPolicy(
        policy_id="runtime-gate",
        policy_version="1",
        rules=(
            MetricThresholdRule(
                rule_id="throughput",
                dimension=ComparisonDimension.RUNTIME,
                metric=runtime_metric,
                max_relative_regression_pct=5.0,
            ),
        ),
    )

    result = apply_regression_policy(
        comparison(
            dimension=ComparisonDimension.RUNTIME,
            metric=runtime_metric,
            higher_is_better=None,
        ),
        policy,
    )

    assert result.decision == RegressionDecision.NOT_EVALUATED
    assert result.rule_results[0].state == ThresholdState.NOT_EVALUATED


def test_incompatible_target_dimension_wins_before_threshold_evaluation() -> None:
    policy = RegressionPolicy(
        policy_id="release-gate",
        policy_version="1",
        rules=(
            MetricThresholdRule(
                rule_id="accuracy",
                dimension=ComparisonDimension.CAPABILITY,
                metric="accuracy|exact-match@1",
                max_absolute_regression=0.05,
            ),
        ),
    )

    result = apply_regression_policy(comparison(comparable=False), policy)

    assert result.decision == RegressionDecision.NOT_COMPARABLE
    assert result.rule_results[0].state == ThresholdState.NOT_COMPARABLE


def test_versioned_policy_round_trips_from_json(tmp_path) -> None:
    path = tmp_path / "policy.json"
    expected = RegressionPolicy(
        policy_id="release-gate",
        policy_version="2026-08-15",
        rules=(
            MetricThresholdRule(
                rule_id="accuracy",
                dimension=ComparisonDimension.CAPABILITY,
                metric="accuracy|exact-match@1",
                max_relative_regression_pct=2.0,
            ),
        ),
    )
    path.write_text(expected.model_dump_json(indent=2), encoding="utf-8")

    assert load_regression_policy(path) == expected
