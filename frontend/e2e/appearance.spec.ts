import { expect, test } from "@playwright/test";

test.use({ colorScheme: "dark" });

test("Appearance defaults to Light, persists explicit choice and lets System follow the OS", async ({
  page,
}) => {
  await page.goto("/#appearance");

  await expect(page.locator("html")).toHaveAttribute("data-theme", "light");
  await expect(page.getByRole("radio", { name: "Light" })).toBeChecked();
  await expect
    .poll(() =>
      page.evaluate(() =>
        getComputedStyle(document.documentElement).getPropertyValue("--color-surface").trim(),
      ),
    )
    .toBe("#f6f8fa");

  await page.getByRole("radio", { name: "Dark" }).check();
  await expect(page.locator("html")).toHaveAttribute("data-theme", "dark");
  await expect
    .poll(() => page.evaluate(() => localStorage.getItem("performance-lab.theme")))
    .toBe("dark");

  await page.reload();
  await expect(page.locator("html")).toHaveAttribute("data-theme", "dark");
  await expect(page.getByRole("radio", { name: "Dark" })).toBeChecked();

  await page.getByRole("radio", { name: "System" }).check();
  await expect(page.locator("html")).toHaveAttribute("data-theme", "system");
  await expect
    .poll(() =>
      page.evaluate(() =>
        getComputedStyle(document.documentElement).getPropertyValue("--color-surface").trim(),
      ),
    )
    .toBe("#080a0d");

  await page.emulateMedia({ colorScheme: "light" });
  await expect
    .poll(() =>
      page.evaluate(() =>
        getComputedStyle(document.documentElement).getPropertyValue("--color-surface").trim(),
      ),
    )
    .toBe("#f6f8fa");
});
