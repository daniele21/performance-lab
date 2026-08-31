import { defineConfig } from "@playwright/test";

const outputDir =
  process.env.PERFORMANCE_LAB_PRE_REAL_OUTPUT_DIR ?? "test-results-pre-real/artifacts";
const reportFile =
  process.env.PERFORMANCE_LAB_PRE_REAL_REPORT ?? "test-results-pre-real/report.json";

export default defineConfig({
  testDir: "./e2e",
  testIgnore: ["full-product.spec.ts", "visual-acceptance.spec.ts"],
  fullyParallel: false,
  workers: 1,
  retries: 0,
  timeout: 60_000,
  expect: { timeout: 8_000 },
  reporter: [["line"], ["json", { outputFile: reportFile }]],
  outputDir,
  use: {
    baseURL: "http://127.0.0.1:4173",
    browserName: "chromium",
    viewport: { width: 1280, height: 900 },
    locale: "en-US",
    timezoneId: "UTC",
    trace: "on",
    screenshot: "on",
    video: "off",
  },
  webServer: {
    command: "npm run build && npm run preview -- --port 4173 --strictPort",
    port: 4173,
    reuseExistingServer: false,
    timeout: 120_000,
  },
});
