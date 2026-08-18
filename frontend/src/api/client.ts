import type {
  ComparisonReadModel,
  RunDetailReadModel,
  RunPreflightReadModel,
  RunPreflightRequest,
  RunSummaryReadModel,
  ScenarioSummaryReadModel,
  TargetSummaryReadModel,
  TestedModelReadModel,
} from "./types";

export class ApiError extends Error {
  readonly status: number;

  constructor(status: number, message: string) {
    super(message);
    this.name = "ApiError";
    this.status = status;
  }
}

interface RequestOptions {
  signal?: AbortSignal;
}

async function readError(response: Response): Promise<string> {
  try {
    const payload = (await response.json()) as { detail?: unknown };
    if (typeof payload.detail === "string" && payload.detail.trim()) return payload.detail;
  } catch {
    // Fall through to the stable status-based message.
  }
  return `Performance Lab API request failed (${response.status})`;
}

async function requestJson<T>(
  path: string,
  init: RequestInit,
  options: RequestOptions = {},
): Promise<T> {
  const response = await fetch(path, {
    ...init,
    headers: { Accept: "application/json", ...init.headers },
    signal: options.signal,
  });
  if (!response.ok) throw new ApiError(response.status, await readError(response));
  return (await response.json()) as T;
}

async function getJson<T>(path: string, options: RequestOptions = {}): Promise<T> {
  return requestJson<T>(path, { method: "GET" }, options);
}

async function postJson<Request, Response>(
  path: string,
  body: Request,
  options: RequestOptions = {},
): Promise<Response> {
  return requestJson<Response>(
    path,
    {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    },
    options,
  );
}

export function listTestedModels(options?: RequestOptions) {
  return getJson<TestedModelReadModel[]>("/api/v1/tested-models", options);
}

export function listRuns(
  { offset = 0, limit = 50 }: { offset?: number; limit?: number } = {},
  options?: RequestOptions,
) {
  const query = new URLSearchParams({ offset: String(offset), limit: String(limit) });
  return getJson<RunSummaryReadModel[]>(`/api/v1/runs?${query.toString()}`, options);
}

export function getRun(runId: string, options?: RequestOptions) {
  return getJson<RunDetailReadModel>(`/api/v1/runs/${encodeURIComponent(runId)}`, options);
}

export function listTargets(options?: RequestOptions) {
  return getJson<TargetSummaryReadModel[]>("/api/v1/targets", options);
}

export function listScenarios(options?: RequestOptions) {
  return getJson<ScenarioSummaryReadModel[]>("/api/v1/scenarios", options);
}

export function preflightRun(request: RunPreflightRequest, options?: RequestOptions) {
  return postJson<RunPreflightRequest, RunPreflightReadModel>(
    "/api/v1/run-preflight",
    request,
    options,
  );
}

export function compareRuns(
  baselineRunId: string,
  candidateRunId: string,
  options?: RequestOptions,
) {
  const query = new URLSearchParams({
    baseline_run_id: baselineRunId,
    candidate_run_id: candidateRunId,
  });
  return getJson<ComparisonReadModel>(`/api/v1/comparisons?${query.toString()}`, options);
}
