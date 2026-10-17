import { defineConfig } from "@playwright/test";
const port = Number(process.env.READINESS_BROWSER_PORT ?? "18765");
const root = process.env.READINESS_BROWSER_ROOT;
if (!root) throw new Error("Use scripts/check_frontend.py --suite browser --out PATH");
export default defineConfig({
  testDir: "./tests/browser",
  testMatch: "**/*.spec.js",
  workers: 1,
  retries: 0,
  timeout: 40000,
  expect: { timeout: 12000 },
  reporter: [["list"], ["junit"]],
  outputDir: process.env.READINESS_BROWSER_ARTIFACTS,
  use: {
    baseURL: `http://127.0.0.1:${port}`,
    viewport: { width: 1280, height: 900 },
    screenshot: "only-on-failure",
    trace: "retain-on-failure",
  },
  webServer: {
    command: `uv run --frozen python -m scripts.browser_fixture --port ${port} --root ${JSON.stringify(root)}`,
    url: `http://127.0.0.1:${port}/health`,
    reuseExistingServer: false,
    timeout: 30000,
    gracefulShutdown: { signal: "SIGTERM", timeout: 12000 },
  },
});
