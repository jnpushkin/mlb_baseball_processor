import { defineConfig } from "@playwright/test";
const fixtureURL = `http://127.0.0.1:${process.env.MLB_BROWSER_TEST_PORT || "8769"}`;
export default defineConfig({
  testDir: "tests/browser",
  fullyParallel: false,
  use: { baseURL: fixtureURL, serviceWorkers: "block" },
  webServer: {
    command: "python3 scripts/serve_browser_fixture.py",
    url: fixtureURL,
    reuseExistingServer: false,
    timeout: 60000,
  },
  reporter: "list",
});
