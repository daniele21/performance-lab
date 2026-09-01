import { expect, test, type Page, type Route } from "@playwright/test";

const API = { api_version: "v1", read_model_version: 1 } as const;
const NOW = "2026-08-31T08:00:00Z";
const DIGEST = "a".repeat(64);

const identity = {
  ...API,
  model_id: "llama-3.2-3b-instruct-q4",
  revision: "r1",
  quantization: "Q4_K_M",
  artifact_digest: "sha256:visual-fixture",
  target_id: "local-target",
  endpoint_identity: "loopback-fixture",
  runtime_name: "llama.cpp",
  runtime_version: "b7000",
  hardware_device_id: "device-a",
  hardware_device_class: "laptop",
};

function metric(
  metricId: string,
  label: string,
  dimension: "quality" | "performance" | "resources",
  value: number,
  unit: string | null,
  higherIsBetter: boolean,
) {
  return {
    ...API,
    metric_id: metricId,
    label,
    dimension,
    availability: "available",
    value,
    unit,
    higher_is_better: higherIsBetter,
    provenance: "visual-fixture",
    protocol_version: "1",
  };
}

const quality = metric("accuracy|exact@1", "Exact match", "quality", 0.91, null, true);
const performance = metric(
  "tokens_per_second",
  "Tokens / second",
  "performance",
  24.8,
  "tok/s",
  true,
);
const resources = metric("peak_rss_mb", "Peak RSS", "resources", 1680, "MB", false);

function runSummary(runId: string, modelId = identity.model_id) {
  return {
    ...API,
    run_id: runId,
    status: "succeeded",
    created_at: NOW,
    completed_at: "2026-08-31T08:01:00Z",
    suite_id: "general-diagnostic-starter",
    suite_version: "1",
    fingerprint_id: `fp-${runId}`,
    identity: { ...identity, model_id: modelId },
    metrics: [quality, performance, resources],
  };
}

const testedModels = [
  {
    ...API,
    cohort_key: "llama-q4-device-a",
    identity,
    run_count: 4,
    latest_run_id: "run-a",
    latest_completed_at: "2026-08-31T08:01:00Z",
    latest_metrics: [quality, performance, resources],
  },
  {
    ...API,
    cohort_key: "qwen-q4-device-a",
    identity: { ...identity, model_id: "qwen2.5-3b-instruct-q4" },
    run_count: 3,
    latest_run_id: "run-b",
    latest_completed_at: "2026-08-31T07:48:00Z",
    latest_metrics: [
      { ...quality, value: 0.86 },
      { ...performance, value: 28.2 },
      { ...resources, value: 1510 },
    ],
  },
];

const target = {
  ...API,
  target_id: "local-target",
  display_name: "Local device",
  adapter_type: "openai-compatible",
  endpoint_profile_id: "loopback",
  endpoint_identity: "loopback-fixture",
  capabilities: ["streaming", "text_generation"],
};

const scenario = {
  ...API,
  scenario: "general_capability",
  title: "General capability",
  description: "Balanced authored diagnostics across representative quality tasks.",
  supported: true,
  blocked_reason: null,
  suite_id: "general-diagnostic-starter",
};

const runPreflight = {
  ...API,
  can_run: true,
  issues: [],
  preview: {
    ...API,
    scenario: "general_capability",
    config: {
      target_id: "local-target",
      endpoint_identity: "loopback-fixture",
      endpoint: { profile_id: "loopback", base_url: "http://127.0.0.1:9/v1" },
      model_id: identity.model_id,
      output_dir: "results",
      store_path: ".performance-lab/runs.sqlite3",
      run_id: null,
      write_bundle: true,
      evidence_mode: "evidence_rich",
      use_host_telemetry: false,
      suite_id: "general-diagnostic-starter",
    },
    config_digest: DIGEST,
    target,
    suite: {
      ...API,
      suite_id: "general-diagnostic-starter",
      suite_version: "1",
      task_count: 3,
      task_ids: ["instruction-following", "factual-qa", "reasoning"],
    },
    datasets: [
      {
        ...API,
        dataset_id: "visual-fixture-dataset",
        dataset_version: "1",
        source: "visual-fixture",
        split: "test",
        sample_count: 12,
        selection_policy: "frozen",
        content_sha256: "b".repeat(64),
      },
    ],
    evaluator_ids: ["exact-match@1", "json-schema@1"],
    generation: { temperature: 0, max_output_tokens: 128 },
    load_profile: {},
    prompt_template_version: "1",
    benchmark_protocol_version: "1",
    identity_resolution: "resolved_at_launch",
  },
};

const dataset = {
  ...API,
  dataset_id: "dataset-a",
  dataset_version: "snapshot-1",
  source: "performance-lab-authored",
  split: "test",
  sample_count: 3,
  selection_policy: "frozen",
  content_sha256: "c".repeat(64),
};

const evaluator = {
  ...API,
  evaluator_id: "exact-match",
  version: "1",
  evaluator_type: "exact_match",
  deterministic: true,
  explanation_supported: false,
  rule_summary: "Normalize text and compare exact equality.",
  configuration: {},
};

const benchmarkCase = {
  ...API,
  case_id: "case-a",
  task_id: "reasoning",
  sample_id: "sample-a",
  dataset_id: "dataset-a",
  dataset_version: "snapshot-1",
  input: "A is above B. Is B above A?",
  expected: "No",
  evaluator_id: "exact-match",
  evaluator_version: "1",
  metric_names: ["accuracy"],
};

const benchmarkDetail = {
  ...API,
  summary: {
    ...API,
    suite_id: "general-diagnostic-starter",
    suite_version: "1",
    task_count: 1,
    task_ids: ["reasoning"],
  },
  generation: { temperature: 0, max_output_tokens: 128 },
  tasks: [
    {
      ...API,
      task_id: "reasoning",
      dataset_snapshot_id: "dataset-a:snapshot-1",
      dataset,
      evaluator,
      metric_names: ["accuracy"],
      sample_limit: null,
      case_count: 1,
      case_content_available: true,
    },
  ],
  cases: [benchmarkCase],
  definition_issues: [],
};

const sampleEvidence = {
  ...API,
  run: runSummary("run-a"),
  fingerprint: {
    fingerprint_id: "fp-run-a",
    target_id: "local-target",
    benchmark_protocol_version: "1",
  },
  sample: {
    ...API,
    run_id: "run-a",
    task_id: "reasoning",
    sample_id: "sample-a",
    attempt: 1,
    status: "succeeded",
    started_at: NOW,
    completed_at: "2026-08-31T08:00:01Z",
    elapsed_ms: 842.4,
    elapsed_provenance: "sample_execution_timestamps",
    input_tokens: 18,
    output_tokens: 3,
    score_count: 1,
    measurement_count: 1,
    error: null,
  },
  benchmark_case: benchmarkCase,
  prompt: {
    ...API,
    state: "retained",
    content: "Answer the reasoning question concisely. A is above B. Is B above A?",
    reason: null,
  },
  response: {
    ...API,
    state: "retained",
    content: "No",
    reason: null,
  },
  quality: {
    ...API,
    verdict: "correct",
    metric: "accuracy",
    value: 1,
    percentage: 100,
  },
  scores: [
    {
      ...API,
      metric: "accuracy",
      value: 1,
      evaluator_id: "exact-match",
      evaluator_version: "1",
      higher_is_better: true,
      numerator: 1,
      denominator: 1,
      evaluator_rule_summary: evaluator.rule_summary,
      explanation_state: "unavailable",
      explanation: null,
    },
  ],
  measurements: [
    {
      ...API,
      name: "latency_ms",
      value: 842.4,
      unit: "ms",
      scope: "sample",
      provenance: "client",
      protocol_version: "latency-v1",
      observed_at: null,
    },
  ],
  definition_issues: [],
};

const policy = {
  ...API,
  policy_id: "strict-quality-dominance",
  policy_version: "1.0.0",
  title: "Strict quality dominance",
  method: "strict_quality_dominance",
  description: "Recommend only when one candidate strictly dominates comparable quality evidence.",
  no_hidden_weights: true,
};

const campaign = {
  ...API,
  campaign_id: "campaign-visual",
  plan_digest: DIGEST,
  use_case_id: "general-capability",
  use_case_version: "1",
  target_id: "local-target",
  suite_id: "general-diagnostic-starter",
  suite_version: "1",
  status: "succeeded",
  revision: 5,
  created_at: NOW,
  updated_at: "2026-08-31T08:03:00Z",
  completed_at: "2026-08-31T08:03:00Z",
  entries: [
    {
      ...API,
      entry_id: "entry-a",
      candidate_id: "candidate-a",
      model_id: identity.model_id,
      config_digest: "d".repeat(64),
      status: "succeeded",
      run_id: "run-a",
      completed_samples: 12,
      total_samples: 12,
      error_code: null,
      error_message: null,
      identity,
      metrics: [quality, performance, resources],
    },
    {
      ...API,
      entry_id: "entry-b",
      candidate_id: "candidate-b",
      model_id: "qwen2.5-3b-instruct-q4",
      config_digest: "e".repeat(64),
      status: "succeeded",
      run_id: "run-b",
      completed_samples: 12,
      total_samples: 12,
      error_code: null,
      error_message: null,
      identity: { ...identity, model_id: "qwen2.5-3b-instruct-q4" },
      metrics: [
        { ...quality, value: 0.86 },
        { ...performance, value: 28.2 },
        { ...resources, value: 1510 },
      ],
    },
  ],
  results: {
    ...API,
    state: "ready",
    decision_policy: policy,
    compatibility: [
      { ...API, dimension: "capability", comparable: true, evidence_available: true, reasons: [] },
      { ...API, dimension: "runtime", comparable: true, evidence_available: true, reasons: [] },
      { ...API, dimension: "resource", comparable: true, evidence_available: true, reasons: [] },
    ],
    recommendation: {
      ...API,
      candidate_id: "candidate-a",
      run_id: "run-a",
      model_id: identity.model_id,
      rationale: "Best comparable quality evidence under the explicit strict-dominance policy.",
    },
    recommendation_reason:
      "Best comparable quality evidence under the explicit strict-dominance policy.",
  },
  error_code: null,
  error_message: null,
};

const campaignCases = [
  {
    ...API,
    task_id: "reasoning",
    sample_id: "sample-a",
    case_id: "reasoning:sample-a",
    candidate_count: 2,
    available_candidate_count: 2,
  },
];

async function fulfillJson(route: Route, payload: unknown, status = 200) {
  await route.fulfill({ status, contentType: "application/json", body: JSON.stringify(payload) });
}

async function installFixture(page: Page) {
  await page.route("**/api/v1/**", async (route) => {
    const request = route.request();
    const path = new URL(request.url()).pathname;

    if (path === "/api/v1/tested-models") return fulfillJson(route, testedModels);
    if (path === "/api/v1/runs" && request.method() === "GET") {
      return fulfillJson(route, [
        runSummary("run-a"),
        runSummary("run-b", "qwen2.5-3b-instruct-q4"),
      ]);
    }
    if (path === "/api/v1/targets") return fulfillJson(route, [target]);
    if (path === "/api/v1/scenarios") return fulfillJson(route, [scenario]);
    if (path === "/api/v1/run-preflight" && request.method() === "POST") {
      return fulfillJson(route, runPreflight);
    }
    if (path === "/api/v1/benchmarks/general-diagnostic-starter/1") {
      return fulfillJson(route, benchmarkDetail);
    }
    if (path === "/api/v1/runs/run-a/samples/reasoning/sample-a/1") {
      return fulfillJson(route, sampleEvidence);
    }
    if (path === "/api/v1/campaigns/campaign-visual") return fulfillJson(route, campaign);
    if (path === "/api/v1/campaigns/campaign-visual/cases") {
      return fulfillJson(route, campaignCases);
    }

    return fulfillJson(
      route,
      { detail: `Unhandled visual acceptance fixture: ${request.method()} ${path}` },
      500,
    );
  });
}

async function matchGolden(page: Page, name: string) {
  await expect(page).toHaveScreenshot(`${name}.png`, {
    animations: "disabled",
    caret: "hide",
  });
}

test.use({
  viewport: { width: 1536, height: 960 },
  locale: "en-US",
  timezoneId: "UTC",
  reducedMotion: "reduce",
  colorScheme: "dark",
});

test("UXUI-10: stable target-backed surfaces match accepted implementation goldens", async ({
  page,
}) => {
  await installFixture(page);

  await page.goto("/#overview");
  await expect(page.getByRole("heading", { name: "Your tested models" })).toBeVisible();
  await expect(page.getByRole("table", { name: "Tested model evidence" })).toBeVisible();
  await matchGolden(page, "overview");

  await page.goto("/#test-a-model");
  await page.getByLabel("Model ID").fill(identity.model_id);
  await page.getByRole("button", { name: "Continue" }).click();
  await page.getByRole("button", { name: "Continue" }).click();
  await page.getByRole("button", { name: "Continue" }).click();
  await expect(page.getByText("Preflight passed")).toBeVisible();
  await matchGolden(page, "test-a-model-review");

  await page.goto("/#benchmarks/general-diagnostic-starter/1");
  await expect(page.getByRole("heading", { name: "general-diagnostic-starter" })).toBeVisible();
  const caseDisclosure = page.locator("details").filter({ hasText: "case-a" }).first();
  await caseDisclosure.locator("summary").click();
  await expect(
    caseDisclosure.getByText("Normalize text and compare exact equality."),
  ).toBeVisible();
  await matchGolden(page, "benchmark-detail");

  await page.goto("/#runs/run-a/samples/reasoning/sample-a/1");
  await expect(page.getByRole("heading", { name: "sample-a" })).toBeVisible();
  await expect(page.getByText("Quality", { exact: true })).toBeVisible();
  await expect(page.getByText("Correct", { exact: true })).toBeVisible();
  await expect(page.getByText("Evaluation explanation unavailable")).toBeVisible();
  await matchGolden(page, "sample-evidence-detail");

  await page.goto("/#campaigns/campaign-visual");
  await expect(page.getByRole("heading", { name: "Results" })).toBeVisible();
  await page.locator(".campaign-results").evaluate((element) => {
    element.scrollIntoView({ block: "start" });
  });
  await matchGolden(page, "campaign-results");
});