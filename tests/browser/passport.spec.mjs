import { test, expect } from "@playwright/test";

test("dashboard starts without loading player statistics or award libraries", async ({
  page,
}) => {
  const json = [];
  page.on("request", (r) => {
    if (r.url().includes(".json")) json.push(r.url());
  });
  await page.goto("/#dashboard");
  await expect(
    page.getByText("Your latest visit", { exact: true }),
  ).toBeVisible();
  expect(json.some((u) => u.includes("data-index-"))).toBeTruthy();
  expect(
    json.some(
      (u) =>
        u.includes("data-playerGames-") || u.includes("data-awardChecklists-"),
    ),
  ).toBeFalsy();
});

test("search, player, game, and Back preserve entity routes", async ({
  page,
}) => {
  await page.goto("/#dashboard");
  await page
    .getByRole("textbox", { name: "Search players, games, and milestones" })
    .fill("Jose Ramirez");
  await page
    .locator("#global-search-results")
    .getByRole("button", { name: /José Ramírez/ })
    .click();
  await expect(
    page.getByRole("dialog", { name: "José Ramírez" }),
  ).toBeVisible();
  await page
    .getByRole("dialog")
    .getByRole("button", { name: /3-hit, HR/ })
    .first()
    .click();
  await expect(page.getByRole("dialog", { name: /SF at BAL/ })).toBeVisible();
  await page.goBack();
  await expect(
    page.getByRole("dialog", { name: "José Ramírez" }),
  ).toBeVisible();
  await page.goBack();
  await expect(
    page.getByRole("heading", { name: "Search your passport" }),
  ).toBeVisible();
  await expect(
    page.getByRole("textbox", { name: "Search query", exact: true }),
  ).toHaveValue("Jose Ramirez");
});

test("game URL opens directly and dialog traps focus", async ({ page }) => {
  await page.goto("/#dashboard?game=TEST2026");
  const dialog = page.getByRole("dialog", { name: /SF at BAL/ });
  await expect(dialog).toBeVisible();
  await expect(
    page.getByRole("button", { name: "Close game details" }),
  ).toBeFocused();
  await page.keyboard.press("Shift+Tab");
  await expect(dialog.locator(":focus")).toHaveCount(1);
  await page.keyboard.press("Escape");
  await expect(page.getByRole("dialog")).toHaveCount(0);
});

test("failed section is retryable without losing the dashboard", async ({
  page,
}) => {
  let failing = true;
  await page.route("**/data-playerGames-*.json", (r) =>
    failing ? r.fulfill({ status: 503, body: "unavailable" }) : r.continue(),
  );
  await page.goto("/#players");
  await expect(
    page.getByRole("button", { name: "Retry section" }),
  ).toBeVisible();
  failing = false;
  await page.getByRole("button", { name: "Retry section" }).click();
  await expect(
    page.getByRole("heading", { name: /Hitter Statistics/ }),
  ).toBeVisible();
});

test("mobile sorting, full details, and game rows remain accessible", async ({
  page,
}) => {
  await page.setViewportSize({ width: 390, height: 844 });
  await page.goto("/#players");
  await page
    .getByRole("combobox", { name: "Sort by", exact: true })
    .selectOption("hr");
  await page.getByText("All stats", { exact: true }).first().click();
  await expect(
    page.getByRole("link", { name: "José Ramírez", exact: true }).first(),
  ).toBeVisible();
  await page
    .getByRole("combobox", { name: "Main navigation", exact: true })
    .selectOption("gamelog");
  await expect(
    page.getByRole("button", { name: "Open", exact: true }).first(),
  ).toBeVisible();
  expect(
    await page.evaluate(
      () => document.documentElement.scrollWidth <= window.innerWidth,
    ),
  ).toBeTruthy();
});

test("private journal survives reload and is not in the shared route", async ({
  page,
}) => {
  await page.goto("/#dashboard/journal");
  await page
    .getByLabel("Notes", { exact: true })
    .fill("Private regression note");
  await page.getByRole("button", { name: "Save journal", exact: true }).click();
  await expect(
    page.getByRole("status").filter({ hasText: "Saved on this device" }),
  ).toBeVisible();
  await page.reload();
  await expect(page.getByLabel("Notes", { exact: true })).toHaveValue(
    "Private regression note",
  );
  expect(page.url()).not.toContain("Private");
});

test("Back restores a default subtab and saved views restore scope", async ({
  page,
}) => {
  await page.goto("/#players");
  await page.getByRole("heading", { name: /Hitter Statistics/ }).waitFor();
  await page.getByRole("button", { name: "Pitchers", exact: true }).click();
  await expect(
    page.getByRole("heading", { name: /Pitcher Statistics/ }),
  ).toBeVisible();
  await page.goBack();
  await expect(
    page.getByRole("heading", { name: /Hitter Statistics/ }),
  ).toBeVisible();
  await page.getByRole("tab", { name: "Dashboard", exact: true }).click();
  await page.locator("summary").filter({ hasText: "Browse:" }).click();
  await page
    .getByRole("combobox", { name: "Season scope", exact: true })
    .selectOption("2025");
  await page
    .getByRole("textbox", { name: "Saved view name", exact: true })
    .fill("My 2025");
  await page.getByRole("button", { name: "Save view", exact: true }).click();
  await page.getByRole("button", { name: "Reset scope", exact: true }).click();
  await page.getByRole("button", { name: "Saved views", exact: true }).click();
  await page.getByRole("button", { name: "My 2025", exact: true }).click();
  await expect(page).toHaveURL(/year=2025/);
  await expect(
    page.getByText("Your latest visit", { exact: true }),
  ).toBeVisible();
});

test.describe("explicit offline recaps", () => {
  test.use({ serviceWorkers: "allow" });
  test("a saved game reloads with its box score while offline", async ({
    page,
    context,
  }) => {
    await page.goto("/#dashboard?game=TEST2026");
    await page
      .getByRole("button", { name: "Save offline", exact: true })
      .click();
    await expect(
      page
        .getByRole("status")
        .filter({ hasText: "Game saved for offline reading" }),
    ).toBeVisible();
    await context.setOffline(true);
    await page.reload();
    await expect(page.getByRole("dialog", { name: /SF at BAL/ })).toBeVisible();
    await expect(
      page.getByRole("heading", { name: "SF Batting", exact: true }),
    ).toBeVisible();
    await expect(
      page
        .getByRole("dialog")
        .getByRole("link", { name: "José Ramírez", exact: true }),
    ).toBeVisible();
  });
});
