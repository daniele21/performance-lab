import { expect, test } from "@playwright/test";

test("J0/J9 campaign: packaged product executes the plan and compares one exact case", async ({
  page,
}) => {
  await page.goto("/#find-best-setup");
  await expect(page.getByRole("heading", { name: "Find best setup" })).toBeVisible();
  await expect(page.getByText("Structured document extraction")).toBeVisible();

  await page.getByRole("button", { name: "Continue" }).click();
  await expect(page.getByText("fixture-good", { exact: true })).toBeVisible();
  await page.getByRole("button", { name: "Continue" }).click();

  await expect(page.getByRole("radio", { name: /Quick/ })).toBeDisabled();
  await page.getByRole("button", { name: "Build benchmark plan" }).click();

  await expect(page.getByRole("heading", { name: "Benchmark plan" })).toBeVisible();
  await expect(page.getByText("general-diagnostic-starter")).toBeVisible();
  await page.getByRole("button", { name: "Review campaign" }).click();

  await expect(page.getByRole("heading", { name: "Campaign review / estimate" })).toBeVisible();
  await expect(page.getByText("Plan frozen")).toBeVisible();
  await expect(page.getByText("Ready to run")).toBeVisible();
  await expect(page.getByText("strict-quality-dominance@1.0.0")).toBeVisible();
  await page.getByRole("button", { name: "Start evaluation campaign" }).click();

  await expect(page).toHaveURL(/#campaigns\/[^/]+$/, { timeout: 120_000 });
  await expect(page.getByRole("heading", { name: "Results" })).toBeVisible({ timeout: 120_000 });
  await expect(page.getByText("No hidden weights · No universal score")).toBeVisible();
  await expect(page.getByText("No single recommended winner")).toBeVisible();

  const campaignUrl = page.url();
  await page.reload();
  await expect(page).toHaveURL(campaignUrl);
  await expect(page.getByRole("heading", { name: "Results" })).toBeVisible();

  const compareCase = page.getByRole("button", { name: "Compare across candidates" }).first();
  await expect(compareCase).toBeVisible();
  await compareCase.click();
  await expect(page).toHaveURL(/#campaigns\/[^/]+\/cases\//);
  await expect(page.getByRole("heading", { name: "Candidate evidence" })).toBeVisible();
  await expect(page.getByText("fixture-good", { exact: true })).toBeVisible();
  await expect(page.getByText("fixture-bad", { exact: true })).toBeVisible();
  await expect(page.getByText("Content not retained").first()).toBeVisible();
  await expect(
    page.getByRole("link", { name: "Open exact sample evidence" }).first(),
  ).toBeVisible();

  await page.getByRole("link", { name: /Back to campaign results/ }).click();
  await expect(page).toHaveURL(campaignUrl);
  const runLink = page.getByRole("button", { name: "Open immutable Run" }).first();
  await expect(runLink).toBeVisible();
  await runLink.click();
  await expect(page).toHaveURL(/#runs\/[^/]+$/);
  await expect(page.getByRole("heading", { name: "fixture-good" })).toBeVisible();
});

test("J1/J8: packaged product completes, persists and drills into sample evidence", async ({
  page,
}) => {
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

  await expect(page.getByRole("heading", { name: "Samples" })).toBeVisible();
  const sampleEvidenceLink = page.getByRole("link", { name: "Inspect sample evidence" }).first();
  await expect(sampleEvidenceLink).toBeVisible();
  await sampleEvidenceLink.click();

  await expect(page).toHaveURL(/#runs\/[^/]+\/samples\//);
  await expect(page.getByRole("heading", { name: "Execution content" })).toBeVisible();
  await expect(page.getByText("Content not retained").first()).toBeVisible();
  await expect(page.getByRole("heading", { name: "Evaluator evidence" })).toBeVisible();
});
