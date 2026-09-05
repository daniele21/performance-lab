import { expect, test } from "@playwright/test";

const inferenceBaseUrl = process.env.PERFORMANCE_LAB_E2E_INFERENCE_BASE_URL;

if (!inferenceBaseUrl) {
  throw new Error("PERFORMANCE_LAB_E2E_INFERENCE_BASE_URL is required for packaged J9");
}

const inferenceUrl = new URL(inferenceBaseUrl);

test("J0/J9 distributed campaign: launch, connect, evaluate and compare one exact case", async ({
  page,
}) => {
  await page.goto("/#test-a-model");
  await expect(page.getByRole("heading", { name: "Test a model" })).toBeVisible();
  await expect(page.getByLabel("Model source")).toHaveValue("local");
  await page.getByLabel("Connection name").fill("Distributed artifact fixture");
  await expect(page.getByLabel("Server type")).toHaveValue("local_llm_server");
  await page.getByLabel("Host").fill(inferenceUrl.hostname);
  await page.getByLabel("Port").fill(inferenceUrl.port);
  await page.getByRole("button", { name: "Connect & discover" }).click();
  await expect(page.getByText("Connection discovered")).toBeVisible();
  await expect(page.getByLabel("Model", { exact: true })).toHaveValue("fixture-good");

  await page.goto("/#find-best-setup");
  await expect(page.getByRole("heading", { name: "Find best setup" })).toBeVisible();
  await expect(page.getByText("Structured document extraction")).toBeVisible();

  const targetSelect = page.getByLabel("Target / device");
  const discoveredTarget = targetSelect
    .locator("option")
    .filter({ hasText: "Distributed artifact fixture" });
  const discoveredTargetId = await discoveredTarget.getAttribute("value");
  expect(discoveredTargetId).not.toBeNull();
  await targetSelect.selectOption(discoveredTargetId!);
  await page.getByRole("button", { name: "Continue" }).click();

  await expect(page.getByRole("heading", { name: "Select models to compare" })).toBeVisible();
  await expect(page.getByText("fixture-good", { exact: true })).toBeVisible();
  await expect(page.getByText("fixture-bad", { exact: true })).toBeVisible();
  await page.getByRole("button", { name: "Continue" }).click();

  await expect(
    page.getByRole("heading", { name: "How thoroughly should we search?" }),
  ).toBeVisible();
  await expect(page.getByRole("radio", { name: /Quick/ })).toBeDisabled();
  await expect(page.getByRole("radio", { name: /Single configuration/ })).toBeChecked();
  await page.getByRole("button", { name: "Continue" }).click();

  await expect(page.getByRole("heading", { name: "Review your evaluation" })).toBeVisible();
  await expect(page.getByText("Ready to evaluate", { exact: true })).toBeVisible();
  await page.getByText("Technical details (advanced)", { exact: true }).click();
  await expect(page.getByText("strict-quality-dominance@1.0.0")).toBeVisible();
  await page.getByRole("button", { name: "Start evaluation" }).click();

  await expect(page).toHaveURL(/#campaigns\/[^/]+$/, { timeout: 120_000 });
  await expect(page.getByRole("heading", { name: "Evaluation complete" })).toBeVisible({
    timeout: 120_000,
  });
  await expect(
    page.getByText("No hidden weights · No universal score", { exact: false }),
  ).toBeVisible();
  await expect(page.getByText("No single recommended setup")).toBeVisible();
  await expect(
    page.getByText(
      "Candidates do not expose the same aggregate quality metrics, so no weighted or partial ranking is inferred.",
    ),
  ).toBeVisible();

  const campaignUrl = page.url();
  await page.reload();
  await expect(page).toHaveURL(campaignUrl);
  await expect(page.getByRole("heading", { name: "Evaluation complete" })).toBeVisible();

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

test("J1/J8: packaged manual test retains and explains exact sample evidence", async ({ page }) => {
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
  await expect(page.getByText("Quality", { exact: true })).toBeVisible();
  await expect(page.getByText("Correct", { exact: true })).toBeVisible();
  await expect(page.getByText("normalized_exact_match · 1 · 100%", { exact: true })).toBeVisible();

  const promptPanel = page.locator(".evidence-drilldown__panel").filter({
    has: page.getByText("Prompt sent to model", { exact: true }),
  });
  await expect(promptPanel.getByText("Reply with exactly: BLUE", { exact: true })).toBeVisible();

  const outputPanel = page.locator(".evidence-drilldown__panel").filter({
    has: page.getByText("Model output", { exact: true }),
  });
  await expect(outputPanel.getByText("BLUE", { exact: true })).toBeVisible();

  const expectedPanel = page.locator(".evidence-drilldown__panel").filter({
    has: page.getByText("Expected output", { exact: true }),
  });
  await expect(expectedPanel.getByText("BLUE", { exact: true })).toBeVisible();

  await expect(page.getByText("Evidence-rich local content", { exact: true })).toBeVisible();
  await expect(page.getByText("Content not retained")).toHaveCount(0);
  await expect(page.getByRole("heading", { name: "Evaluator evidence" })).toBeVisible();
});
