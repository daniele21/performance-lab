export type ApiVersion = "v1";
export type ReadModelVersion = 1;

export interface UIModelIdentity {
  api_version: ApiVersion;
  read_model_version: ReadModelVersion;
}

export type EvidenceAvailability = "available" | "unknown" | "unavailable" | "not_evaluated";
export type MetricDimension = "quality" | "performance" | "resources";
export type RunStatus = "planned" | "running" | "succeeded" | "failed" | "cancelled";
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
