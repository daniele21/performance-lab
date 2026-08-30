export type AppRoute =
  | { kind: "overview" }
  | { kind: "best-setup" }
  | { kind: "runs" }
  | { kind: "run-detail"; runId: string }
  | { kind: "test-model" }
  | { kind: "live-run"; jobId: string }
  | { kind: "compare"; runId?: string }
  | {
      kind: "library";
      section: "benchmarks" | "datasets" | "evaluators" | "baselines" | "regression-policies";
    }
  | { kind: "settings"; section: "model-connections" | "devices-targets" | "advanced" }
  | { kind: "not-found"; path: string };

export function parseHash(hash: string): AppRoute {
  const raw = hash.startsWith("#") ? hash.slice(1) : hash;
  if (!raw || raw === "overview") return { kind: "overview" };
  if (raw === "find-best-setup") return { kind: "best-setup" };
  if (raw === "runs") return { kind: "runs" };
  if (raw === "test-a-model") return { kind: "test-model" };

  if (raw.startsWith("live-run/")) {
    const encodedJobId = raw.slice("live-run/".length);
    if (!encodedJobId) return { kind: "not-found", path: raw };
    try {
      return { kind: "live-run", jobId: decodeURIComponent(encodedJobId) };
    } catch {
      return { kind: "not-found", path: raw };
    }
  }

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

  if (raw === "benchmarks" || raw === "test-suites") {
    return { kind: "library", section: "benchmarks" };
  }
  if (
    raw === "datasets" ||
    raw === "evaluators" ||
    raw === "baselines" ||
    raw === "regression-policies"
  ) {
    return { kind: "library", section: raw };
  }

  if (raw === "model-connections" || raw === "endpoints") {
    return { kind: "settings", section: "model-connections" };
  }
  if (raw === "devices-targets" || raw === "advanced") {
    return { kind: "settings", section: raw };
  }

  return { kind: "not-found", path: raw };
}

export function navigate(hash: string) {
  window.location.hash = hash.startsWith("#") ? hash : `#${hash}`;
}
