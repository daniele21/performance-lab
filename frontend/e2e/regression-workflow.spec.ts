import { expect, test, type Page, type Route } from "@playwright/test";

const API_IDENTITY = { api_version: "v1", read_model_version: 1 } as const;
const NOW = "2026-09-05T09:00:00Z";

function runSummary(runId: string, modelId: string) {
  return {
    ...API_IDENTITY,
    run_id: runId,
    status: "succeeded",
    created_at: NOW,
    completed_at: NOW,
    suite_id: "general-diagnostic-starter",
    suite_version: "1",
    fingerprint_id: `fp-${runId}`,
    identity: {
      ...API_IDENTITY,
      model_id: modelId,
      revision: "r1",
      quantization: "Q4_K_M",
      artifact_digest: `sha256:${runId}`,
      target_id: "target-local",
      endpoint_identity: "loopback-fixture",
      runtime_name: "llama.cpp",
      runtime_version: "fixture-1",
      hardware_device_id: "device-a",
      hardware_device_class: "desktop",
    },
    metrics: [],
  };
}

type Decision = "pass" | "fail" | "not_comparable";

function comparison(decision: Decision) {
  const incompatible = decision === "not_comparable";
  return {
    ...API_IDENTITY,
    baseline_run_id: "run-base",
    candidate_run_id: "run-candidate",
    identity_differences: incompatible
      ? [{ path: "dataset_snapshots", baseline: "fixture-v1", candidate: "fixture-v2" }]
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
                code: "dataset_snapshot_mismatch",
                field: "dataset_snapshots",
                message: "Dataset snapshots differ; quality is not comparable.",
                baseline: "fixture-v1",
                candidate: "fixture-v2",
              },
            ]
          : [],
        deltas: incompatible
          ? []
          : [
              {
                metric: "accuracy|exact-match@1",
                baseline_value: 0.8,
                candidate_value: decision === "pass" ? 0.79 : 0.7,
                absolute_delta: decision === "pass" ? -0.01 : -0.1,
                relative_delta_pct: decision === "pass" ? -1.25 : -12.5,
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

function evaluation(decision: Decision) {
  return {
    ...API_IDENTITY,
    baseline_run_id: "run-base",
    baseline_fingerprint_id: "fp-run-base",
    candidate_run_id: "run-candidate",
    candidate_fingerprint_id: "fp-run-candidate",
    policy_id: "release-gate",
    policy_version: "1",
    decision,
    rule_results: [
      {
        ...API_IDENTITY,
        rule_id: "accuracy",
        dimension: "capability",
        metric: "accuracy|exact-match@1",
        state: decision,
        reason:
          decision === "pass"
            ? "regression is within configured tolerance"
            : decision === "fail"
              ? "absolute regression 0.1 exceeds 0.02"
              : "target dimension is not comparable",
      },
    ],
    comparison: comparison(decision),
  };
}

async function fulfillJson(route: Route, payload: unknown, status = 200) {
  await route.fulfill({ status, contentType: "application/json", body: JSON.stringify(payload) });
}

async function installFixture(page: Page, decision: Decision) {
  const runs = [
    runSummary("run-candidate", "model-candidate"),
    runSummary("run-base", "model-baseline"),
  ];
  const policies = [
    {
      ...API_IDENTITY,
      policy_id: "release-gate",
      policy_version: "1",
      rule_count: 1,
    },
  ];

  await page.route("**/api/v1/**", async (route) => {
    const request = route.request();
    const path = new URL(request.url()).pathname;
    if (path === "/api/v1/runs") {
      await fulfillJson(route, runs);
      return;
    }
    if (path === "/api/v1/regression-policies") {
      await fulfillJson(route, policies);
      return;
    }
    if (path === "/api/v1/regression-evaluations") {
      await fulfillJson(route, evaluation(decision));
      return;
    }
    await fulfillJson(route, { detail: `Unhandled regression fixture route: ${path}` }, 500);
  });
}

async function openAndEvaluate(page: Page, decision: Decision) {
  await installFixture(page, decision);
  await page.goto("/#compare");
  await expect(page.getByLabel("Regression policy")).toContainText("release-gate@1");
  await page.getByRole("button", { name: "Evaluate regression" }).click();
  await expect(page.getByRole("heading", { name: "Compatibility first" })).toBeVisible();
  await expect(page.getByRole("heading", { name: "Regression policy outcome" })).toBeVisible();
  await expect(page.getByText("release-gate@1", { exact: true })).toBeVisible();
}

test("policy-backed Compare renders PASS from backend policy evidence", async ({ page }) => {
  await openAndEvaluate(page, "pass");
  await expect(page.locator(".compare-regression-summary").getByText("PASS", { exact: true })).toBeVisible();
  await expect(page.getByRole("table", { name: "Regression policy rules" })).toContainText(
    "regression is within configured tolerance",
  );
  await expect(page.getByRole("table", { name: "Capability / quality metric deltas" })).toBeVisible();
});

test("policy-backed Compare renders FAIL with the owning rule reason", async ({ page }) => {
  await openAndEvaluate(page, "fail");
  await expect(page.locator(".compare-regression-summary").getByText("FAIL", { exact: true })).toBeVisible();
  await expect(page.getByRole("table", { name: "Regression policy rules" })).toContainText(
    "absolute regression 0.1 exceeds 0.02",
  );
});

test("policy-backed Compare foregrounds NOT_COMPARABLE and hides invalid deltas", async ({
  page,
}) => {
  await openAndEvaluate(page, "not_comparable");
  await expect(page.getByText("Dataset snapshots differ", { exact: false })).toBeVisible();
  await expect(
    page.locator(".compare-regression-summary").getByText("NOT COMPARABLE", { exact: true }),
  ).toBeVisible();
  await expect(page.getByRole("table", { name: "Capability / quality metric deltas" })).toHaveCount(
    0,
  );
});
