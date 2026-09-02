import { defineConfig } from "@playwright/test";

const baseURL = process.env.PERFORMANCE_LAB_REAL_E2E_BASE_URL;
const outputDir =
  process.env.PERFORMANCE_LAB_REAL_E2E_OUTPUT_DIR ?? "test-results-real-runtime/artifacts";
const reportFile =
  process.env.PERFORMANCE_LAB_REAL_E2E_REPORT ?? "test-results-real-runtime/report.json";

if (!baseURL) {
  throw new Error("PERFORMANCE_LAB_REAL_E2E_BASE_URL is required for real-runtime E2E");
}
if (!process.env.PERFORMANCE_LAB_REAL_E2E_MODEL) {
  throw new Error("PERFORMANCE_LAB_REAL_E2E_MODEL is required for real-runtime E2E");
}

export default defineConfig({
  testDir: "../tests/real_runtime",
  testMatch: "value01_browser.spec.ts",
  fullyParallel: false,
  workers: 1,
  retries: 0,
  timeout: 600_000,
  expect: { timeout: 30_000 },
  reporter: [["line"], ["json", { outputFile: reportFile }]],
  outputDir,
  use: {
    baseURL,
    browserName: "chromium",
    viewport: { width: 1536, height: 960 },
    locale: "en-US",
    timezoneId: "UTC",
    trace: "on",
    screenshot: "on",
    video: "on",
  },
});
