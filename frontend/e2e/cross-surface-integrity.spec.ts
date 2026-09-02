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
    await fulfillJson(route, []);
  });
}

async function assertNoDocumentOverflow(page: Page) {
  const overflow = await page.evaluate(
    () => document.documentElement.scrollWidth > document.documentElement.clientWidth + 1,
  );
  expect(overflow).toBe(false);
}

async function assertAriaReferencesResolve(page: Page) {
  const unresolved = await page
    .locator("[aria-labelledby], [aria-describedby]")
    .evaluateAll((elements) =>
      elements.flatMap((element) => {
        const references = ["aria-labelledby", "aria-describedby"] as const;
        return references.flatMap((attribute) => {
          const value = element.getAttribute(attribute);
          if (!value) return [];
          return value
            .split(/\s+/)
            .filter(Boolean)
            .filter((id) => !document.getElementById(id))
            .map((id) => ({
              attribute,
              id,
              tag: element.tagName.toLowerCase(),
            }));
        });
      }),
    );
  expect(unresolved).toEqual([]);
}

const ROUTES = [
  "overview",
  "test-a-model",
  "runs",
  "compare",
  "benchmarks",
  "datasets",
  "evaluators",
  "baselines",
  "regression-policies",
  "model-connections",
  "devices-targets",
  "advanced",
] as const;

test("minimum desktop routes keep valid ARIA references and bounded horizontal layout", async ({
  page,
}) => {
  await installEmptyProductFixture(page);
  await page.setViewportSize({ width: 1024, height: 800 });

  for (const route of ROUTES) {
    await page.goto(`/#${route}`);
    await expect(page.getByRole("main")).toBeVisible();
    await assertAriaReferencesResolve(page);
    await assertNoDocumentOverflow(page);
  }
});
