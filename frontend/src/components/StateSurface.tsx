import type { ReactNode } from "react";

type StateKind = "empty" | "loading" | "error";

interface StateSurfaceProps {
  kind: StateKind;
  title: string;
  description: string;
  action?: ReactNode;
}

const KIND_LABELS: Record<StateKind, string> = {
  empty: "Empty",
  loading: "Loading",
  error: "Error",
};

export function StateSurface({ kind, title, description, action }: StateSurfaceProps) {
  return (
    <section
      className="state-surface"
      data-kind={kind}
      aria-live={kind === "loading" ? "polite" : undefined}
    >
      <p className="state-surface__kind">{KIND_LABELS[kind]}</p>
      <h2>{title}</h2>
      <p>{description}</p>
      {action ? <div className="state-surface__action">{action}</div> : null}
    </section>
  );
}
