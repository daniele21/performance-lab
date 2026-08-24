import { expect, test, type Page, type Route } from "@playwright/test";

const API_IDENTITY = { api_version: "v1", read_model_version: 1 } as const;
const NOW = "2026-08-24T07:00:00Z";
const DIGEST = "a".repeat(64);

const identity = {
  ...API_IDENTITY,
  model_id: "model-candidate",
  revision: "r1",
  quantization: "Q4_K_M",
  artifact_digest: "sha256:model",
  target_id: "target-local",
  endpoint_identity: "loopback-fixture",
  runtime_name: "llama.cpp",
  runtime_version: "fixture-1",
  hardware_device_id: "device-a",
  hardware_device_class: "phone",
};

const qualityMetric = {
  ...API_IDENTITY,
  metric_id: "normalized_exact_match|fixture@1",
  label: "Exact match",
  dimension: "quality",
  availability: "available",
  value: 0.84,
  unit: null,
  higher_is_better: true,
  provenance: "fixture",
  protocol_version: "1",
};

const performanceMetric = {
  ...API_IDENTITY,
  metric_id: "tokens_per_second",
  label: "Tokens / second",
  dimension: "performance",
  availability: "available",
  value: 18.5,
  unit: "tok/s",
  higher_is_better: true,
  provenance: "fixture",
  protocol_version: "1",
};

const resourceMetric = {
  ...API_IDENTITY,
  metric_id: "peak_rss_mb",
  label: "Peak RSS",
  dimension: "resources",
  availability: "available",
  value: 1420,
  unit: "MB",
  higher_is_better: false,
  provenance: "fixture",
  protocol_version: "1",
};

function runSummary(runId: string, modelId = "model-candidate") {
  return {
    ...API_IDENTITY,
    run_id: runId,
    status: "succeeded",
    created_at: NOW,
    completed_at: NOW,
    suite_id: "general-diagnostic-starter",
    suite_version: "1",
    fingerprint_id: `fp-${runId}`,
    identity: { ...identity, model_id: modelId },
    metrics: [qualityMetric, performanceMetric, resourceMetric],
  };
}

function runDetail(runId: string) {
  return {
    ...API_IDENTITY,
    summary: runSummary(runId),
    evidence: {
      ...API_IDENTITY,
      fingerprint: { fingerprint_id: `fp-${runId}`, fixture: true },
      dataset_count: 1,
      evaluator_count: 1,
      sample_count: 4,
    },
  };
}

function jobSnapshot(jobId: string, state: "running" | "succeeded" | "failed" | "cancelled") {
  const terminal = state !== "running";
  return {
    api_version: "v1",
    job_id: jobId,
    state,
    revision: terminal ? 2 : 1,
    created_at: NOW,
    updated_at: NOW,
    config_digest: DIGEST,
    target_id: "target-local",
    model_id: "model-candidate",
    scenario: "general_capability",
    phase: terminal ? "completed" : "evaluating",
    completed_samples: terminal ? 4 : 1,
    total_samples: 4,
    run_id: state === "succeeded" ? "run-candidate" : null,
    run_status:
      state === "succeeded"
        ? "succeeded"
        : state === "failed"
          ? "failed"
          : state === "cancelled"
            ? "cancelled"
            : "running",
    error_code: state === "failed" ? "fixture_failure" : null,
    error_message: state === "failed" ? "Fixture inference failed. Retry is safe." : null,
  };
}

const targets = [
  {
    ...API_IDENTITY,
    target_id: "target-local",
    display_name: "Local device",
    adapter_type: "openai-compatible",
    endpoint_profile_id: "loopback",
    endpoint_identity: "loopback-fixture",
    capabilities: ["streaming"],
  },
];

const scenarios = [
  {
    ...API_IDENTITY,
    scenario: "general_capability",
    title: "General capability",
    description: "Use the frozen starter suite.",
    supported: true,
    blocked_reason: null,
    suite_id: "general-diagnostic-starter",
  },
];

const preflight = {
  ...API_IDENTITY,
  can_run: true,
  issues: [],
  preview: {
    ...API_IDENTITY,
    scenario: "general_capability",
    config: {
      target_id: "target-local",
      endpoint_identity: "loopback-fixture",
      endpoint: { profile_id: "loopback", base_url: "http://127.0.0.1:9/v1" },
      model_id: "model-candidate",
      output_dir: "results",
      store_path: ".performance-lab/runs.sqlite3",
      run_id: null,
      write_bundle: true,
      use_host_telemetry: false,
      suite_id: "general-diagnostic-starter",
    },
    config_digest: DIGEST,
    target: targets[0],
    suite: {
      ...API_IDENTITY,
      suite_id: "general-diagnostic-starter",
      suite_version: "1",
      task_count: 1,
      task_ids: ["fixture-task"],
    },
    datasets: [
      {
        ...API_IDENTITY,
        dataset_id: "fixture-dataset",
        dataset_version: "1",
        source: "browser-fixture",
        split: "test",
        sample_count: 4,
        selection_policy: "frozen",
        content_sha256: "b".repeat(64),
      },
    ],
    evaluator_ids: ["fixture-evaluator@1"],
    generation: {},
    load_profile: {},
    prompt_template_version: "1",
    benchmark_protocol_version: "1",
    identity_resolution: "resolved_at_launch",
  },
};

interface FixtureOptions {
  comparison?: "compatible" | "incompatible";
  requireCancellationBeforeLaunch?: boolean;
}

interface FixtureState {
  cancelled: boolean;
  launchRequests: number;
}

async function fulfillJson(route: Route, payload: unknown, status = 200) {
  await route.fulfill({ status, contentType: "application/json", body: JSON.stringify(payload) });
}

function comparison(mode: "compatible" | "incompatible") {
  const incompatible = mode === "incompatible";
  return {
    ...API_IDENTITY,
    baseline_run_id: "run-base",
    candidate_run_id: "run-candidate",
    identity_differences: incompatible
      ? [{ path: "suite_id", baseline: "starter-v1", candidate: "other-suite" }]
      : [],
    dimensions: [
      {
        ...API_IDENTITY,
        dimension: "capability",
        comparable: !incompatible,
        reasons: incompatible
          ? [
              {
                ...API_IDENTITY,
                code: "suite_mismatch",
                field: "suite_id",
                message: "Suite identity differs; quality deltas are not interpretable.",
                baseline: "starter-v1",
                candidate: "other-suite",
              },
            ]
          : [],
        deltas: incompatible
          ? []
          : [
              {
                metric: "normalized_exact_match|fixture@1",
                baseline_value: 0.74,
                candidate_value: 0.84,
                absolute_delta: 0.1,
                relative_delta_pct: 13.51,
                higher_is_better: true,
                unit: null,
              },
            ],
        missing_in_baseline: [],
        missing_in_candidate: [],
      },
      {
        ...API_IDENTITY,
        dimension: "runtime",
        comparable: true,
        reasons: [],
        deltas: [],
        missing_in_baseline: [],
        missing_in_candidate: [],
      },
      {
        ...API_IDENTITY,
        dimension: "resource",
        comparable: true,
        reasons: [],
        deltas: [],
        missing_in_baseline: [],
        missing_in_candidate: [],
      },
    ],
  };
}

async function installFixture(page: Page, options: FixtureOptions = {}): Promise<FixtureState> {
  const state: FixtureState = { cancelled: false, launchRequests: 0 };
  const runs = [runSummary("run-candidate"), runSummary("run-base", "model-baseline")];

  await page.route("**/api/v1/**", async (route) => {
    const request = route.request();
    const url = new URL(request.url());
    const path = url.pathname;

    if (path === "/api/v1/tested-models") {
      await fulfillJson(route, [
        {
          ...API_IDENTITY,
          cohort_key: "candidate-cohort",
          identity,
          run_count: 2,
          latest_run_id: "run-candidate",
          latest_completed_at: NOW,
          latest_metrics: [qualityMetric, performanceMetric, resourceMetric],
        },
      ]);
      return;
    }
    if (path === "/api/v1/runs" && request.method() === "GET") {
      await fulfillJson(route, runs);
      return;
    }
    if (path.startsWith("/api/v1/runs/") && request.method() === "GET") {
      const runId = decodeURIComponent(path.slice("/api/v1/runs/".length));
      await fulfillJson(route, runDetail(runId));
      return;
    }
    if (path === "/api/v1/targets") {
      await fulfillJson(route, targets);
      return;
    }
    if (path === "/api/v1/scenarios") {
      await fulfillJson(route, scenarios);
      return;
    }
    if (path === "/api/v1/run-preflight" && request.method() === "POST") {
      await fulfillJson(route, preflight);
      return;
    }
    if (path === "/api/v1/run-jobs" && request.method() === "POST") {
      state.launchRequests += 1;
      if (options.requireCancellationBeforeLaunch && !state.cancelled) {
        await fulfillJson(route, { detail: "Previous job resources are still owned." }, 409);
        return;
      }
      await fulfillJson(route, jobSnapshot("job-success", "running"));
      return;
    }
    if (path.endsWith("/cancel") && request.method() === "POST") {
      state.cancelled = true;
      const jobId = decodeURIComponent(path.split("/").at(-2) ?? "job-cancel");
      await fulfillJson(route, jobSnapshot(jobId, "cancelled"));
      return;
    }
    if (path.endsWith("/events") && request.method() === "GET") {
      const jobId = decodeURIComponent(path.split("/").at(-2) ?? "job-success");
      const snapshot =
        jobId === "job-success" ? jobSnapshot(jobId, "succeeded") : jobSnapshot(jobId, "running");
      await route.fulfill({
        status: 200,
        contentType: "text/event-stream",
        headers: { "Cache-Control": "no-cache" },
        body: `event: run_job\ndata: ${JSON.stringify(snapshot)}\n\n`,
      });
      return;
    }
    if (path.startsWith("/api/v1/run-jobs/") && request.method() === "GET") {
      const jobId = decodeURIComponent(path.slice("/api/v1/run-jobs/".length));
      const snapshot =
        jobId === "job-fail"
          ? jobSnapshot(jobId, "failed")
          : jobId === "job-cancel" && state.cancelled
            ? jobSnapshot(jobId, "cancelled")
            : jobSnapshot(jobId, "running");
      await fulfillJson(route, snapshot);
      return;
    }
    if (path === "/api/v1/comparisons") {
      await fulfillJson(route, comparison(options.comparison ?? "compatible"));
      return;
    }
    if (path === "/api/v1/suites") {
      await fulfillJson(route, [preflight.preview.suite]);
      return;
    }
    if (path === "/api/v1/datasets") {
      await fulfillJson(route, preflight.preview.datasets);
      return;
    }
    if (path === "/api/v1/baselines" || path === "/api/v1/regression-policies") {
      await fulfillJson(route, []);
      return;
    }

    await fulfillJson(
      route,
      { detail: `Unhandled browser fixture route: ${request.method()} ${path}` },
      500,
    );
  });

  return state;
}

async function completeEvaluation(page: Page) {
  await expect(page.getByRole("heading", { name: "Test a model" })).toBeVisible();
  await page.getByLabel("Model ID").fill("model-candidate");
  await page.getByRole("button", { name: "Continue" }).click();
  await expect(page.getByRole("heading", { name: "What do you want to learn?" })).toBeVisible();
  await page.getByRole("button", { name: "Continue" }).click();
  await expect(page.getByRole("heading", { name: "Test settings" })).toBeVisible();
  await page.getByRole("button", { name: "Continue" }).click();
  await expect(page.getByText("Preflight passed")).toBeVisible();
  await page.getByRole("button", { name: "Run test" }).click();
  await expect(page).toHaveURL(/#runs\/run-candidate$/);
  await expect(page.getByRole("heading", { name: "model-candidate" })).toBeVisible();
}

async function assertNoDuplicateIds(page: Page) {
  const duplicates = await page.locator("[id]").evaluateAll((nodes) => {
    const ids = nodes.map((node) => node.id).filter(Boolean);
    return ids.filter((id, index) => ids.indexOf(id) !== index);
  });
  expect(duplicates).toEqual([]);
}

test("J1: configure, freeze, run, progress and inspect immutable result", async ({ page }) => {
  await installFixture(page);
  await page.goto("/#test-a-model");
  await completeEvaluation(page);
  await expect(page.getByText("fp-run-candidate", { exact: true })).toBeVisible();
  await expect(page.getByRole("heading", { name: "Quality" })).toBeVisible();
});

test("J2: find tested model evidence with device/workload context", async ({ page }) => {
  await installFixture(page);
  await page.goto("/#overview");

  await expect(page.getByRole("heading", { name: "Your tested models" })).toBeVisible();
  await expect(page.getByRole("table", { name: "Tested model evidence" })).toContainText(
    "model-candidate",
  );
  await expect(page.getByRole("table", { name: "Tested model evidence" })).toContainText(
    "device-a",
  );
  await expect(page.getByText("Recommended model")).toHaveCount(0);
});

test("J3: compatible evidence exposes only valid trade-off deltas", async ({ page }) => {
  await installFixture(page, { comparison: "compatible" });
  await page.goto("/#compare");

  await page.locator("#select-baseline").selectOption("run-base");
  await page.locator("#select-candidate").selectOption("run-candidate");
  await page.getByRole("button", { name: "Compare evidence" }).click();

  await expect(
    page.getByRole("table", { name: "Capability / quality metric deltas" }),
  ).toBeVisible();
  await expect(page.getByText("normalized_exact_match")).toBeVisible();
  await expect(page.getByText("Suite identity differs", { exact: false })).toHaveCount(0);
});

test("J4: incompatible evidence foregrounds reasons and hides invalid deltas", async ({ page }) => {
  await installFixture(page, { comparison: "incompatible" });
  await page.goto("/#compare");

  await page.locator("#select-baseline").selectOption("run-base");
  await page.locator("#select-candidate").selectOption("run-candidate");
  await page.getByRole("button", { name: "Compare evidence" }).click();

  await expect(page.getByText("Suite identity differs", { exact: false })).toBeVisible();
  await expect(page.getByRole("table", { name: "Capability / quality metric deltas" })).toHaveCount(
    0,
  );
});

test("J5: failed run exposes actionable recovery and a successful retry", async ({ page }) => {
  await installFixture(page);
  await page.goto("/#live-run/job-fail");

  await expect(page.getByText("The evaluation failed")).toBeVisible();
  await expect(page.getByText("Fixture inference failed. Retry is safe.")).toBeVisible();
  await page.getByRole("button", { name: "Test a model" }).click();
  await completeEvaluation(page);
});

test("J6: cancellation completes before the next evaluation succeeds", async ({ page }) => {
  const state = await installFixture(page, { requireCancellationBeforeLaunch: true });
  await page.goto("/#live-run/job-cancel");

  await expect(page.getByRole("button", { name: "Cancel run" })).toBeVisible();
  await page.getByRole("button", { name: "Cancel run" }).click();
  await expect(page.getByRole("heading", { name: "Run cancelled" })).toBeVisible();
  expect(state.cancelled).toBe(true);

  await page.getByRole("button", { name: "Test again" }).click();
  await completeEvaluation(page);
  expect(state.launchRequests).toBe(1);
});

test("compact, wide and reduced-motion modes preserve core accessibility invariants", async ({
  page,
}) => {
  await installFixture(page);
  await page.emulateMedia({ reducedMotion: "reduce" });

  for (const viewport of [
    { width: 375, height: 812 },
    { width: 1440, height: 900 },
  ]) {
    await page.setViewportSize(viewport);
    await page.goto("/#overview");
    await expect(page.getByRole("main")).toBeVisible();
    await expect(page.getByRole("navigation", { name: "Primary navigation" })).toBeVisible();
    await expect(page.getByRole("heading", { name: "Your tested models" })).toBeVisible();
    await assertNoDuplicateIds(page);

    const horizontalOverflow = await page.evaluate(
      () => document.documentElement.scrollWidth > document.documentElement.clientWidth + 1,
    );
    expect(horizontalOverflow).toBe(false);
  }

  const transitionDuration = await page
    .getByRole("link", { name: "Overview" })
    .evaluate((element) => getComputedStyle(element).transitionDuration);
  expect(Number.parseFloat(transitionDuration)).toBeLessThanOrEqual(0.00001);
});
