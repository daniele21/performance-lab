import type { ReactNode } from "react";

interface DisclosureProps {
  summary: ReactNode;
  children: ReactNode;
  defaultOpen?: boolean;
}

export function Disclosure({ summary, children, defaultOpen = false }: DisclosureProps) {
  return (
    <details className="disclosure" open={defaultOpen || undefined}>
      <summary>{summary}</summary>
      <div className="disclosure__content">{children}</div>
    </details>
  );
}
