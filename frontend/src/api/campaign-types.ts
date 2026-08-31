import type { DecisionPolicyReadModel, CampaignPlanPreviewRequest } from "./planning-types";
import type { IdentitySummary, MetricReadModel, UIModelIdentity } from "./types";

export type CampaignStatus =
  | "queued"
  | "running"
  | "cancelling"
  | "succeeded"
  | "failed"
  | "cancelled"
  | "interrupted";

export type CampaignEntryStatus =
  | "queued"
  | "running"
  | "succeeded"
  | "failed"
  | "cancelled"
  | "interrupted";

export type CampaignComparisonDimension = "capability" | "runtime" | "resource";

export interface CampaignCompatibilityReasonReadModel extends UIModelIdentity {
  baseline_run_id: string;
  candidate_run_id: string;
  code: string;
  field: string;
  message: string;
}

export interface CampaignDimensionReadModel extends UIModelIdentity {
  dimension: CampaignComparisonDimension;
  comparable: boolean;
  evidence_available: boolean;
  reasons: CampaignCompatibilityReasonReadModel[];
}

export interface CampaignRecommendationReadModel extends UIModelIdentity {
  candidate_id: string;
  run_id: string;
  model_id: string;
  rationale: string;
}

export interface CampaignResultsReadModel extends UIModelIdentity {
  state: "pending" | "ready" | "partial";
  decision_policy: DecisionPolicyReadModel;
  compatibility: CampaignDimensionReadModel[];
  recommendation: CampaignRecommendationReadModel | null;
  recommendation_reason: string;
}

export interface CampaignEntryReadModel extends UIModelIdentity {
  entry_id: string;
  candidate_id: string;
  model_id: string;
  config_digest: string;
  status: CampaignEntryStatus;
  run_id: string | null;
  completed_samples: number;
  total_samples: number;
  error_code: string | null;
  error_message: string | null;
  identity: IdentitySummary | null;
  metrics: MetricReadModel[];
}

export interface CampaignReadModel extends UIModelIdentity {
  campaign_id: string;
  plan_digest: string;
  use_case_id: string;
  use_case_version: string;
  target_id: string;
  suite_id: string;
  suite_version: string;
  status: CampaignStatus;
  revision: number;
  created_at: string;
  updated_at: string;
  completed_at: string | null;
  entries: CampaignEntryReadModel[];
  results: CampaignResultsReadModel;
  error_code: string | null;
  error_message: string | null;
}

export interface CampaignLaunchRequest {
  plan: CampaignPlanPreviewRequest;
  plan_digest: string;
}
