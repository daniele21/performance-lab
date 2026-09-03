import type {
  DatasetSummaryReadModel,
  GenerationParameterDomainReadModel,
  SuiteSummaryReadModel,
  TargetSummaryReadModel,
  UIModelIdentity,
} from "./types";

export type CampaignSearchStrategy = "fixed" | "quick" | "standard" | "thorough" | "custom";

export interface UseCaseReadModel extends UIModelIdentity {
  use_case_id: string;
  version: string;
  title: string;
  description: string;
  task_family: string;
  suite_id: string;
  suite_version: string;
  source: "starter" | "workload_pack";
}

export interface CandidateModelReadModel extends UIModelIdentity {
  candidate_id: string;
  target_id: string;
  model_id: string;
  revision: string | null;
  artifact_digest: string | null;
  quantization: string | null;
  runtime_name: string | null;
  runtime_version: string | null;
  runtime_config_digest: string | null;
  generation_parameter_domains: GenerationParameterDomainReadModel[];
  source: "configured" | "discovered";
}

export interface ConfigurationSearchOptionReadModel extends UIModelIdentity {
  strategy: CampaignSearchStrategy;
  title: string;
  description: string;
  available: boolean;
  blocked_reason: string | null;
}

export interface CampaignTargetPlanningReadModel extends UIModelIdentity {
  target: TargetSummaryReadModel;
  hardware_device_id: string | null;
  hardware_device_class: string | null;
  candidates: CandidateModelReadModel[];
  supported_generation_parameters: string[];
  bounded_generation_parameter_ranges: string[];
  configuration_search_options: ConfigurationSearchOptionReadModel[];
}

export interface CampaignPlanningContextReadModel extends UIModelIdentity {
  use_cases: UseCaseReadModel[];
  targets: CampaignTargetPlanningReadModel[];
}

export interface CampaignPlanPreviewRequest {
  use_case_id: string;
  target_id: string;
  candidate_ids: string[];
  configuration_strategy: CampaignSearchStrategy;
}

export interface CampaignPlanIssueReadModel extends UIModelIdentity {
  code: string;
  message: string;
  field: string | null;
}

export interface ConfigurationSearchPlanReadModel extends UIModelIdentity {
  strategy: CampaignSearchStrategy;
  title: string;
  configuration_count_per_candidate: number;
  base_generation: Record<string, unknown>;
  bounded_parameter_ranges: string[];
  note: string;
}

export interface BenchmarkPlanReadModel extends UIModelIdentity {
  suite: SuiteSummaryReadModel;
  datasets: DatasetSummaryReadModel[];
  evaluator_ids: string[];
  case_count_per_run: number;
}

export interface CampaignEstimateReadModel extends UIModelIdentity {
  candidate_count: number;
  configuration_count_per_candidate: number;
  planned_run_count: number;
  benchmark_case_count_per_run: number;
  estimated_request_count: number;
  estimated_duration_seconds: number | null;
  duration_reason: string;
}

export interface DecisionPolicyReadModel extends UIModelIdentity {
  policy_id: string;
  policy_version: string;
  title: string;
  method: "strict_quality_dominance";
  description: string;
  no_hidden_weights: true;
}

export interface CampaignPlanPreviewReadModel extends UIModelIdentity {
  can_plan: boolean;
  issues: CampaignPlanIssueReadModel[];
  plan_digest: string | null;
  use_case: UseCaseReadModel | null;
  target: TargetSummaryReadModel | null;
  candidates: CandidateModelReadModel[];
  configuration_search: ConfigurationSearchPlanReadModel | null;
  benchmark_plan: BenchmarkPlanReadModel | null;
  estimate: CampaignEstimateReadModel | null;
  decision_policy: DecisionPolicyReadModel | null;
  execution_available: boolean;
  execution_blocked_reason: string | null;
}
