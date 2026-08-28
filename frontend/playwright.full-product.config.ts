import { defineConfig } from "@playwright/test";

const baseURL = process.env.PERFORMANCE_LAB_E2E_BASE_URL;

if (!baseURL) {
  throw new Error("PERFORMANCE_LAB_E2E_BASE_URL is required for packaged full-product E2E");
}

export default defineConfig({
  testDir: "./e2e",
  testMatch: "full-product.spec.ts",
  fullyParallel: false,
  workers: 1,
  retries: 0,
  timeout: 120_000,
  expect: { timeout: 15_000 },
  reporter: [["line"]],
  outputDir: "test-results-full-product",
  use: {
    baseURL,
    browserName: "chromium",
    trace: "retain-on-failure",
    screenshot: "only-on-failure",
    video: "off",
  },
});
