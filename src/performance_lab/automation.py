"""Stable machine-readable regression gate contract for CI and automation."""

from __future__ import annotations

from enum import IntEnum
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from performance_lab.regression import (
    BaselineRegressionEngine,
    RegressionDecision,
    RegressionPolicyEvaluation,
    apply_regression_policy,
    bind_baseline,
    load_regression_policy,
)
from performance_lab.storage import SQLiteRunStore

AUTOMATION_SCHEMA_VERSION: Literal[1] = 1


class AutomationExitCode(IntEnum):
    PASS = 0
    FAIL = 1
    ERROR = 2
    NOT_COMPARABLE = 3
    NOT_EVALUATED = 4


class AutomationModel(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")


class RegressionGateReport(AutomationModel):
    schema_version: Literal[1] = AUTOMATION_SCHEMA_VERSION
    decision: RegressionDecision
    baseline_run_id: str = Field(min_length=1)
    baseline_fingerprint_id: str = Field(min_length=1)
    candidate_run_id: str = Field(min_length=1)
    candidate_fingerprint_id: str = Field(min_length=1)
    policy_id: str = Field(min_length=1)
    policy_version: str = Field(min_length=1)
    evaluation: RegressionPolicyEvaluation


class AutomationErrorReport(AutomationModel):
    schema_version: Literal[1] = AUTOMATION_SCHEMA_VERSION
    decision: Literal["error"] = "error"
    error_type: str = Field(min_length=1)
    message: str = Field(min_length=1)


def evaluate_regression_gate(
    *,
    store_path: Path,
    baseline_run_id: str,
    candidate_run_id: str,
    policy_path: Path,
    baseline_id: str | None = None,
) -> RegressionGateReport:
    """Evaluate an explicit baseline/candidate pair and return a stable v1 report."""

    store = SQLiteRunStore(store_path)
    baseline = bind_baseline(
        store,
        baseline_id=baseline_id or f"automation:{baseline_run_id}",
        run_id=baseline_run_id,
    )
    comparison = BaselineRegressionEngine(store).compare(baseline, candidate_run_id)
    policy = load_regression_policy(policy_path)
    evaluation = apply_regression_policy(comparison, policy)
    return RegressionGateReport(
        decision=evaluation.decision,
        baseline_run_id=baseline.run_id,
        baseline_fingerprint_id=baseline.fingerprint_id,
        candidate_run_id=comparison.candidate_run_id,
        candidate_fingerprint_id=comparison.candidate_fingerprint_id,
        policy_id=policy.policy_id,
        policy_version=policy.policy_version,
        evaluation=evaluation,
    )


def exit_code_for_decision(decision: RegressionDecision) -> AutomationExitCode:
    return {
        RegressionDecision.PASS: AutomationExitCode.PASS,
        RegressionDecision.FAIL: AutomationExitCode.FAIL,
        RegressionDecision.NOT_COMPARABLE: AutomationExitCode.NOT_COMPARABLE,
        RegressionDecision.NOT_EVALUATED: AutomationExitCode.NOT_EVALUATED,
    }[decision]
