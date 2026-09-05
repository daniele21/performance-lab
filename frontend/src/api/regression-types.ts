import type { ComparisonReadModel, UIModelIdentity } from "./types";

export type RegressionDecision = "pass" | "fail" | "not_comparable" | "not_evaluated";
export type RegressionRuleState = "pass" | "fail" | "not_comparable" | "not_evaluated";

export interface RegressionRuleReadModel extends UIModelIdentity {
  rule_id: string;
  dimension: "capability" | "runtime" | "resource";
  metric: string;
  state: RegressionRuleState;
  reason: string;
}

export interface RegressionEvaluationReadModel extends UIModelIdentity {
  baseline_run_id: string;
  baseline_fingerprint_id: string;
  candidate_run_id: string;
  candidate_fingerprint_id: string;
  policy_id: string;
  policy_version: string;
  decision: RegressionDecision;
  rule_results: RegressionRuleReadModel[];
  comparison: ComparisonReadModel;
}
