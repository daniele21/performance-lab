import { expect, test, type Page, type Route } from "@playwright/test";

const API_IDENTITY = { api_version: "v1", read_model_version: 1 } as const;

const runSummary = {
  ...API_IDENTITY,
  run_id: "run-a",
  status: "succeeded",
  created_at: "2026-09-05T10:00:00Z",
  completed_at: "2026-09-05T10:00:02Z",
  suite_id: "starter",
  suite_version: "1",
  fingerprint_id: "f".repeat(64),
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

const runDetail = {
  ...API_IDENTITY,
  summary: runSummary,
  evidence: {
    ...API_IDENTITY,
    fingerprint: { fingerprint_id: "f".repeat(64), target_id: "local" },
    dataset_count: 1,
    evaluator_count: 1,
    sample_count: 4,
  },
};

const availableRepeatability = {
  ...API_IDENTITY,
  anchor_run_id: "run-a",
  fingerprint_id: "f".repeat(64),
  state: "available",
  load_profile: {
    concurrency: 1,
    request_count: 4,
    warmup_requests: 0,
    streaming: false,
  },
  run_ids: ["run-a", "run-b", "run-failed"],
  run_count: 3,
  succeeded_run_count: 2,
  failed_run_count: 1,
  cancelled_run_count: 0,
  sample_attempt_count: 10,
  succeeded_sample_count: 8,
  failed_sample_count: 2,
  cancelled_sample_count: 0,
  note: "Failures remain in the cohort denominators and are not converted to zero.",
  metrics: [
    {
      ...API_IDENTITY,
      metric_id: "total_latency_ms|client|single-request-v1|ms",
      label: "total_latency_ms",
      dimension: "performance",
      unit: "ms",
      higher_is_better: null,
      run_values: [
        { ...API_IDENTITY, run_id: "run-a", value: 100, source_sample_count: 4 },
        { ...API_IDENTITY, run_id: "run-b", value: 120, source_sample_count: 4 },
      ],
      distribution: {
        ...API_IDENTITY,
        sample_count: 2,
        minimum: 100,
        maximum: 120,
        mean: 110,
        median: 110,
        stddev: 10,
        coefficient_of_variation: 0.0909,
        p90: {
          ...API_IDENTITY,
          percentile: 90,
          value: null,
          sample_count: 2,
          qualified: false,
          qualification: "requires at least 10 samples; only 2 available",
        },
        p95: {
          ...API_IDENTITY,
          percentile: 95,
          value: null,
          sample_count: 2,
          qualified: false,
          qualification: "requires at least 20 samples; only 2 available",
        },
      },
    },
  ],
};

async function fulfillJson(route: Route, payload: unknown, status = 200) {
  await route.fulfill({ status, contentType: "application/json", body: JSON.stringify(payload) });
}

async function installFixture(page: Page, repeatability: unknown) {
  await page.route("**/api/v1/**", async (route) => {
    const pathname = new URL(route.request().url()).pathname;
    if (pathname === "/api/v1/runs/run-a") {
      await fulfillJson(route, runDetail);
      return;
    }
    if (pathname === "/api/v1/runs/run-a/samples") {
      await fulfillJson(route, []);
      return;
    }
    if (pathname === "/api/v1/runs/run-a/repeatability") {
      await fulfillJson(route, repeatability);
      return;
    }
    await fulfillJson(route, []);
  });
}

test("J9: Run Detail exposes exact-fingerprint variability and failure denominators", async ({
  page,
}) => {
  await installFixture(page, availableRepeatability);
  await page.goto("/#runs/run-a");

  const section = page.getByLabel("Repeatability evidence");
  await expect(section.getByRole("heading", { name: "Repeatability" })).toBeVisible();
  await expect(section.getByText("Evidence available", { exact: true })).toBeVisible();
  await expect(section.getByText("3 exact-fingerprint runs", { exact: true })).toBeVisible();
  await expect(section.getByText("2 succeeded · 1 failed · 0 cancelled", { exact: true })).toBeVisible();
  await expect(section.getByText("8 succeeded · 2 failed · 0 cancelled", { exact: true })).toBeVisible();

  await section.getByText("Show run-to-run variability", { exact: true }).click();
  await expect(section.getByRole("heading", { name: "total_latency_ms" })).toBeVisible();
  await expect(section.getByText("110 ms", { exact: true })).toBeVisible();
  await expect(
    section.getByText("requires at least 10 samples; only 2 available", { exact: true }),
  ).toBeVisible();
  await expect(section.getByText("Stable", { exact: true })).toHaveCount(0);
});

test("J9: Run Detail keeps one exact-fingerprint Run explicitly insufficient", async ({ page }) => {
  await installFixture(page, {
    ...availableRepeatability,
    state: "insufficient_repeats",
    run_ids: ["run-a"],
    run_count: 1,
    succeeded_run_count: 1,
    failed_run_count: 0,
    sample_attempt_count: 4,
    succeeded_sample_count: 4,
    failed_sample_count: 0,
    metrics: [],
    note: "Only one exact-fingerprint Run is retained. Repeat this exact frozen test.",
  });
  await page.goto("/#runs/run-a");

  const section = page.getByLabel("Repeatability evidence");
  await expect(section.getByText("Insufficient repeats", { exact: true })).toBeVisible();
  await expect(section.getByText("1 exact-fingerprint runs", { exact: true })).toBeVisible();
  await expect(section.getByText("Repeat this exact frozen test.", { exact: false })).toBeVisible();
  await expect(section.getByText("Show run-to-run variability", { exact: true })).toHaveCount(0);
});
