export type AppRoute =
  | { kind: "overview" }
  | { kind: "best-setup" }
  | { kind: "campaign"; campaignId: string }
  | {
      kind: "campaign-case-comparison";
      campaignId: string;
      taskId: string;
      sampleId: string;
    }
  | { kind: "runs" }
  | { kind: "run-detail"; runId: string }
  | {
      kind: "sample-evidence";
      runId: string;
      taskId: string;
      sampleId: string;
      attempt: number;
    }
  | { kind: "test-model" }
  | { kind: "live-run"; jobId: string }
  | { kind: "compare"; runId?: string }
  | { kind: "benchmark-detail"; suiteId: string; suiteVersion: string }
  | {
      kind: "library";
      section: "benchmarks" | "datasets" | "evaluators" | "baselines" | "regression-policies";
    }
  | {
      kind: "settings";
      section: "model-connections" | "devices-targets" | "appearance" | "advanced";
    }
  | { kind: "not-found"; path: string };

function decodePathSegment(value: string) {
  return decodeURIComponent(value);
}

export function parseHash(hash: string): AppRoute {
  const raw = hash.startsWith("#") ? hash.slice(1) : hash;
  if (!raw || raw === "overview") return { kind: "overview" };
  if (raw === "find-best-setup") return { kind: "best-setup" };
  if (raw === "runs") return { kind: "runs" };
  if (raw === "test-a-model") return { kind: "test-model" };

  if (raw.startsWith("campaigns/")) {
    const parts = raw.split("/");
    if (parts.length === 5 && parts[2] === "cases") {
      try {
        return {
          kind: "campaign-case-comparison",
          campaignId: decodePathSegment(parts[1]),
          taskId: decodePathSegment(parts[3]),
          sampleId: decodePathSegment(parts[4]),
        };
      } catch {
        return { kind: "not-found", path: raw };
      }
    }
    if (parts.length !== 2 || !parts[1]) return { kind: "not-found", path: raw };
    try {
      return { kind: "campaign", campaignId: decodePathSegment(parts[1]) };
    } catch {
      return { kind: "not-found", path: raw };
    }
  }

  if (raw.startsWith("live-run/")) {
    const encodedJobId = raw.slice("live-run/".length);
    if (!encodedJobId) return { kind: "not-found", path: raw };
    try {
      return { kind: "live-run", jobId: decodePathSegment(encodedJobId) };
    } catch {
      return { kind: "not-found", path: raw };
    }
  }

  if (raw.startsWith("runs/")) {
    const parts = raw.split("/");
    if (parts.length === 6 && parts[2] === "samples") {
      const attempt = Number(parts[5]);
      if (!Number.isInteger(attempt) || attempt < 1) return { kind: "not-found", path: raw };
      try {
        return {
          kind: "sample-evidence",
          runId: decodePathSegment(parts[1]),
          taskId: decodePathSegment(parts[3]),
          sampleId: decodePathSegment(parts[4]),
          attempt,
        };
      } catch {
        return { kind: "not-found", path: raw };
      }
    }

    const encodedRunId = raw.slice("runs/".length);
    if (!encodedRunId) return { kind: "runs" };
    try {
      return { kind: "run-detail", runId: decodePathSegment(encodedRunId) };
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

  if (raw.startsWith("benchmarks/")) {
    const parts = raw.split("/");
    if (parts.length !== 3) return { kind: "not-found", path: raw };
    try {
      return {
        kind: "benchmark-detail",
        suiteId: decodePathSegment(parts[1]),
        suiteVersion: decodePathSegment(parts[2]),
      };
    } catch {
      return { kind: "not-found", path: raw };
    }
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
  if (raw === "devices-targets" || raw === "appearance" || raw === "advanced") {
    return { kind: "settings", section: raw };
  }

  return { kind: "not-found", path: raw };
}

export function navigate(hash: string) {
  window.location.hash = hash.startsWith("#") ? hash : `#${hash}`;
}
