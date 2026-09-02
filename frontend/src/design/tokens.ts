export const BRAND_CONTRACT_VERSION = "0.6.0" as const;

export const COLOR_TOKENS = {
  surface: "#F6F8FA",
  surface_elevated: "#FFFFFF",
  surface_subtle: "#EFF2F5",
  surface_raised: "#FFFFFF",
  text_primary: "#171A1F",
  text_secondary: "#5D6672",
  text_tertiary: "#818B98",
  primary: "#247F91",
  secondary: "#6959D9",
  quality: "#26899B",
  performance: "#7059D6",
  resources: "#3F78AD",
  success: "#217A55",
  warning: "#9A6317",
  error: "#C44754",
  evidence_unknown: "#707A86",
  evidence_unavailable: "#A2A9B2",
  border: "#D6DCE4",
  border_subtle: "#E6EAF0",
  border_strong: "#B9C2CE",
  focus: "#176F80",
} as const;

export const DARK_COLOR_TOKENS = {
  surface: "#080A0D",
  surface_elevated: "#0E1116",
  surface_subtle: "#141820",
  surface_raised: "#191E27",
  text_primary: "#F4F6F8",
  text_secondary: "#A0A8B2",
  text_tertiary: "#707A86",
  primary: "#7DD6E8",
  secondary: "#9A8CF7",
  quality: "#67D5E3",
  performance: "#A78BFA",
  resources: "#7AB8F5",
  success: "#4FD18B",
  warning: "#E9B44C",
  error: "#F06D78",
  evidence_unknown: "#6F7782",
  evidence_unavailable: "#484F58",
  border: "#222831",
  border_subtle: "#1A1F27",
  border_strong: "#303844",
  focus: "#9AE7F3",
} as const;

export const MOTION_TOKENS = {
  durations: {
    instant: "0ms",
    fast: "100ms",
    standard: "140ms",
    large: "220ms",
  },
  easing: {
    enter: "cubic-bezier(0.2, 0, 0, 1)",
    exit: "cubic-bezier(0.4, 0, 1, 1)",
    move: "cubic-bezier(0.2, 0, 0, 1)",
  },
  spring: {
    default: "n/a - restrained CSS transitions are canonical",
    bounce: "none for repeated product workflows",
  },
  reduced_motion_strategy:
    "remove non-essential transitions and spatial movement while preserving immediate state, focus and progress feedback",
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
