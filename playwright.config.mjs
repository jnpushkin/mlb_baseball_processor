import { defineConfig } from "@playwright/test";
export default defineConfig({
  testDir: "tests/browser",
  fullyParallel: false,
  use: { baseURL: "http://127.0.0.1:8769", serviceWorkers: "block" },
  webServer: {
    command: "python3 scripts/serve_browser_fixture.py",
    url: "http://127.0.0.1:8769",
    reuseExistingServer: !process.env.CI,
    timeout: 60000,
  },
  reporter: "list",
});
