export type ApiVersion = "v1";
export type ReadModelVersion = 1;

export interface UIModelIdentity {
  api_version: ApiVersion;
  read_model_version: ReadModelVersion;
}

export type EvidenceAvailability = "available" | "unknown" | "unavailable" | "not_evaluated";
export type EvidenceContentState = "retained" | "not_retained" | "unavailable";
export type EvidenceMode = "aggregate_safe" | "evidence_rich";
export type ExplanationState = "available" | "unavailable";
export type MetricDimension = "quality" | "performance" | "resources";
export type RunStatus = "planned" | "running" | "succeeded" | "failed" | "cancelled";
export type SampleStatus = "succeeded" | "failed" | "cancelled";
export type SampleQualityVerdict = "correct" | "incorrect" | "partial" | "scored" | "not_evaluated";
export type ScenarioKind = "general_capability" | "my_workload" | "performance" | "regression";
export type RunJobState =
  "starting" | "running" | "cancelling" | "succeeded" | "failed" | "cancelled" | "interrupted";

export interface MetricReadModel extends UIModelIdentity {
  metric_id: string;
  label: string;
  dimension: MetricDimension;
  availability: EvidenceAvailability;
  value: number | null;
  unit: string | null;
  higher_is_better: boolean | null;
  provenance: string | null;
  protocol_version: string | null;
}

export interface IdentitySummary extends UIModelIdentity {
  model_id: string;
  revision: string | null;
  quantization: string | null;
  artifact_digest: string | null;
  target_id: string;
  endpoint_identity: string;
  runtime_name: string | null;
  runtime_version: string | null;
  hardware_device_id: string | null;
  hardware_device_class: string | null;
}

export interface RunSummaryReadModel extends UIModelIdentity {
  run_id: string;
  status: RunStatus;
  created_at: string;
  completed_at: string | null;
  suite_id: string;
  suite_version: string;
  fingerprint_id: string;
  identity: IdentitySummary;
  metrics: MetricReadModel[];
}

export interface ExecutionFingerprint {
  fingerprint_id: string;
  [key: string]: unknown;
}

export interface RunEvidenceReadModel extends UIModelIdentity {
  fingerprint: ExecutionFingerprint;
  dataset_count: number;
  evaluator_count: number;
  sample_count: number;
}

export interface RunDetailReadModel extends UIModelIdentity {
  summary: RunSummaryReadModel;
  evidence: RunEvidenceReadModel;
}

export interface TestedModelReadModel extends UIModelIdentity {
  cohort_key: string;
  identity: IdentitySummary;
  run_count: number;
  latest_run_id: string;
  latest_completed_at: string | null;
  latest_metrics: MetricReadModel[];
}

export interface TargetSummaryReadModel extends UIModelIdentity {
  target_id: string;
  display_name: string;
  adapter_type: string;
  endpoint_profile_id: string;
  endpoint_identity: string;
  capabilities: string[];
}

export interface EndpointConnectionInput {
  display_name: string;
  base_url: string;
  server_type: "openai_compatible" | "local_llm_server";
  timeout_seconds: number;
}

export interface CapabilitySupportReadModel extends UIModelIdentity {
  name: string;
  state: "supported" | "unsupported" | "unknown";
  source: "declared" | "observed" | "none";
  detail: string | null;
}

export interface RuntimeParameterReadModel extends UIModelIdentity {
  name: string;
  scope: "runtime_load";
  current_value: unknown;
  editable: false;
  provenance: "local_llm_server";
}

export interface DiscoveredModelReadModel extends UIModelIdentity {
  model_id: string;
  runtime_parameters: RuntimeParameterReadModel[];
}

export interface EndpointProbeReadModel extends UIModelIdentity {
  healthy: boolean;
  endpoint_identity: string;
  target: TargetSummaryReadModel | null;
  models: DiscoveredModelReadModel[];
  capabilities: CapabilitySupportReadModel[];
  supported_generation_parameters: string[];
  warning: string | null;
}

export interface DatasetSummaryReadModel extends UIModelIdentity {
  dataset_id: string;
  dataset_version: string;
  source: string;
  split: string;
  sample_count: number;
  selection_policy: string;
  content_sha256: string;
}

export interface SuiteSummaryReadModel extends UIModelIdentity {
  suite_id: string;
  suite_version: string;
  task_count: number;
  task_ids: string[];
}

export interface EvaluatorDefinitionReadModel extends UIModelIdentity {
  evaluator_id: string;
  version: string;
  evaluator_type: string;
  deterministic: boolean | null;
  explanation_supported: boolean | null;
  rule_summary: string | null;
  configuration: Record<string, unknown>;
}

export interface BenchmarkTaskReadModel extends UIModelIdentity {
  task_id: string;
  dataset_snapshot_id: string;
  dataset: DatasetSummaryReadModel | null;
  evaluator: EvaluatorDefinitionReadModel;
  metric_names: string[];
  sample_limit: number | null;
  case_count: number | null;
  case_content_available: boolean;
}

export interface BenchmarkCaseReadModel extends UIModelIdentity {
  case_id: string;
  task_id: string;
  sample_id: string;
  dataset_id: string;
  dataset_version: string;
  input: unknown;
  expected: unknown;
  evaluator_id: string;
  evaluator_version: string;
  metric_names: string[];
}

export interface BenchmarkDetailReadModel extends UIModelIdentity {
  summary: SuiteSummaryReadModel;
  generation: Record<string, unknown>;
  tasks: BenchmarkTaskReadModel[];
  cases: BenchmarkCaseReadModel[];
  definition_issues: string[];
}

export interface BaselineSummaryReadModel extends UIModelIdentity {
  baseline_id: string;
  run_id: string;
  fingerprint_id: string;
  selected_at: string;
  label: string | null;
}

export interface PolicySummaryReadModel extends UIModelIdentity {
  policy_id: string;
  policy_version: string;
  rule_count: number;
}

export interface ScenarioSummaryReadModel extends UIModelIdentity {
  scenario: ScenarioKind;
  title: string;
  description: string;
  supported: boolean;
  blocked_reason: string | null;
  suite_id: string | null;
}

export interface RunPreflightRequest {
  target_id: string;
  model_id: string;
  scenario: ScenarioKind;
  use_host_telemetry: boolean;
}

export interface PreflightIssueReadModel extends UIModelIdentity {
  code: string;
  message: string;
  field: string | null;
}

export interface StarterRunConfigTransport {
  target_id: string;
  endpoint_identity: string;
  endpoint: Record<string, unknown>;
  model_id: string;
  output_dir: string;
  store_path: string;
  run_id: string | null;
  write_bundle: boolean;
  evidence_mode: EvidenceMode;
  use_host_telemetry: boolean;
  suite_id: "general-diagnostic-starter";
  [key: string]: unknown;
}

export interface FrozenExecutionPreviewReadModel extends UIModelIdentity {
  scenario: ScenarioKind;
  config: StarterRunConfigTransport;
  config_digest: string;
  target: TargetSummaryReadModel;
  suite: SuiteSummaryReadModel;
  datasets: DatasetSummaryReadModel[];
  evaluator_ids: string[];
  generation: Record<string, unknown>;
  load_profile: Record<string, unknown>;
  prompt_template_version: string;
  benchmark_protocol_version: string;
  identity_resolution: "resolved_at_launch";
}

export interface RunPreflightReadModel extends UIModelIdentity {
  can_run: boolean;
  issues: PreflightIssueReadModel[];
  preview: FrozenExecutionPreviewReadModel | null;
}

export interface RunLaunchRequest {
  preflight: RunPreflightRequest;
  config_digest: string;
}

export interface RunJobSnapshot {
  api_version: ApiVersion;
  job_id: string;
  state: RunJobState;
  revision: number;
  created_at: string;
  updated_at: string;
  config_digest: string | null;
  target_id: string | null;
  model_id: string | null;
  scenario: string | null;
  phase: string | null;
  completed_samples: number;
  total_samples: number;
  run_id: string | null;
  run_status: RunStatus | null;
  error_code: string | null;
  error_message: string | null;
}

export interface SampleErrorInfo {
  code: string;
  category: string;
  retryable: boolean;
}

export interface SampleSummaryReadModel extends UIModelIdentity {
  run_id: string;
  task_id: string;
  sample_id: string;
  attempt: number;
  status: SampleStatus;
  started_at: string;
  completed_at: string;
  elapsed_ms: number;
  elapsed_provenance: "sample_execution_timestamps";
  input_tokens: number | null;
  output_tokens: number | null;
  score_count: number;
  measurement_count: number;
  error: SampleErrorInfo | null;
}

export interface EvidenceContentReadModel extends UIModelIdentity {
  state: EvidenceContentState;
  content: unknown | null;
  reason: string | null;
}

export interface SampleScoreReadModel extends UIModelIdentity {
  metric: string;
  value: number;
  evaluator_id: string;
  evaluator_version: string;
  higher_is_better: boolean;
  numerator: number | null;
  denominator: number | null;
  evaluator_rule_summary: string | null;
  explanation_state: ExplanationState;
  explanation: string | null;
}

export interface SampleQualitySummaryReadModel extends UIModelIdentity {
  verdict: SampleQualityVerdict;
  metric: string | null;
  value: number | null;
  percentage: number | null;
}

export interface SampleMeasurementReadModel extends UIModelIdentity {
  name: string;
  value: number;
  unit: string;
  scope: "sample" | "run";
  provenance: "client" | "host" | "runtime";
  protocol_version: string;
  observed_at: string | null;
}

export interface SampleEvidenceDetailReadModel extends UIModelIdentity {
  run: RunSummaryReadModel;
  fingerprint: ExecutionFingerprint;
  sample: SampleSummaryReadModel;
  benchmark_case: BenchmarkCaseReadModel | null;
  prompt: EvidenceContentReadModel;
  response: EvidenceContentReadModel;
  quality: SampleQualitySummaryReadModel;
  scores: SampleScoreReadModel[];
  measurements: SampleMeasurementReadModel[];
  definition_issues: string[];
}

export interface CompatibilityReasonReadModel extends UIModelIdentity {
  code: string;
  field: string;
  message: string;
  baseline: unknown;
  candidate: unknown;
}

export interface MetricDelta {
  metric: string;
  baseline_value: number;
  candidate_value: number;
  absolute_delta: number;
  relative_delta_pct: number | null;
  higher_is_better: boolean | null;
  unit: string | null;
}

export interface DimensionComparisonReadModel extends UIModelIdentity {
  dimension: "capability" | "runtime" | "resource";
  comparable: boolean;
  reasons: CompatibilityReasonReadModel[];
  deltas: MetricDelta[];
  missing_in_baseline: string[];
  missing_in_candidate: string[];
}

export interface IdentityDifference {
  path: string;
  baseline: unknown;
  candidate: unknown;
}

export interface ComparisonReadModel extends UIModelIdentity {
  baseline_run_id: string;
  candidate_run_id: string;
  identity_differences: IdentityDifference[];
  dimensions: DimensionComparisonReadModel[];
}
