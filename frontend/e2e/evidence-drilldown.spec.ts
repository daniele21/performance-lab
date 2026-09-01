import { expect, test, type Page, type Route } from "@playwright/test";

const API_IDENTITY = { api_version: "v1", read_model_version: 1 } as const;
const dataset = {
  ...API_IDENTITY,
  dataset_id: "dataset-a",
  dataset_version: "snapshot-1",
  source: "browser-fixture",
  split: "test",
  sample_count: 1,
  selection_policy: "frozen",
  content_sha256: "a".repeat(64),
};
const evaluator = {
  ...API_IDENTITY,
  evaluator_id: "exact-match",
  version: "1",
  evaluator_type: "exact_match",
  deterministic: true,
  explanation_supported: false,
  rule_summary: "Normalize text and compare exact equality.",
  configuration: {},
};
const benchmarkSummary = {
  ...API_IDENTITY,
  suite_id: "starter",
  suite_version: "1",
  task_count: 1,
  task_ids: ["task-a"],
};
const benchmarkCase = {
  ...API_IDENTITY,
  case_id: "case-a",
  task_id: "task-a",
  sample_id: "sample-a",
  dataset_id: "dataset-a",
  dataset_version: "snapshot-1",
  input: "Question?",
  expected: "Expected answer",
  evaluator_id: "exact-match",
  evaluator_version: "1",
  metric_names: ["accuracy"],
};
const benchmarkDetail = {
  ...API_IDENTITY,
  summary: benchmarkSummary,
  generation: { temperature: 0 },
  tasks: [
    {
      ...API_IDENTITY,
      task_id: "task-a",
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
const runSummary = {
  ...API_IDENTITY,
  run_id: "run-a",
  status: "succeeded",
  created_at: "2026-08-30T10:00:00Z",
  completed_at: "2026-08-30T10:00:01Z",
  suite_id: "starter",
  suite_version: "1",
  fingerprint_id: "fingerprint-a",
  identity: {
    ...API_IDENTITY,
    model_id: "model-a",
    revision: "r1",
    quantization: "Q4_K_M",
    artifact_digest: null,
    target_id: "local",
    endpoint_identity: "loopback",
    runtime_name: "llama.cpp",
    runtime_version: "1",
    hardware_device_id: "device-a",
    hardware_device_class: "cpu",
  },
  metrics: [],
};
const sample = {
  ...API_IDENTITY,
  run_id: "run-a",
  task_id: "task-a",
  sample_id: "sample-a",
  attempt: 1,
  status: "succeeded",
  started_at: "2026-08-30T10:00:00Z",
  completed_at: "2026-08-30T10:00:01Z",
  elapsed_ms: 1000,
  elapsed_provenance: "sample_execution_timestamps",
  input_tokens: 4,
  output_tokens: 2,
  score_count: 1,
  measurement_count: 1,
  error: null,
};
const sampleEvidence = {
  ...API_IDENTITY,
  run: runSummary,
  fingerprint: { fingerprint_id: "fingerprint-a", target_id: "local" },
  sample,
  benchmark_case: benchmarkCase,
  prompt: {
    ...API_IDENTITY,
    state: "retained",
    content: "Rendered prompt sent to model: Question?",
    reason: null,
  },
  response: {
    ...API_IDENTITY,
    state: "retained",
    content: "Expected answer",
    reason: null,
  },
  scores: [
    {
      ...API_IDENTITY,
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
      ...API_IDENTITY,
      name: "latency_ms",
      value: 1000,
      unit: "ms",
      scope: "sample",
      provenance: "client",
      protocol_version: "latency-v1",
      observed_at: null,
    },
  ],
  definition_issues: [],
};

async function fulfillJson(route: Route, payload: unknown, status = 200) {
  await route.fulfill({ status, contentType: "application/json", body: JSON.stringify(payload) });
}

async function installEvidenceFixture(page: Page) {
  await page.route("**/api/v1/benchmarks**", async (route) => {
    const pathname = new URL(route.request().url()).pathname;
    if (pathname === "/api/v1/benchmarks") {
      await fulfillJson(route, [benchmarkSummary]);
      return;
    }
    if (pathname === "/api/v1/benchmarks/starter/1") {
      await fulfillJson(route, benchmarkDetail);
      return;
    }
    await fulfillJson(route, { detail: "benchmark definition not found" }, 404);
  });

  await page.route("**/api/v1/runs/**", async (route) => {
    const pathname = new URL(route.request().url()).pathname;
    if (pathname === "/api/v1/runs/run-a") {
      await fulfillJson(route, {
        ...API_IDENTITY,
        summary: runSummary,
        evidence: {
          ...API_IDENTITY,
          fingerprint: { fingerprint_id: "fingerprint-a", target_id: "local" },
          dataset_count: 1,
          evaluator_count: 1,
          sample_count: 1,
        },
      });
      return;
    }
    if (pathname === "/api/v1/runs/run-a/samples") {
      await fulfillJson(route, [sample]);
      return;
    }
    if (pathname === "/api/v1/runs/run-a/samples/task-a/sample-a/1") {
      await fulfillJson(route, sampleEvidence);
      return;
    }
    await fulfillJson(route, { detail: "sample evidence not found" }, 404);
  });
}

test("J7: benchmark definition exposes inspectable cases and evaluator rules", async ({ page }) => {
  await installEvidenceFixture(page);
  await page.goto("/#benchmarks");

  await page.getByRole("link", { name: "starter" }).click();
  await expect(page.getByRole("heading", { name: "starter" })).toBeVisible();
  await expect(page.getByText("Benchmark definition", { exact: true })).toBeVisible();

  const caseDisclosure = page.locator("details").filter({
    has: page.getByText("case-a · task-a", { exact: true }),
  });
  await caseDisclosure.locator("summary").click();
  await expect(caseDisclosure.getByText("Question?", { exact: true })).toBeVisible();
  await expect(caseDisclosure.getByText("Expected answer", { exact: true })).toBeVisible();
  await expect(
    caseDisclosure.getByText("Normalize text and compare exact equality.", { exact: true }),
  ).toBeVisible();
  await expect(page.getByText("model-a")).toHaveCount(0);
});

test("J8: run samples expose the exact prompt, model output and expected output distinctly", async ({ page }) => {
  await installEvidenceFixture(page);
  await page.goto("/#runs/run-a");

  await expect(page.getByRole("heading", { name: "Samples" })).toBeVisible();
  await expect(page.getByRole("heading", { name: "sample-a" })).toBeVisible();
  await page.getByRole("link", { name: "Inspect sample evidence" }).click();

  await expect(page.getByRole("heading", { name: "sample-a" })).toBeVisible();
  await expect(page.getByText("Prompt sent to model", { exact: true })).toBeVisible();
  await expect(page.getByText("Rendered prompt sent to model: Question?", { exact: true })).toBeVisible();
  await expect(page.getByText("Model output", { exact: true })).toBeVisible();
  await expect(page.getByText("Expected answer", { exact: true })).toBeVisible();
  await expect(page.getByText("Expected output", { exact: true })).toBeVisible();
  await expect(page.getByText("Original benchmark input", { exact: true })).toBeVisible();
  await expect(page.getByText("It is not the prompt sent to the model.", { exact: false })).toBeVisible();
  await expect(page.getByText("Evaluation explanation unavailable")).toBeVisible();
  await expect(page.getByText("client · sample · latency-v1")).toBeVisible();
});
