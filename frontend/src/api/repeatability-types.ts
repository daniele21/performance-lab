import type { MetricDimension, UIModelIdentity } from "./types";

export type RepeatabilityState = "available" | "insufficient_repeats" | "unavailable";

export interface RepeatabilityPercentileReadModel extends UIModelIdentity {
  percentile: number;
  value: number | null;
  sample_count: number;
  qualified: boolean;
  qualification: string | null;
}

export interface RepeatabilityDistributionReadModel extends UIModelIdentity {
  sample_count: number;
  minimum: number;
  maximum: number;
  mean: number;
  median: number;
  stddev: number;
  coefficient_of_variation: number | null;
  p90: RepeatabilityPercentileReadModel;
  p95: RepeatabilityPercentileReadModel;
}

export interface RepeatabilityRunValueReadModel extends UIModelIdentity {
  run_id: string;
  value: number;
  source_sample_count: number | null;
}

export interface RepeatabilityMetricReadModel extends UIModelIdentity {
  metric_id: string;
  label: string;
  dimension: Extract<MetricDimension, "quality" | "performance">;
  unit: string | null;
  higher_is_better: boolean | null;
  run_values: RepeatabilityRunValueReadModel[];
  distribution: RepeatabilityDistributionReadModel;
}

export interface RepeatabilityLoadProfile {
  concurrency: number;
  request_count: number;
  warmup_requests: number;
  streaming: boolean;
}

export interface RepeatabilityReadModel extends UIModelIdentity {
  anchor_run_id: string;
  fingerprint_id: string;
  state: RepeatabilityState;
  load_profile: RepeatabilityLoadProfile;
  run_ids: string[];
  run_count: number;
  succeeded_run_count: number;
  failed_run_count: number;
  cancelled_run_count: number;
  sample_attempt_count: number;
  succeeded_sample_count: number;
  failed_sample_count: number;
  cancelled_sample_count: number;
  metrics: RepeatabilityMetricReadModel[];
  note: string;
}
