"""Versioned threshold policies applied only after compatibility is established."""

from __future__ import annotations

import json
from enum import StrEnum
from pathlib import Path
from typing import Literal

from pydantic import Field, ValidationError, model_validator

from performance_lab.domain import ComparisonDimension

from .engine import (
    RegressionComparison,
    RegressionDimensionResult,
    RegressionDimensionState,
    RegressionMetricResult,
    RegressionModel,
    ThresholdState,
)

REGRESSION_POLICY_SCHEMA_VERSION: Literal[1] = 1


class RegressionPolicyError(ValueError):
    pass


class MetricDirection(StrEnum):
    AUTO = "auto"
    HIGHER_IS_BETTER = "higher_is_better"
    LOWER_IS_BETTER = "lower_is_better"


class RegressionDecision(StrEnum):
    PASS = "pass"
    FAIL = "fail"
    NOT_COMPARABLE = "not_comparable"
    NOT_EVALUATED = "not_evaluated"


class MetricThresholdRule(RegressionModel):
    rule_id: str = Field(min_length=1)
    dimension: ComparisonDimension
    metric: str = Field(min_length=1)
    direction: MetricDirection = MetricDirection.AUTO
    max_absolute_regression: float | None = Field(default=None, ge=0)
    max_relative_regression_pct: float | None = Field(default=None, ge=0)

    @model_validator(mode="after")
    def require_threshold(self) -> MetricThresholdRule:
        if self.max_absolute_regression is None and self.max_relative_regression_pct is None:
            raise ValueError("at least one regression threshold is required")
        return self


class RegressionPolicy(RegressionModel):
    schema_version: Literal[1] = REGRESSION_POLICY_SCHEMA_VERSION
    policy_id: str = Field(min_length=1)
    policy_version: str = Field(min_length=1)
    rules: tuple[MetricThresholdRule, ...]

    @model_validator(mode="after")
    def require_unique_rules(self) -> RegressionPolicy:
        if not self.rules:
            raise ValueError("regression policy requires at least one rule")
        ids = [rule.rule_id for rule in self.rules]
        if len(ids) != len(set(ids)):
            raise ValueError("regression policy rule ids must be unique")
        targets = [(rule.dimension, rule.metric) for rule in self.rules]
        if len(targets) != len(set(targets)):
            raise ValueError("only one regression rule may target a dimension/metric pair")
        return self


class RegressionRuleEvaluation(RegressionModel):
    rule_id: str = Field(min_length=1)
    dimension: ComparisonDimension
    metric: str = Field(min_length=1)
    state: ThresholdState
    reason: str


class RegressionPolicyEvaluation(RegressionModel):
    policy_id: str = Field(min_length=1)
    policy_version: str = Field(min_length=1)
    decision: RegressionDecision
    comparison: RegressionComparison
    rule_results: tuple[RegressionRuleEvaluation, ...]


def load_regression_policy(path: Path) -> RegressionPolicy:
    try:
        raw: object = json.loads(path.read_text(encoding="utf-8"))
    except OSError as exc:
        raise RegressionPolicyError(f"cannot read regression policy: {path}") from exc
    except json.JSONDecodeError as exc:
        raise RegressionPolicyError("regression policy is not valid JSON") from exc
    if not isinstance(raw, dict):
        raise RegressionPolicyError("regression policy must be a JSON object")
    if raw.get("schema_version") != REGRESSION_POLICY_SCHEMA_VERSION:
        raise RegressionPolicyError(
            f"unsupported regression policy schema_version={raw.get('schema_version')!r}; "
            f"expected {REGRESSION_POLICY_SCHEMA_VERSION}"
        )
    try:
        return RegressionPolicy.model_validate(raw)
    except ValidationError as exc:
        raise RegressionPolicyError(str(exc)) from exc


def apply_regression_policy(
    comparison: RegressionComparison,
    policy: RegressionPolicy,
) -> RegressionPolicyEvaluation:
    """Apply exact-match threshold rules without overriding compatibility semantics."""

    rules = {(rule.dimension, rule.metric): rule for rule in policy.rules}
    dimensions = tuple(_evaluate_dimension(dimension, rules) for dimension in comparison.dimensions)
    evaluated_comparison = comparison.model_copy(update={"dimensions": dimensions})
    rule_results = tuple(_evaluate_rule(evaluated_comparison, rule) for rule in policy.rules)
    return RegressionPolicyEvaluation(
        policy_id=policy.policy_id,
        policy_version=policy.policy_version,
        decision=_overall_decision(rule_results),
        comparison=evaluated_comparison,
        rule_results=rule_results,
    )


def _evaluate_dimension(
    dimension: RegressionDimensionResult,
    rules: dict[tuple[ComparisonDimension, str], MetricThresholdRule],
) -> RegressionDimensionResult:
    if dimension.state == RegressionDimensionState.NOT_COMPARABLE:
        return dimension
    metrics = tuple(
        _evaluate_metric(metric, rules.get((dimension.dimension, metric.delta.metric)))
        for metric in dimension.metrics
    )
    return dimension.model_copy(update={"metrics": metrics})


def _evaluate_metric(
    metric: RegressionMetricResult,
    rule: MetricThresholdRule | None,
) -> RegressionMetricResult:
    if rule is None:
        return metric
    direction = _resolve_direction(metric, rule)
    if direction is None:
        return metric.model_copy(
            update={
                "threshold_state": ThresholdState.NOT_EVALUATED,
                "threshold_reason": "metric direction is unknown; policy must set it explicitly",
            }
        )

    absolute_regression = _regression_amount(metric.delta.absolute_delta, direction)
    relative_regression = (
        _regression_amount(metric.delta.relative_delta_pct, direction)
        if metric.delta.relative_delta_pct is not None
        else None
    )
    failures: list[str] = []
    if (
        rule.max_absolute_regression is not None
        and absolute_regression > rule.max_absolute_regression
    ):
        failures.append(
            f"absolute regression {absolute_regression:g} exceeds "
            f"{rule.max_absolute_regression:g}"
        )
    if rule.max_relative_regression_pct is not None:
        if relative_regression is None:
            return metric.model_copy(
                update={
                    "threshold_state": ThresholdState.NOT_EVALUATED,
                    "threshold_reason": "relative threshold requested but baseline value is zero",
                }
            )
        if relative_regression > rule.max_relative_regression_pct:
            failures.append(
                f"relative regression {relative_regression:g}% exceeds "
                f"{rule.max_relative_regression_pct:g}%"
            )
    if failures:
        return metric.model_copy(
            update={
                "threshold_state": ThresholdState.FAIL,
                "threshold_reason": "; ".join(failures),
            }
        )
    return metric.model_copy(
        update={
            "threshold_state": ThresholdState.PASS,
            "threshold_reason": "regression is within configured tolerance",
        }
    )


def _resolve_direction(
    metric: RegressionMetricResult,
    rule: MetricThresholdRule,
) -> MetricDirection | None:
    if rule.direction != MetricDirection.AUTO:
        return rule.direction
    if metric.delta.higher_is_better is True:
        return MetricDirection.HIGHER_IS_BETTER
    if metric.delta.higher_is_better is False:
        return MetricDirection.LOWER_IS_BETTER
    return None


def _regression_amount(delta: float, direction: MetricDirection) -> float:
    if direction == MetricDirection.HIGHER_IS_BETTER:
        return max(0.0, -delta)
    if direction == MetricDirection.LOWER_IS_BETTER:
        return max(0.0, delta)
    raise AssertionError("AUTO direction must be resolved before threshold evaluation")


def _evaluate_rule(
    comparison: RegressionComparison,
    rule: MetricThresholdRule,
) -> RegressionRuleEvaluation:
    dimension = comparison.dimension(rule.dimension)
    if dimension.state == RegressionDimensionState.NOT_COMPARABLE:
        return RegressionRuleEvaluation(
            rule_id=rule.rule_id,
            dimension=rule.dimension,
            metric=rule.metric,
            state=ThresholdState.NOT_COMPARABLE,
            reason="target dimension is not comparable",
        )
    metric = next((item for item in dimension.metrics if item.delta.metric == rule.metric), None)
    if metric is None:
        return RegressionRuleEvaluation(
            rule_id=rule.rule_id,
            dimension=rule.dimension,
            metric=rule.metric,
            state=ThresholdState.NOT_EVALUATED,
            reason="target metric is unavailable in the compatible comparison",
        )
    return RegressionRuleEvaluation(
        rule_id=rule.rule_id,
        dimension=rule.dimension,
        metric=rule.metric,
        state=metric.threshold_state,
        reason=metric.threshold_reason,
    )


def _overall_decision(results: tuple[RegressionRuleEvaluation, ...]) -> RegressionDecision:
    states = {result.state for result in results}
    if ThresholdState.NOT_COMPARABLE in states:
        return RegressionDecision.NOT_COMPARABLE
    if ThresholdState.FAIL in states:
        return RegressionDecision.FAIL
    if ThresholdState.NOT_EVALUATED in states:
        return RegressionDecision.NOT_EVALUATED
    return RegressionDecision.PASS
