import { expect, test } from "@playwright/test";

test("J1: packaged product completes and persists a real evaluation workflow", async ({ page }) => {
  await page.goto("/#test-a-model");
  await expect(page.getByRole("heading", { name: "Test a model" })).toBeVisible();

  await page.getByLabel("Model ID").fill("fixture-good");
  await page.getByRole("button", { name: "Continue" }).click();
  await expect(page.getByRole("heading", { name: "What do you want to learn?" })).toBeVisible();

  await page.getByRole("button", { name: "Continue" }).click();
  await expect(page.getByRole("heading", { name: "Test settings" })).toBeVisible();

  await page.getByRole("button", { name: "Continue" }).click();
  await expect(page.getByText("Preflight passed")).toBeVisible();
  await page.getByRole("button", { name: "Run test" }).click();

  await expect(page).toHaveURL(/#runs\/[^/]+$/, { timeout: 120_000 });
  await expect(page.getByRole("heading", { name: "fixture-good" })).toBeVisible();
  await expect(page.getByRole("heading", { name: "Quality" })).toBeVisible();

  const persistedResultUrl = page.url();
  await page.reload();
  await expect(page).toHaveURL(persistedResultUrl);
  await expect(page.getByRole("heading", { name: "fixture-good" })).toBeVisible();
});
