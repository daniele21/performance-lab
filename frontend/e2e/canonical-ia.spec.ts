import { expect, test, type Page, type Route } from "@playwright/test";

async function fulfillJson(route: Route, payload: unknown) {
  await route.fulfill({
    status: 200,
    contentType: "application/json",
    body: JSON.stringify(payload),
  });
}

async function installEmptyProductFixture(page: Page) {
  await page.route("**/api/v1/**", async (route) => {
    const path = new URL(route.request().url()).pathname;

    if (
      path === "/api/v1/tested-models" ||
      path === "/api/v1/runs" ||
      path === "/api/v1/benchmarks" ||
      path === "/api/v1/datasets" ||
      path === "/api/v1/evaluators" ||
      path === "/api/v1/baselines" ||
      path === "/api/v1/regression-policies" ||
      path === "/api/v1/targets"
    ) {
      await fulfillJson(route, []);
      return;
    }

    await route.fulfill({
      status: 500,
      contentType: "application/json",
      body: JSON.stringify({ detail: `Unhandled canonical IA fixture route: ${path}` }),
    });
  });
}

test("canonical desktop IA preserves converged and staged secondary navigation", async ({ page }) => {
  await page.setViewportSize({ width: 1536, height: 960 });
  await installEmptyProductFixture(page);
  await page.goto("/#overview");

  const primary = page.getByRole("navigation", { name: "Primary navigation" });
  await expect(primary.getByRole("link")).toHaveText([
    "Overview",
    "Find best setup",
    "Test a model",
    "Runs",
    "Compare",
  ]);

  const library = page.getByRole("navigation", { name: "Library" });
  const settings = page.getByRole("navigation", { name: "Settings" });
  const benchmarks = library.getByRole("link", { name: "Benchmarks" });
  const evaluators = library.getByRole("link", { name: "Evaluators" });
  const modelConnections = settings.getByRole("link", { name: "Model connections" });
  await expect(library).toBeVisible();
  await expect(settings).toBeVisible();

  for (const pendingLabel of ["Models", "Evidence"]) {
    await expect(library.getByText(pendingLabel, { exact: true })).toBeVisible();
    await expect(library.getByRole("link", { name: pendingLabel })).toHaveCount(0);
  }
  for (const pendingLabel of ["Evidence retention", "Accessibility"]) {
    await expect(settings.getByText(pendingLabel, { exact: true })).toBeVisible();
    await expect(settings.getByRole("link", { name: pendingLabel })).toHaveCount(0);
  }
  await expect(library.getByText("Pending", { exact: true })).toHaveCount(2);
  await expect(settings.getByText("Pending", { exact: true })).toHaveCount(2);

  await benchmarks.click();
  await expect(page).toHaveURL(/#benchmarks$/);
  await expect(
    page.getByRole("heading", { name: "Benchmarks", exact: true, level: 1 }),
  ).toBeVisible();
  await expect(benchmarks).toHaveAttribute("aria-current", "page");

  await evaluators.click();
  await expect(page).toHaveURL(/#evaluators$/);
  await expect(
    page.getByRole("heading", { name: "Evaluators", exact: true, level: 1 }),
  ).toBeVisible();
  await expect(evaluators).toHaveAttribute("aria-current", "page");

  await modelConnections.click();
  await expect(page).toHaveURL(/#model-connections$/);
  await expect(
    page.getByRole("heading", { name: "Model connections", exact: true, level: 1 }),
  ).toBeVisible();
  await expect(modelConnections).toHaveAttribute("aria-current", "page");

  await page.goto("/#test-suites");
  await expect(
    page.getByRole("heading", { name: "Benchmarks", exact: true, level: 1 }),
  ).toBeVisible();
  await expect(benchmarks).toHaveAttribute("aria-current", "page");

  await page.goto("/#endpoints");
  await expect(
    page.getByRole("heading", { name: "Model connections", exact: true, level: 1 }),
  ).toBeVisible();
  await expect(modelConnections).toHaveAttribute("aria-current", "page");
});
