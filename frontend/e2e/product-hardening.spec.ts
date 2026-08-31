import { expect, test, type Page, type Route } from "@playwright/test";

const API = { api_version: "v1", read_model_version: 1 } as const;
const NOW = "2026-08-31T08:00:00Z";
const LONG_MODEL_ID = `model-${"x".repeat(180)}`;
const LONG_RUN_ID = `run-${"r".repeat(180)}`;
const LONG_TASK_ID = `task-${"t".repeat(60)}`;
const LONG_SAMPLE_ID = `sample-${"s".repeat(90)}`;
const LONG_CONTENT = `content-${"z".repeat(1800)}`;

async function fulfillJson(route: Route, payload: unknown, status = 200) {
  await route.fulfill({ status, contentType: "application/json", body: JSON.stringify(payload) });
}

function identity(modelId: string) {
  return {
    ...API,
    model_id: modelId,
    revision: "revision-with-a-long-but-valid-identity",
    quantization: "Q4_K_M",
    artifact_digest: `sha256:${"a".repeat(64)}`,
    target_id: "target-local",
    endpoint_identity: "loopback-fixture",
    runtime_name: "llama.cpp",
    runtime_version: "fixture-1",
    hardware_device_id: "device-a",
    hardware_device_class: "laptop",
  };
}

function qualityMetric(index = 0) {
  return {
    ...API,
    metric_id: `quality_metric_${index}|fixture@1`,
    label: `Quality metric ${index}`,
    dimension: "quality",
    availability: "available",
    value: 1 - index / 100,
    unit: null,
    higher_is_better: true,
    provenance: "fixture",
    protocol_version: "1",
  };
}

function runSummary(runId = LONG_RUN_ID, modelId = LONG_MODEL_ID) {
  return {
    ...API,
    run_id: runId,
    status: "succeeded",
    created_at: NOW,
    completed_at: NOW,
    suite_id: "general-diagnostic-starter",
    suite_version: "1",
    fingerprint_id: `fp-${runId}`,
    identity: identity(modelId),
    metrics: [qualityMetric()],
  };
}

async function installRunsFixture(page: Page, failFirst = false) {
  let attempts = 0;
  await page.route("**/api/v1/runs**", async (route) => {
    attempts += 1;
    if (failFirst && attempts === 1) {
      await fulfillJson(route, { detail: "Fixture storage is temporarily unavailable." }, 503);
      return;
    }
    await fulfillJson(route, []);
  });
}

function sampleEvidence(runId: string, modelId: string, scoreOffset: number) {
  return {
    ...API,
    run: runSummary(runId, modelId),
    fingerprint: { fingerprint_id: `fp-${runId}` },
    sample: {
      ...API,
      run_id: runId,
      task_id: LONG_TASK_ID,
      sample_id: LONG_SAMPLE_ID,
      attempt: 1,
      status: "succeeded",
      started_at: NOW,
      completed_at: NOW,
      elapsed_ms: 125.5,
      elapsed_provenance: "sample_execution_timestamps",
      input_tokens: 64,
      output_tokens: 32,
      score_count: 12,
      measurement_count: 1,
      error: null,
    },
    benchmark_case: {
      ...API,
      case_id: `${LONG_TASK_ID}:${LONG_SAMPLE_ID}`,
      task_id: LONG_TASK_ID,
      sample_id: LONG_SAMPLE_ID,
      dataset_id: "long-content-fixture",
      dataset_version: "1",
      input: LONG_CONTENT,
      expected: LONG_CONTENT,
      evaluator_id: "fixture",
      evaluator_version: "1",
      metric_names: Array.from({ length: 12 }, (_, index) => `quality_metric_${index}`),
    },
    prompt: {
      ...API,
      state: "retained",
      content: LONG_CONTENT,
      reason: null,
    },
    response: {
      ...API,
      state: "retained",
      content: LONG_CONTENT,
      reason: null,
    },
    scores: Array.from({ length: 12 }, (_, index) => ({
      ...API,
      metric: `quality_metric_${index}`,
      value: 1 - (index + scoreOffset) / 100,
      evaluator_id: "fixture",
      evaluator_version: "1",
      higher_is_better: true,
      numerator: null,
      denominator: null,
      evaluator_rule_summary: `Fixture evaluator rule ${index}`,
      explanation_state: "available",
      explanation: `Explanation ${index}`,
    })),
    measurements: [
      {
        ...API,
        name: "elapsed_ms",
        value: 125.5,
        unit: "ms",
        provenance: "fixture",
        protocol_version: "1",
      },
    ],
    definition_issues: [],
  };
}

function candidate(index: number, modelId: string, runId: string) {
  return {
    ...API,
    entry_id: `entry-${index}`,
    candidate_id: `candidate-${index}`,
    model_id: modelId,
    config_digest: String(index).repeat(64),
    entry_status: "succeeded",
    run_id: runId,
    identity: identity(modelId),
    comparable_to_reference: true,
    compatibility_reasons: [],
    evidence: sampleEvidence(runId, modelId, index),
    unavailable_reason: null,
  };
}

const longCaseComparison = {
  ...API,
  campaign_id: "campaign-long",
  suite_id: "general-diagnostic-starter",
  suite_version: "1",
  task_id: LONG_TASK_ID,
  sample_id: LONG_SAMPLE_ID,
  state: "ready",
  reference_run_id: LONG_RUN_ID,
  benchmark_case: sampleEvidence(LONG_RUN_ID, LONG_MODEL_ID, 0).benchmark_case,
  candidates: [
    candidate(1, LONG_MODEL_ID, LONG_RUN_ID),
    candidate(2, `alternative-${"y".repeat(170)}`, `run-alt-${"q".repeat(170)}`),
  ],
  comparable_candidate_count: 2,
  summary: "Both retained candidate attempts are capability-compatible for this exact case.",
};

async function assertNoDocumentOverflow(page: Page) {
  const overflow = await page.evaluate(
    () => document.documentElement.scrollWidth > document.documentElement.clientWidth + 1,
  );
  expect(overflow).toBe(false);
}

test("keyboard users can skip navigation and SPA route changes restore focus to main", async ({
  page,
}) => {
  await installRunsFixture(page);
  await page.goto("/#runs");
  await expect(page.getByRole("heading", { name: "Runs", exact: true })).toBeVisible();

  await page.keyboard.press("Tab");
  const skipLink = page.getByRole("link", { name: "Skip to main content" });
  await expect(skipLink).toBeFocused();
  await expect(skipLink).toBeVisible();
  await page.keyboard.press("Enter");
  await expect(page.getByRole("main")).toBeFocused();
  await expect(page).toHaveURL(/#runs$/);

  const compareLink = page.getByRole("link", { name: "Compare", exact: true });
  await compareLink.focus();
  await page.keyboard.press("Enter");
  await expect(page).toHaveURL(/#compare$/);
  await expect(page.getByRole("main")).toBeFocused();
});

test("recoverable loading failures are announced and retry returns to a useful empty state", async ({
  page,
}) => {
  await installRunsFixture(page, true);
  await page.goto("/#runs");

  const alert = page.getByRole("alert");
  await expect(alert).toContainText("Could not load runs");
  await expect(alert).toContainText("Fixture storage is temporarily unavailable.");
  await page.getByRole("button", { name: "Try again" }).click();

  await expect(page.getByRole("heading", { name: "Runs", exact: true })).toBeVisible();
  await expect(page.getByText("No completed runs yet")).toBeVisible();
});

test("supported desktop widths contain long case identity, content and evaluator evidence", async ({
  page,
}) => {
  await page.route("**/api/v1/campaigns/campaign-long/cases/**", async (route) => {
    await fulfillJson(route, longCaseComparison);
  });

  for (const viewport of [
    { width: 1024, height: 800 },
    { width: 1280, height: 900 },
    { width: 1600, height: 1000 },
  ]) {
    await page.setViewportSize(viewport);
    await page.goto(
      `/#campaigns/campaign-long/cases/${encodeURIComponent(LONG_TASK_ID)}/${encodeURIComponent(LONG_SAMPLE_ID)}`,
    );

    await expect(page.getByRole("heading", { name: "Candidate evidence" })).toBeVisible();
    await expect(page.getByText(LONG_MODEL_ID, { exact: true })).toBeVisible();
    await expect(page.getByText("quality_metric_11 · fixture@1").first()).toBeVisible();
    await expect(page.locator("pre").first()).toContainText(LONG_CONTENT.slice(0, 120));
    await assertNoDocumentOverflow(page);
  }
});

test("reduced motion keeps functional focus affordances while eliminating transitions", async ({
  page,
}) => {
  await installRunsFixture(page);
  await page.emulateMedia({ reducedMotion: "reduce" });
  await page.goto("/#runs");

  await page.keyboard.press("Tab");
  const skipLink = page.getByRole("link", { name: "Skip to main content" });
  await expect(skipLink).toBeVisible();
  const transitionDuration = await skipLink.evaluate(
    (element) => getComputedStyle(element).transitionDuration,
  );
  expect(Number.parseFloat(transitionDuration)).toBeLessThanOrEqual(0.00001);
});
