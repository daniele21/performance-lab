"""Policy-backed regression projection layered on the canonical UI query stack."""

from __future__ import annotations

from performance_lab.regression import BaselineRegressionEngine, apply_regression_policy, bind_baseline

from .execution_policy_queries import UIQueryService as ExecutionPolicyUIQueryService
from .regression_models import RegressionEvaluationReadModel, RegressionRuleReadModel


class UIQueryService(ExecutionPolicyUIQueryService):
    """Expose explicit policy-backed regression without duplicating regression semantics."""

    def evaluate_regression(
        self,
        *,
        baseline_run_id: str,
        candidate_run_id: str,
        policy_id: str,
        policy_version: str,
    ) -> RegressionEvaluationReadModel:
        if baseline_run_id == candidate_run_id:
            raise ValueError("baseline and candidate must be different completed runs")

        policy = next(
            (
                item
                for item in self.policies
                if item.policy_id == policy_id and item.policy_version == policy_version
            ),
            None,
        )
        if policy is None:
            raise LookupError(f"regression policy not configured: {policy_id}@{policy_version}")

        baseline = bind_baseline(
            self.store,
            baseline_id=f"ui:{baseline_run_id}",
            run_id=baseline_run_id,
        )
        regression = BaselineRegressionEngine(self.store).compare(baseline, candidate_run_id)
        evaluation = apply_regression_policy(regression, policy)

        return RegressionEvaluationReadModel(
            baseline_run_id=baseline.run_id,
            baseline_fingerprint_id=baseline.fingerprint_id,
            candidate_run_id=regression.candidate_run_id,
            candidate_fingerprint_id=regression.candidate_fingerprint_id,
            policy_id=policy.policy_id,
            policy_version=policy.policy_version,
            decision=evaluation.decision,
            rule_results=tuple(
                RegressionRuleReadModel(
                    rule_id=result.rule_id,
                    dimension=result.dimension,
                    metric=result.metric,
                    state=result.state,
                    reason=result.reason,
                )
                for result in evaluation.rule_results
            ),
            comparison=self.compare(baseline_run_id, candidate_run_id),
        )
