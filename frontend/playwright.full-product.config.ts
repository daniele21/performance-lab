import { defineConfig } from "@playwright/test";

const baseURL = process.env.PERFORMANCE_LAB_E2E_BASE_URL;
const outputDir =
  process.env.PERFORMANCE_LAB_PACKAGED_E2E_OUTPUT_DIR ?? "test-results-full-product/artifacts";
const reportFile =
  process.env.PERFORMANCE_LAB_PACKAGED_E2E_REPORT ?? "test-results-full-product/report.json";

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
  reporter: [["line"], ["json", { outputFile: reportFile }]],
  outputDir,
  use: {
    baseURL,
    browserName: "chromium",
    trace: "on",
    screenshot: "on",
    video: "on",
  },
});
