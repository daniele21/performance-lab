import type { ReactNode } from "react";

type StatusTone = "neutral" | "success" | "warning" | "error" | "unknown";

interface StatusProps {
  children: ReactNode;
  tone?: StatusTone;
}

export function Status({ children, tone = "neutral" }: StatusProps) {
  return (
    <span className="status" data-tone={tone}>
      <span className="status__indicator" aria-hidden="true" />
      <span>{children}</span>
    </span>
  );
}
