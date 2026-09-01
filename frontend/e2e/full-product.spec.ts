import { expect, test } from "@playwright/test";

const inferenceBaseUrl = process.env.PERFORMANCE_LAB_E2E_INFERENCE_BASE_URL;

if (!inferenceBaseUrl) {
  throw new Error("PERFORMANCE_LAB_E2E_INFERENCE_BASE_URL is required for packaged J9");
}

test("J0/J9 campaign: packaged product executes the plan and compares one exact case", async ({
  page,
}) => {
  const probe = await page.request.post("/api/v1/endpoint-probes", {
    data: {
      display_name: "J9 discovered fixture",
      base_url: inferenceBaseUrl,
      server_type: "local_llm_server",
      timeout_seconds: 5,
    },
  });
  expect(probe.ok()).toBeTruthy();
  const discovered = (await probe.json()) as { models: Array<{ model_id: string }> };
  expect(discovered.models.map((model) => model.model_id)).toEqual(["fixture-good", "fixture-bad"]);

  await page.goto("/#find-best-setup");
  await expect(page.getByRole("heading", { name: "Find best setup" })).toBeVisible();
  await expect(page.getByText("Structured document extraction")).toBeVisible();

  await page.getByRole("button", { name: "Continue" }).click();
  const targetSelect = page.getByLabel("Target / device");
  const discoveredTarget = targetSelect
    .locator("option")
    .filter({ hasText: "J9 discovered fixture" });
  const discoveredTargetId = await discoveredTarget.getAttribute("value");
  expect(discoveredTargetId).not.toBeNull();
  await targetSelect.selectOption(discoveredTargetId!);

  await expect(page.getByText("fixture-good", { exact: true })).toBeVisible();
  await expect(page.getByText("fixture-bad", { exact: true })).toBeVisible();
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
  await expect(
    page.getByText(
      "Candidates do not expose the same aggregate quality metrics, so no weighted or partial ranking is inferred.",
    ),
  ).toBeVisible();

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
  const goodRun = page.getByRole("article").filter({ hasText: "fixture-good" });
  const runLink = goodRun.getByRole("button", { name: "Open immutable Run" });
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

  await expect(page.getByLabel("Model", { exact: true })).toHaveValue("fixture-good");
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
  await expect(page.getByRole("heading", { name: "Model exchange" })).toBeVisible();
  await expect(page.getByText("Prompt sent to model", { exact: true })).toBeVisible();
  await expect(page.getByText("Model output", { exact: true })).toBeVisible();
  await expect(page.getByText("Expected output", { exact: true })).toBeVisible();
  await expect(page.getByText("Content not retained")).toHaveCount(2);
  await expect(page.getByRole("heading", { name: "Evaluator evidence" })).toBeVisible();
});
