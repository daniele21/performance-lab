import type { EvidenceState as EvidenceStateValue } from "../design/tokens";

interface EvidenceStateProps {
  state: EvidenceStateValue;
}

const LABELS: Record<EvidenceStateValue, string> = {
  available: "Available",
  unknown: "Unknown",
  unavailable: "Unavailable",
  not_evaluated: "Not evaluated",
  partial: "Partial evidence",
};

export function EvidenceState({ state }: EvidenceStateProps) {
  return (
    <span className="evidence-state" data-state={state}>
      <span className="evidence-state__indicator" aria-hidden="true" />
      {LABELS[state]}
    </span>
  );
}
