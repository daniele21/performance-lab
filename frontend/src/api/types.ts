export type ApiVersion = "v1";
export type ReadModelVersion = 1;

export interface UIModelIdentity {
  api_version: ApiVersion;
  read_model_version: ReadModelVersion;
}

export type EvidenceAvailability = "available" | "unknown" | "unavailable" | "not_evaluated";
export type MetricDimension = "quality" | "performance" | "resources";
export type RunStatus = "planned" | "running" | "succeeded" | "failed" | "cancelled";

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

export interface CompatibilityReasonReadModel extends UIModelIdentity {
  code: string;
  field: string;
  message: string;
  baseline: unknown;
  candidate: unknown;
}

export interface MetricDelta {
  metric_id: string;
  baseline: number;
  candidate: number;
  absolute_delta: number;
  relative_delta: number | null;
  higher_is_better: boolean | null;
  unit: string | null;
  [key: string]: unknown;
}

export interface DimensionComparisonReadModel extends UIModelIdentity {
  dimension: "quality" | "runtime" | "resources";
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
