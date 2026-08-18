export const BRAND_CONTRACT_VERSION = "0.4.0" as const;

export const COLOR_TOKENS = {
  surface: "#0B0F14",
  surface_elevated: "#111820",
  surface_subtle: "#151E27",
  text_primary: "#F8FAFC",
  text_secondary: "#94A3B8",
  primary: "#00E5FF",
  secondary: "#7B5CFF",
  quality: "#22D3EE",
  performance: "#8B5CF6",
  resources: "#38BDF8",
  success: "#22C55E",
  warning: "#F59E0B",
  error: "#EF4444",
  evidence_unknown: "#64748B",
  evidence_unavailable: "#475569",
  border: "#24303C",
  focus: "#67E8F9",
} as const;

export type ColorTokenName = keyof typeof COLOR_TOKENS;

export const METRIC_DIMENSIONS = ["quality", "performance", "resources"] as const;
export type MetricDimension = (typeof METRIC_DIMENSIONS)[number];

export const EVIDENCE_STATES = [
  "available",
  "unknown",
  "unavailable",
  "not_evaluated",
  "partial",
] as const;
export type EvidenceState = (typeof EVIDENCE_STATES)[number];
