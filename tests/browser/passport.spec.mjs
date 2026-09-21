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

test("discovery matchups link to the exact witnessed play", async ({
  page,
}) => {
  await page.goto("/#dashboard/discover");
  await expect(
    page.getByRole("heading", { name: "Play explorer", exact: true }),
  ).toBeVisible();
  await page.getByRole("button", { name: "Matchups", exact: true }).click();
  await expect(
    page.getByRole("heading", { name: "Batter vs. pitcher history" }),
  ).toBeVisible();
  await expect(page.locator('th[aria-sort="descending"]')).toHaveText(/PA/);
  await page.getByRole("button", { name: "See plays", exact: true }).click();
  await expect(page).toHaveURL(/pitcher=pitcher/);
  await page
    .getByRole("button", { name: "Open game", exact: true })
    .first()
    .click();
  await expect(page).toHaveURL(/playIndex=0/);
  await expect(page.locator("#pbp-play-TEST2026-0")).toBeVisible();
  await expect(page.locator("#pbp-play-TEST2026-0")).toHaveClass(/ring-inset/);
});

test("all discovery sections render on a phone without overflowing", async ({
  page,
}) => {
  await page.setViewportSize({ width: 390, height: 844 });
  await page.goto("/#dashboard/discover");
  const sections = [
    ["Shared games", "Players who shared your games"],
    ["Game stories", "Game stories"],
    ["Career share", "Your share of a career"],
    ["Pitch arsenals", "Pitch arsenals"],
    ["Personal milestones", "Personal milestones"],
    ["Then & now", "Then & now"],
    ["Trips", "Your baseball trips"],
    ["Player journeys", "Player journeys"],
    ["Trivia", "Personal baseball trivia"],
  ];
  for (const [button, heading] of sections) {
    await page
      .getByRole("combobox", { name: "Discovery tool", exact: true })
      .selectOption({ label: button });
    await expect(
      page.getByRole("heading", { name: heading, exact: true }),
    ).toBeVisible();
    expect(
      await page.evaluate(
        () => document.documentElement.scrollWidth <= window.innerWidth,
      ),
    ).toBeTruthy();
  }
});

test("career verification recalculates the share when Browse scope changes", async ({
  page,
}) => {
  await page.route("**/people/123/stats?**", (r) =>
    r.fulfill({
      json: {
        stats: [
          {
            group: { displayName: "hitting" },
            splits: [{ stat: { hits: 90 } }],
          },
        ],
      },
    }),
  );
  await page.goto("/#dashboard/discover?tool=career");
  await expect(
    page.getByRole("cell", { name: "Refresh required", exact: true }),
  ).toBeVisible();
  await page
    .getByRole("button", { name: "Verify current total", exact: true })
    .click();
  await expect(
    page.getByRole("cell", { name: "10.00", exact: true }),
  ).toBeVisible();
  await page.locator("summary").filter({ hasText: "Browse:" }).click();
  await page
    .getByRole("combobox", { name: "Season scope", exact: true })
    .selectOption("2026");
  await expect(
    page.getByRole("cell", { name: "3.33", exact: true }),
  ).toBeVisible();
});

test("compound queries survive reload and malformed query links stay usable", async ({
  page,
}) => {
  await page.goto(
    "/#players/explorer?conditions=%7B%22bad%22%3Atrue%7D&filters=3",
  );
  await page
    .getByRole("button", { name: "3+ hits and a steal", exact: true })
    .click();
  await expect(
    page.getByLabel("Condition 1 value", { exact: true }),
  ).toHaveValue("3");
  await expect(
    page.getByLabel("Condition 2 value", { exact: true }),
  ).toHaveValue("1");
  await page.reload();
  await expect(
    page.getByLabel("Condition 1 value", { exact: true }),
  ).toHaveValue("3");
  await page.getByLabel("Query name", { exact: true }).fill("Hits and steals");
  await page.getByRole("button", { name: "Save query", exact: true }).click();
  await expect(
    page.getByRole("status").filter({ hasText: "Saved in Dashboard" }),
  ).toBeVisible();
});

test("trip fields and itinerary survive a private backup import", async ({
  page,
}) => {
  await page.goto("/#dashboard/journal");
  const backup = {
    schemaVersion: 1,
    journal: {
      TEST2026: {
        notes: "Imported note",
        trip: "Regression trip",
        rating: "5",
        ticketCost: "42.50",
        currency: "USD",
      },
    },
    itinerary: [
      { gamePk: 1, date: "2026-09-21", venue: "Test park", matchup: "A @ B" },
    ],
  };
  await page.getByLabel("Import backup", { exact: true }).setInputFiles({
    name: "private-test.json",
    mimeType: "application/json",
    buffer: Buffer.from(JSON.stringify(backup)),
  });
  await expect(page.getByLabel("Trip name", { exact: true })).toHaveValue(
    "Regression trip",
  );
  await expect(page.getByLabel("Ticket cost", { exact: true })).toHaveValue(
    "42.50",
  );
  await page.reload();
  await expect(page.getByLabel("Game rating", { exact: true })).toHaveValue(
    "5",
  );
  await page.getByRole("button", { name: "Next visit", exact: true }).click();
  await expect(page.getByText("A @ B", { exact: false })).toBeVisible();
  await page.getByRole("button", { name: "Discover", exact: true }).click();
  await page.getByRole("button", { name: "Trips", exact: true }).click();
  await expect(page.getByText("USD 42.50", { exact: true })).toBeVisible();
});

test("date range schedule can be saved as an itinerary and exported", async ({
  page,
}) => {
  await page.route("**/api/v1/schedule?**", (r) =>
    r.fulfill({
      json: {
        dates: [
          {
            games: [
              {
                gamePk: 999,
                gameDate: "2026-09-21T23:05:00Z",
                officialDate: "2026-09-21",
                venue: { name: "Test park" },
                teams: {
                  away: {
                    team: {
                      id: 137,
                      name: "San Francisco Giants",
                      abbreviation: "SF",
                    },
                  },
                  home: {
                    team: {
                      id: 110,
                      name: "Baltimore Orioles",
                      abbreviation: "BAL",
                    },
                  },
                },
                status: { detailedState: "Scheduled" },
              },
            ],
          },
        ],
      },
    }),
  );
  await page.goto("/#dashboard/plan");
  await page.getByLabel("Planning date", { exact: true }).fill("2026-09-21");
  await page
    .getByLabel("Planning end date", { exact: true })
    .fill("2026-09-23");
  await page
    .getByRole("button", { name: "Find scheduled games", exact: true })
    .click();
  await page
    .getByRole("button", { name: "Add to itinerary", exact: true })
    .click();
  await expect(
    page.getByRole("button", { name: "Add to itinerary", exact: true }),
  ).toBeDisabled();
  const download = page.waitForEvent("download");
  await page
    .getByRole("button", { name: "Export itinerary calendar", exact: true })
    .click();
  expect((await download).suggestedFilename()).toMatch(/\.ics$/);
});

test("co-appearances show shared games independently of plate appearances", async ({
  page,
}) => {
  await page.goto("/#dashboard/discover?tool=shared");
  await page
    .getByLabel("Shared games player", { exact: true })
    .selectOption("jose");
  await page
    .getByRole("button", { name: "See shared games", exact: true })
    .click();
  await expect(
    page.getByRole("dialog", { name: "Shared games", exact: true }),
  ).toBeVisible();
  await page
    .getByRole("dialog")
    .getByRole("button", { name: "Open game", exact: true })
    .click();
  await expect(page.getByRole("dialog", { name: /SF at BAL/ })).toBeVisible();
});

test("Mexico City attendance is recognized under both stadium names", async ({
  page,
}) => {
  await page.goto("/#dashboard/plan");
  const parks = page
    .locator("details")
    .filter({ hasText: "Unvisited current ballparks" });
  await parks.locator("summary").click();
  await expect(parks).not.toContainText("Estadio Alfredo Harp Helu");
  await expect(parks).toContainText("Tokyo Dome");
});
