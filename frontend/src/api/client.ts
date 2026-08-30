import type {
  CampaignPlanPreviewReadModel,
  CampaignPlanPreviewRequest,
  CampaignPlanningContextReadModel,
} from "./planning-types";
import type {
  BaselineSummaryReadModel,
  BenchmarkDetailReadModel,
  ComparisonReadModel,
  DatasetSummaryReadModel,
  EndpointConnectionInput,
  EndpointProbeReadModel,
  EvaluatorDefinitionReadModel,
  PolicySummaryReadModel,
  RunDetailReadModel,
  RunJobSnapshot,
  RunLaunchRequest,
  RunPreflightReadModel,
  RunPreflightRequest,
  RunSummaryReadModel,
  SampleEvidenceDetailReadModel,
  SampleSummaryReadModel,
  ScenarioSummaryReadModel,
  SuiteSummaryReadModel,
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
    if (Array.isArray(payload.detail)) {
      const messages = payload.detail.filter(
        (item): item is string => typeof item === "string" && Boolean(item.trim()),
      );
      if (messages.length) return messages.join(" · ");
    }
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

export function listRunSamples(runId: string, options?: RequestOptions) {
  return getJson<SampleSummaryReadModel[]>(
    `/api/v1/runs/${encodeURIComponent(runId)}/samples`,
    options,
  );
}

export function getSampleEvidence(
  runId: string,
  taskId: string,
  sampleId: string,
  attempt: number,
  options?: RequestOptions,
) {
  const segments = [runId, taskId, sampleId].map(encodeURIComponent);
  return getJson<SampleEvidenceDetailReadModel>(
    `/api/v1/runs/${segments[0]}/samples/${segments[1]}/${segments[2]}/${attempt}`,
    options,
  );
}

export function listTargets(options?: RequestOptions) {
  return getJson<TargetSummaryReadModel[]>("/api/v1/targets", options);
}

export function probeEndpoint(connection: EndpointConnectionInput, options?: RequestOptions) {
  return postJson<EndpointConnectionInput, EndpointProbeReadModel>(
    "/api/v1/endpoint-probes",
    connection,
    options,
  );
}

export function getCampaignPlanning(options?: RequestOptions) {
  return getJson<CampaignPlanningContextReadModel>("/api/v1/campaign-planning", options);
}

export function previewCampaignPlan(request: CampaignPlanPreviewRequest, options?: RequestOptions) {
  return postJson<CampaignPlanPreviewRequest, CampaignPlanPreviewReadModel>(
    "/api/v1/campaign-plan-preview",
    request,
    options,
  );
}

export function listSuites(options?: RequestOptions) {
  return getJson<SuiteSummaryReadModel[]>("/api/v1/suites", options);
}

export function listBenchmarks(options?: RequestOptions) {
  return getJson<SuiteSummaryReadModel[]>("/api/v1/benchmarks", options);
}

export function getBenchmark(suiteId: string, suiteVersion: string, options?: RequestOptions) {
  return getJson<BenchmarkDetailReadModel>(
    `/api/v1/benchmarks/${encodeURIComponent(suiteId)}/${encodeURIComponent(suiteVersion)}`,
    options,
  );
}

export function listDatasets(options?: RequestOptions) {
  return getJson<DatasetSummaryReadModel[]>("/api/v1/datasets", options);
}

export function listEvaluators(options?: RequestOptions) {
  return getJson<EvaluatorDefinitionReadModel[]>("/api/v1/evaluators", options);
}

export function listBaselines(options?: RequestOptions) {
  return getJson<BaselineSummaryReadModel[]>("/api/v1/baselines", options);
}

export function listRegressionPolicies(options?: RequestOptions) {
  return getJson<PolicySummaryReadModel[]>("/api/v1/regression-policies", options);
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

export function launchRunJob(request: RunLaunchRequest, options?: RequestOptions) {
  return postJson<RunLaunchRequest, RunJobSnapshot>("/api/v1/run-jobs", request, options);
}

export function getRunJob(jobId: string, options?: RequestOptions) {
  return getJson<RunJobSnapshot>(`/api/v1/run-jobs/${encodeURIComponent(jobId)}`, options);
}

export function cancelRunJob(jobId: string, options?: RequestOptions) {
  return postJson<Record<string, never>, RunJobSnapshot>(
    `/api/v1/run-jobs/${encodeURIComponent(jobId)}/cancel`,
    {},
    options,
  );
}

const TERMINAL_JOB_STATES = new Set<RunJobSnapshot["state"]>([
  "succeeded",
  "failed",
  "cancelled",
  "interrupted",
]);

interface RunJobSubscription {
  afterRevision?: number;
  onSnapshot: (snapshot: RunJobSnapshot) => void;
  onDisconnect?: () => void;
  onMalformedEvent?: () => void;
}

export function subscribeRunJob(jobId: string, subscription: RunJobSubscription) {
  const query = new URLSearchParams({
    after_revision: String(subscription.afterRevision ?? -1),
  });
  const source = new EventSource(
    `/api/v1/run-jobs/${encodeURIComponent(jobId)}/events?${query.toString()}`,
  );
  const handleSnapshot = (event: Event) => {
    const message = event as MessageEvent<string>;
    try {
      const snapshot = JSON.parse(message.data) as RunJobSnapshot;
      subscription.onSnapshot(snapshot);
      if (TERMINAL_JOB_STATES.has(snapshot.state)) source.close();
    } catch {
      subscription.onMalformedEvent?.();
    }
  };

  source.addEventListener("run_job", handleSnapshot);
  source.onerror = () => subscription.onDisconnect?.();
  return () => source.close();
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
