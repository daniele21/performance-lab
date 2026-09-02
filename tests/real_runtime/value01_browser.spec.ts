import { expect, test } from "@playwright/test";

const model = process.env.PERFORMANCE_LAB_REAL_E2E_MODEL;

if (!model) {
  throw new Error("PERFORMANCE_LAB_REAL_E2E_MODEL is required for VALUE-01 real browser E2E");
}

test("VALUE-01 real browser: discover, execute, inspect run and sample evidence", async ({ page }) => {
  await page.goto("/#test-a-model");
  await expect(page.getByRole("heading", { name: "Test a model" })).toBeVisible();

  await expect(page.getByLabel("Model source")).toHaveValue("configured");
  await expect(page.getByLabel("Model", { exact: true })).toHaveValue(model, { timeout: 30_000 });
  await page.getByRole("button", { name: "Continue" }).click();

  await expect(page.getByRole("heading", { name: "What do you want to learn?" })).toBeVisible();
  await page.getByRole("button", { name: "Continue" }).click();

  await expect(page.getByRole("heading", { name: "Test settings" })).toBeVisible();
  await page.getByRole("button", { name: "Continue" }).click();

  await expect(page.getByText("Preflight passed")).toBeVisible({ timeout: 30_000 });
  await page.getByRole("button", { name: "Run test" }).click();

  await expect(page).toHaveURL(/#runs\/[^/]+$/, { timeout: 600_000 });
  await expect(page.getByRole("heading", { name: model })).toBeVisible();
  await expect(page.getByRole("heading", { name: "Quality" })).toBeVisible();
  await expect(page.getByRole("heading", { name: "Samples" })).toBeVisible();

  const runUrl = page.url();
  await page.reload();
  await expect(page).toHaveURL(runUrl);
  await expect(page.getByRole("heading", { name: model })).toBeVisible();

  const sampleEvidenceLink = page.getByRole("link", { name: "Inspect sample evidence" }).first();
  await expect(sampleEvidenceLink).toBeVisible();
  await sampleEvidenceLink.click();

  await expect(page).toHaveURL(/#runs\/[^/]+\/samples\//);
  await expect(page.getByRole("heading", { name: "Model exchange" })).toBeVisible();
  await expect(page.getByText("Evidence-rich local content", { exact: true })).toBeVisible();
  await expect(page.getByRole("heading", { name: "Evaluator evidence" })).toBeVisible();
});
