import type { ReactNode } from "react";

import type { EvidenceState, MetricDimension } from "../design/tokens";

interface MetricProps {
  label: string;
  value?: number | string | null;
  unit?: string;
  dimension: MetricDimension;
  availability?: EvidenceState;
}

const STATE_LABELS: Record<Exclude<EvidenceState, "available">, string> = {
  unknown: "Unknown",
  unavailable: "Unavailable",
  not_evaluated: "Not evaluated",
  partial: "Partial evidence",
};

export function Metric({ label, value, unit, dimension, availability = "available" }: MetricProps) {
  let displayValue = "Unknown";
  if (availability !== "available") {
    displayValue = STATE_LABELS[availability];
  } else if (value !== null && value !== undefined) {
    displayValue = `${value}${unit ? ` ${unit}` : ""}`;
  }

  return (
    <div className="metric" data-dimension={dimension} data-availability={availability}>
      <span className="metric__label">{label}</span>
      <strong className="metric__value">{displayValue}</strong>
    </div>
  );
}

interface MetricGroupProps {
  label: string;
  children: ReactNode;
}

export function MetricGroup({ label, children }: MetricGroupProps) {
  return (
    <section className="metric-group" aria-label={label}>
      {children}
    </section>
  );
}
