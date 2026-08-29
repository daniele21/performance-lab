import { expect, test } from "@playwright/test";

test("J0 UX: use-case-first best setup journey is explicit and truthfully blocked", async ({ page }) => {
  await page.goto("/#find-best-setup");

  await expect(page.getByRole("heading", { name: "Find best setup" })).toBeVisible();
  await expect(page.getByRole("navigation", { name: "Primary navigation" })).toContainText(
    "Find best setup",
  );
  await expect(page.getByText("Automatic campaign setup")).toBeVisible();
  await expect(page.getByText("Engine pending")).toBeVisible();
  await expect(page.getByText("Different quantizations", { exact: false })).toBeVisible();
  await expect(page.getByRole("button", { name: "Start evaluation campaign" })).toBeDisabled();
  await expect(page.getByRole("button", { name: "Manual test" })).toBeVisible();
});
