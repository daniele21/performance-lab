import { expect, test, type Route } from "@playwright/test";

const snapshot = {
  api_version: "v1",
  job_id: "job-reconnect",
  state: "running",
  revision: 1,
  created_at: "2026-08-30T16:00:00Z",
  updated_at: "2026-08-30T16:00:01Z",
  config_digest: "a".repeat(64),
  target_id: "target-local",
  model_id: "model-candidate",
  scenario: "general_capability",
  phase: "evaluating",
  completed_samples: 1,
  total_samples: 4,
  run_id: null,
  run_status: "running",
  error_code: null,
  error_message: null,
};

async function fulfillJson(route: Route, payload: unknown, status = 200) {
  await route.fulfill({ status, contentType: "application/json", body: JSON.stringify(payload) });
}

test("Live Run can reconnect after a transient initial read failure", async ({ page }) => {
  let readAttempts = 0;

  await page.route("**/api/v1/run-jobs/job-reconnect**", async (route) => {
    const request = route.request();
    const url = new URL(request.url());

    if (url.pathname.endsWith("/events")) {
      await route.fulfill({
        status: 200,
        contentType: "text/event-stream",
        headers: { "Cache-Control": "no-cache" },
        body: `event: run_job\ndata: ${JSON.stringify(snapshot)}\n\n`,
      });
      return;
    }

    readAttempts += 1;
    if (readAttempts === 1) {
      await fulfillJson(route, { detail: "Temporary local API interruption" }, 503);
      return;
    }
    await fulfillJson(route, snapshot);
  });

  await page.goto("/#live-run/job-reconnect");
  await expect(page.getByRole("heading", { name: "Could not reconnect to this run" })).toBeVisible();
  await expect(page.getByText("Temporary local API interruption", { exact: false })).toBeVisible();

  await page.getByRole("button", { name: "Reconnect to run" }).click();

  await expect(page.getByRole("heading", { name: "model-candidate" })).toBeVisible();
  await expect(page.getByText("Live progress connected")).toBeVisible();
  expect(readAttempts).toBe(2);
});
