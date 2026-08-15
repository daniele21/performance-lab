"""CI-specific regression gate semantics and artifact rendering."""

from __future__ import annotations

from pathlib import Path
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from performance_lab.automation import RegressionGateReport
from performance_lab.domain import ComparisonDimension
from performance_lab.regression import RegressionDecision, ThresholdState

CI_REPORT_SCHEMA_VERSION: Literal[1] = 1


class CiModel(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")


class CiRuleResult(CiModel):
    rule_id: str = Field(min_length=1)
    dimension: ComparisonDimension
    metric: str = Field(min_length=1)
    policy_state: ThresholdState
    effective_state: ThresholdState
    reason: str = Field(min_length=1)


class CiRegressionReport(CiModel):
    schema_version: Literal[1] = CI_REPORT_SCHEMA_VERSION
    decision: RegressionDecision
    runner_identity_controlled: bool
    resource_hardware_comparability_trusted: bool
    regression: RegressionGateReport
    rule_results: tuple[CiRuleResult, ...]


def build_ci_regression_report(
    regression: RegressionGateReport,
    *,
    runner_identity_controlled: bool = False,
) -> CiRegressionReport:
    """Apply conservative CI runner semantics on top of the regression policy result."""

    results = tuple(
        _ci_rule_result(rule, runner_identity_controlled=runner_identity_controlled)
        for rule in regression.evaluation.rule_results
    )
    decision = _overall_decision(tuple(result.effective_state for result in results))
    return CiRegressionReport(
        decision=decision,
        runner_identity_controlled=runner_identity_controlled,
        resource_hardware_comparability_trusted=runner_identity_controlled,
        regression=regression,
        rule_results=results,
    )


def render_ci_summary(report: CiRegressionReport) -> str:
    """Render a concise Markdown summary suitable for GITHUB_STEP_SUMMARY."""

    lines = [
        f"## Performance Lab regression gate — {report.decision.value.upper()}",
        "",
        f"- Baseline: `{report.regression.baseline_run_id}`",
        f"- Candidate: `{report.regression.candidate_run_id}`",
        f"- Policy: `{report.regression.policy_id}@{report.regression.policy_version}`",
    ]
    if report.runner_identity_controlled:
        lines.append("- CI runner hardware identity: controlled; resource rules may be evaluated.")
    else:
        lines.append(
            "- CI runner hardware identity: uncontrolled; "
            "resource rules are forced to NOT_COMPARABLE."
        )

    lines.extend(
        [
            "",
            "| Rule | Dimension | Metric | Result | Reason |",
            "| --- | --- | --- | --- | --- |",
        ]
    )
    for rule in report.rule_results:
        reason = rule.reason.replace("|", "\\|").replace("\n", " ")
        lines.append(
            f"| `{rule.rule_id}` | {rule.dimension.value} | `{rule.metric}` | "
            f"**{rule.effective_state.value}** | {reason} |"
        )

    identity_count = len(report.regression.evaluation.comparison.identity_differences)
    lines.extend(["", f"Identity differences recorded: **{identity_count}**."])
    return "\n".join(lines) + "\n"


def write_ci_artifact(report: CiRegressionReport, destination: Path) -> Path:
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(report.model_dump_json(indent=2) + "\n", encoding="utf-8")
    return destination


def append_ci_summary(report: CiRegressionReport, destination: Path) -> Path:
    destination.parent.mkdir(parents=True, exist_ok=True)
    with destination.open("a", encoding="utf-8") as handle:
        handle.write(render_ci_summary(report))
    return destination


def _ci_rule_result(rule: object, *, runner_identity_controlled: bool) -> CiRuleResult:
    from performance_lab.regression import RegressionRuleEvaluation

    if not isinstance(rule, RegressionRuleEvaluation):
        raise TypeError("expected RegressionRuleEvaluation")
    if rule.dimension == ComparisonDimension.RESOURCE and not runner_identity_controlled:
        return CiRuleResult(
            rule_id=rule.rule_id,
            dimension=rule.dimension,
            metric=rule.metric,
            policy_state=rule.state,
            effective_state=ThresholdState.NOT_COMPARABLE,
            reason="CI runner hardware identity is not declared controlled",
        )
    return CiRuleResult(
        rule_id=rule.rule_id,
        dimension=rule.dimension,
        metric=rule.metric,
        policy_state=rule.state,
        effective_state=rule.state,
        reason=rule.reason,
    )


def _overall_decision(states: tuple[ThresholdState, ...]) -> RegressionDecision:
    state_set = set(states)
    if ThresholdState.NOT_COMPARABLE in state_set:
        return RegressionDecision.NOT_COMPARABLE
    if ThresholdState.FAIL in state_set:
        return RegressionDecision.FAIL
    if ThresholdState.NOT_EVALUATED in state_set:
        return RegressionDecision.NOT_EVALUATED
    return RegressionDecision.PASS
