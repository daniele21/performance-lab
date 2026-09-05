"""Stable browser projection for policy-backed regression evaluation."""

from __future__ import annotations

from pydantic import Field

from performance_lab.domain import ComparisonDimension
from performance_lab.regression import RegressionDecision, ThresholdState

from .ui_models import ComparisonReadModel, UIModel


class RegressionRuleReadModel(UIModel):
    rule_id: str = Field(min_length=1)
    dimension: ComparisonDimension
    metric: str = Field(min_length=1)
    state: ThresholdState
    reason: str = Field(min_length=1)


class RegressionEvaluationReadModel(UIModel):
    baseline_run_id: str = Field(min_length=1)
    baseline_fingerprint_id: str = Field(min_length=1)
    candidate_run_id: str = Field(min_length=1)
    candidate_fingerprint_id: str = Field(min_length=1)
    policy_id: str = Field(min_length=1)
    policy_version: str = Field(min_length=1)
    decision: RegressionDecision
    rule_results: tuple[RegressionRuleReadModel, ...]
    comparison: ComparisonReadModel
