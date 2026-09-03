import { expect, test } from "@playwright/test";
import { writeFileSync } from "node:fs";

const rawModels = process.env.PERFORMANCE_LAB_VALUE02_MODELS;
const resultPath = process.env.PERFORMANCE_LAB_VALUE02_BROWSER_RESULT;

if (!rawModels) {
  throw new Error("PERFORMANCE_LAB_VALUE02_MODELS is required for VALUE-02 real browser E2E");
}
if (!resultPath) {
  throw new Error("PERFORMANCE_LAB_VALUE02_BROWSER_RESULT is required for VALUE-02 real browser E2E");
}

const models = rawModels
  .split(",")
  .map((item) => item.trim())
  .filter(Boolean);

if (models.length < 2 || new Set(models).size !== models.length) {
  throw new Error("VALUE-02 requires at least two unique requested models");
}

test("VALUE-02 real browser: compare real models and inspect the canonical decision", async ({
  page,
}) => {
  await page.goto("/#find-best-setup");
  await expect(page.getByRole("heading", { name: "Find best setup" })).toBeVisible();
  await page.getByRole("button", { name: "Continue" }).click();

  await expect(page.getByRole("heading", { name: "Select models to compare" })).toBeVisible();
  const rows = page.locator(".best-setup-model-row");
  const count = await rows.count();
  const visibleModels: string[] = [];
  for (let index = 0; index < count; index += 1) {
    const row = rows.nth(index);
    const modelId = (await row.locator("strong").innerText()).trim();
    visibleModels.push(modelId);
    const checkbox = row.locator('input[type="checkbox"]');
    const shouldSelect = models.includes(modelId);
    if ((await checkbox.isChecked()) !== shouldSelect) await checkbox.click();
  }
  for (const model of models) expect(visibleModels).toContain(model);
  await expect(page.getByText(`${models.length} selected for comparison`, { exact: true })).toBeVisible();
  await page.getByRole("button", { name: "Continue" }).click();

  await expect(
    page.getByRole("heading", { name: "How thoroughly should we search?" }),
  ).toBeVisible();
  const fixed = page.getByRole("radio", { name: /Single configuration/ });
  if (await fixed.isVisible()) await fixed.check();
  await page.getByRole("button", { name: "Continue" }).click();

  await expect(page.getByRole("heading", { name: "Review your evaluation" })).toBeVisible();
  await expect(page.getByText("Ready to evaluate", { exact: true })).toBeVisible();
  await expect(page.getByText("strict-quality-dominance@1.0.0")).toBeVisible();
  await page.getByRole("button", { name: "Start evaluation" }).click();

  await expect(page).toHaveURL(/#campaigns\/[^/]+$/, { timeout: 30_000 });
  const campaignId = page.url().split("#campaigns/")[1];
  if (!campaignId) throw new Error("campaign id is missing from VALUE-02 browser route");

  await expect(page.getByRole("heading", { name: "Evaluation complete" })).toBeVisible({
    timeout: 1_800_000,
  });
  await expect(page.getByLabel("Campaign results")).toBeVisible();
  await expect(page.getByText("Strict quality dominance", { exact: true })).toBeVisible();
  await expect(page.getByText("No hidden weights · No universal score", { exact: false })).toBeVisible();
  for (const model of models) {
    await expect(page.getByText(model, { exact: true }).first()).toBeVisible();
  }

  const recommended = page.getByRole("button", { name: "Inspect recommended Run" });
  const noRank = page.getByText("No single recommended setup", { exact: true });
  const recommendationState = (await recommended.isVisible()) ? "recommended" : "no_rank";
  if (recommendationState === "recommended") {
    await expect(recommended).toBeVisible();
  } else {
    await expect(noRank).toBeVisible();
  }

  const compare = page.getByRole("button", { name: "Compare across candidates" }).first();
  await expect(compare).toBeVisible({ timeout: 30_000 });
  await compare.click();
  await expect(page).toHaveURL(/#campaigns\/[^/]+\/cases\//);
  for (const model of models.slice(0, 2)) {
    await expect(page.getByText(model, { exact: true })).toBeVisible();
  }

  writeFileSync(
    resultPath,
    `${JSON.stringify(
      {
        schema_version: 1,
        campaign_id: campaignId,
        requested_models: models,
        recommendation_state: recommendationState,
        case_route: new URL(page.url()).hash,
      },
      null,
      2,
    )}\n`,
    "utf-8",
  );
});
