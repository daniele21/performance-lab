export type AppRoute =
  | { kind: "overview" }
  | { kind: "runs" }
  | { kind: "run-detail"; runId: string }
  | { kind: "test-model" }
  | { kind: "compare"; runId?: string }
  | { kind: "not-found"; path: string };

export function parseHash(hash: string): AppRoute {
  const raw = hash.startsWith("#") ? hash.slice(1) : hash;
  if (!raw || raw === "overview") return { kind: "overview" };
  if (raw === "runs") return { kind: "runs" };
  if (raw === "test-a-model") return { kind: "test-model" };

  if (raw.startsWith("runs/")) {
    const encodedRunId = raw.slice("runs/".length);
    if (!encodedRunId) return { kind: "runs" };
    try {
      return { kind: "run-detail", runId: decodeURIComponent(encodedRunId) };
    } catch {
      return { kind: "not-found", path: raw };
    }
  }

  if (raw === "compare") return { kind: "compare" };
  if (raw.startsWith("compare?")) {
    const query = new URLSearchParams(raw.slice("compare?".length));
    const runId = query.get("run") ?? undefined;
    return { kind: "compare", runId };
  }

  return { kind: "not-found", path: raw };
}

export function navigate(hash: string) {
  window.location.hash = hash.startsWith("#") ? hash : `#${hash}`;
}
