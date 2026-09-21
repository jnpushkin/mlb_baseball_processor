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

test("Journal is removed and old links open the ballpark goals", async ({
  page,
}) => {
  await page.goto("/#dashboard/journal?journalGame=TEST2026");
  await expect(page).toHaveURL(/#dashboard\/plan$/);
  await expect(
    page.getByRole("heading", { name: "Your next ballpark visit" }),
  ).toBeVisible();
  await expect(
    page.getByRole("button", { name: "Journal", exact: true }),
  ).toHaveCount(0);
  const goal = page.getByRole("article", {
    name: "Orioles in every ballpark",
    exact: true,
  });
  await expect(goal.getByRole("progressbar")).toHaveAttribute("value", "1");
  await expect(goal.getByRole("progressbar")).toHaveAttribute("max", "30");
  await expect(
    page
      .getByRole("article", {
        name: "Orioles in every ballpark with Dad",
        exact: true,
      })
      .getByRole("progressbar"),
  ).toHaveAttribute("value", "0");
  await goal.getByText("Missing parks (29)", { exact: true }).click();
  await expect(goal).toContainText("Oracle Park");
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

test("Saved views imports private plans and preserves legacy backups", async ({
  page,
}) => {
  await page.goto("/#dashboard/saved");
  const backup = {
    schemaVersion: 1,
    journal: { TEST2026: { notes: "Legacy private note" } },
    views: [
      { name: "Imported season", route: { tab: "gamelog", year: "2026" } },
    ],
    itinerary: [
      {
        gamePk: 1,
        date: "2026-09-21",
        venue: "Test park",
        matchup: "A @ B",
        withDad: true,
      },
    ],
  };
  await page.getByLabel("Import backup", { exact: true }).setInputFiles({
    name: "private-test.json",
    mimeType: "application/json",
    buffer: Buffer.from(JSON.stringify(backup)),
  });
  await expect(
    page.getByText("Backup imported. Existing saved items were preserved."),
  ).toBeVisible();
  await expect(
    page.getByRole("button", { name: "Imported season", exact: true }),
  ).toBeVisible();
  expect(
    await page.evaluate(
      () => JSON.parse(localStorage.getItem("passport:journal")).TEST2026.notes,
    ),
  ).toBe("Legacy private note");
  await page.getByRole("button", { name: "Next visit", exact: true }).click();
  await expect(page.getByText(/A @ B.*With Dad/)).toBeVisible();
  await page.reload();
  await expect(page.getByText(/A @ B.*With Dad/)).toBeVisible();
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
                venue: { name: "Fenway Park" },
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

test("Mexico City is a separate completed visit rather than a missing current home park", async ({
  page,
}) => {
  await page.goto("/#dashboard/plan");
  const goal = page.getByRole("article", {
    name: "Orioles in every ballpark",
    exact: true,
  });
  await goal.getByText("Other parks visited (1)", { exact: true }).click();
  await expect(goal).toContainText("Estadio Alfredo Harp Helu");
  await expect(goal.getByRole("progressbar")).toHaveAttribute("max", "30");
});

for (const [route, heading] of [
  ["gamelog", /Game Log/],
  ["players", /Hitter Statistics/],
  ["players/awards", /No Award Data/],
  ["milestones", /No Milestones/],
]) {
  test(`expired release recovers ${route} without reloading the page`, async ({
    page,
  }) => {
    let boots = 0,
      refreshes = 0;
    await page.route("**/data-index-*.json", async (request) => {
      boots++;
      const old = await (await request.fetch()).json();
      for (const key of Object.keys(old.__libraries))
        old.__libraries[key] = `expired/${old.__libraries[key]}`;
      await request.fulfill({ json: old });
    });
    await page.route("**/expired/*.json", (request) =>
      request.fulfill({ status: 404, body: "expired release" }),
    );
    await page.route("**/data.json", (request) => {
      refreshes++;
      return request.continue();
    });
    await page.goto(`/#${route}?year=2026`);
    await expect(page.getByRole("heading", { name: heading })).toBeVisible();
    await expect(
      page.getByRole("button", { name: "Retry section" }),
    ).toHaveCount(0);
    await expect(page).toHaveURL(/year=2026/);
    expect(boots).toBe(1);
    expect(refreshes).toBe(1);
  });
}

test("expired boot index recovers a directly linked game", async ({ page }) => {
  await page.route("**/data-index-*.json", (r) =>
    r.fulfill({ status: 404, body: "expired release" }),
  );
  await page.goto("/#dashboard?game=TEST2026");
  await expect(page.getByRole("dialog", { name: /SF at BAL/ })).toBeVisible();
});

test("data recovery preserves an unsaved planning date range", async ({
  page,
}) => {
  await page.route("**/data-index-*.json", async (request) => {
    const old = await (await request.fetch()).json();
    old.__libraries.searchEvents = "expired-search.json";
    await request.fulfill({ json: old });
  });
  await page.route("**/expired-search.json", (request) =>
    request.fulfill({ status: 404, body: "expired" }),
  );
  await page.goto("/#dashboard/plan");
  await page.getByLabel("Planning date", { exact: true }).fill("2026-10-01");
  await page
    .getByLabel("Planning end date", { exact: true })
    .fill("2026-10-07");
  const refreshed = page.waitForResponse((response) =>
    response.url().endsWith("/data.json"),
  );
  await page
    .getByRole("textbox", { name: "Search players, games, and milestones" })
    .fill("Jose");
  await refreshed;
  await expect(page.getByLabel("Planning date", { exact: true })).toHaveValue(
    "2026-10-01",
  );
  await expect(
    page.getByLabel("Planning end date", { exact: true }),
  ).toHaveValue("2026-10-07");
});

test("planner ranks the three goals and adjusts for Dad on a phone", async ({
  page,
}) => {
  await page.setViewportSize({ width: 390, height: 844 });
  const game = (id, venue, orioles) => ({
    gamePk: id,
    officialDate: "2026-09-21",
    gameDate: `2026-09-21T${id === 1 ? "18" : "20"}:00:00Z`,
    venue: { name: venue },
    teams: {
      away: {
        team: {
          id: orioles ? 110 : 137,
          name: orioles ? "Baltimore Orioles" : "San Francisco Giants",
        },
      },
      home: { team: { id: 111, name: "Boston Red Sox" } },
    },
    status: { detailedState: "Scheduled" },
  });
  await page.route("**/api/v1/schedule?**", (request) =>
    request.fulfill({
      json: {
        dates: [
          {
            games: [
              game(1, "Fenway Park", false),
              game(2, "Wrigley Field", true),
              game(3, "Oriole Park at Camden Yards", true),
            ],
          },
        ],
      },
    }),
  );
  await page.goto("/#dashboard/plan?year=2026");
  await page
    .getByRole("button", { name: "Find scheduled games", exact: true })
    .click();
  const results = page.locator("#next-visit-schedule article");
  await expect(results).toHaveCount(3);
  await expect(results.first()).toContainText("Wrigley Field");
  await expect(results.first()).toContainText(
    "Orioles in every ballpark with Dad",
  );
  await page.getByLabel("Planning with Dad", { exact: true }).uncheck();
  await expect(results).toHaveCount(1);
  await expect(results.first()).toContainText("Wrigley Field");
  await expect(results.first()).not.toContainText("every ballpark with Dad");
  await page.getByLabel("Planning goal", { exact: true }).selectOption("dad");
  await expect(
    page.getByLabel("Planning with Dad", { exact: true }),
  ).toBeChecked();
  await expect(results).toHaveCount(3);
  expect(
    await page.evaluate(
      () => document.documentElement.scrollWidth <= innerWidth,
    ),
  ).toBeTruthy();
});

test("companion editor selects names, publishes, and reloads authoritative records", async ({
  page,
}) => {
  const { readFile } = await import("node:fs/promises");
  const html = await readFile(
    new URL("../../baseball_processor/companion_manager.html", import.meta.url),
    "utf8",
  );
  let records = {
    revision: "first",
    names: ["Dad", "Mom"],
    games: [
      {
        gameId: "CLE201605280",
        date: "05/28/2016",
        awayTeam: "BAL",
        homeTeam: "CLE",
        venue: "Progressive Field",
        companions: ["Dad"],
      },
      {
        gameId: "NYN202609140",
        date: "09/14/2026",
        awayTeam: "BAL",
        homeTeam: "NYM",
        venue: "Citi Field",
        companions: [],
      },
    ],
  };
  let submitted;
  await page.route("**/companions?token=fixture", (r) =>
    r.fulfill({ contentType: "text/html", body: html }),
  );
  await page.route("**/api/companions", async (r) => {
    expect(r.request().headers()["x-add-game-token"]).toBe("fixture");
    if (r.request().method() === "POST") {
      submitted = r.request().postDataJSON();
      records = {
        ...records,
        revision: "second",
        games: records.games.map((g) =>
          g.gameId === submitted.gameId
            ? { ...g, companions: submitted.companions }
            : g,
        ),
      };
      await r.fulfill({
        status: 202,
        json: { id: "companion-job", state: "queued" },
      });
    } else await r.fulfill({ json: records });
  });
  await page.route("**/api/jobs/companion-job", (r) =>
    r.fulfill({
      json: {
        state: "complete",
        saved: true,
        processed: true,
        deployed: true,
        message: "Companions saved and published. Ballpark goals are updated.",
      },
    }),
  );
  await page.setViewportSize({ width: 390, height: 844 });
  await page.goto("/companions?token=fixture");
  await page
    .getByRole("combobox", { name: "Attended game", exact: true })
    .selectOption("NYN202609140");
  await page.getByRole("checkbox", { name: "Dad", exact: true }).check();
  await page
    .getByRole("textbox", { name: "New companion name" })
    .fill("Friend <b>");
  await page.getByRole("button", { name: "Add name", exact: true }).click();
  await expect(
    page.getByRole("checkbox", { name: "Friend <b>", exact: true }),
  ).toBeChecked();
  await page
    .getByRole("button", { name: "Save and publish", exact: true })
    .click();
  await expect(page.getByRole("status")).toHaveText(
    "Companions saved and published. Ballpark goals are updated.",
  );
  expect(submitted).toEqual({
    gameId: "NYN202609140",
    companions: ["Dad", "Friend <b>"],
    revision: "first",
  });
  await page.reload();
  await expect(
    page.getByRole("checkbox", { name: "Dad", exact: true }),
  ).toBeChecked();
  await expect(
    page.getByRole("checkbox", { name: "Friend <b>", exact: true }),
  ).toBeChecked();
  expect(
    await page.evaluate(
      () => document.documentElement.scrollWidth <= innerWidth,
    ),
  ).toBeTruthy();
});

test("companion editor keeps draft choices when another edit conflicts", async ({
  page,
}) => {
  const { readFile } = await import("node:fs/promises");
  const html = await readFile(
    new URL("../../baseball_processor/companion_manager.html", import.meta.url),
    "utf8",
  );
  await page.route("**/companions?token=fixture", (r) =>
    r.fulfill({ contentType: "text/html", body: html }),
  );
  await page.route("**/api/companions", (r) =>
    r.fulfill(
      r.request().method() === "POST"
        ? {
            status: 409,
            json: {
              error:
                "Companions changed in another edit. Reload the game list before saving.",
            },
          }
        : {
            json: {
              revision: "first",
              names: ["Dad"],
              games: [
                {
                  gameId: "ONE",
                  date: "09/14/2026",
                  homeTeam: "NYM",
                  awayTeam: "BAL",
                  venue: "Citi Field",
                  companions: [],
                },
              ],
            },
          },
    ),
  );
  await page.goto("/companions?token=fixture");
  await page.getByRole("checkbox", { name: "Dad", exact: true }).check();
  await page
    .getByRole("button", { name: "Save and publish", exact: true })
    .click();
  await expect(page.getByRole("status")).toContainText("another edit");
  await expect(
    page.getByRole("checkbox", { name: "Dad", exact: true }),
  ).toBeChecked();
  await expect(
    page.getByRole("button", { name: "Save and publish", exact: true }),
  ).toBeEnabled();
});

test("companion editor reuses a connected browser session in a fresh tab", async ({
  page,
  context,
}) => {
  const { readFile } = await import("node:fs/promises");
  const html = await readFile(
    new URL("../../baseball_processor/companion_manager.html", import.meta.url),
    "utf8",
  );
  await context.route("**/companions", (r) =>
    r.fulfill({ contentType: "text/html", body: html }),
  );
  await context.route("**/api/companions", async (r) => {
    const headers = await r.request().allHeaders();
    const authorized =
      headers["x-add-game-token"] === "fixture" ||
      headers.cookie?.includes("passport_manager=fixture");
    await r.fulfill(
      authorized
        ? {
            headers: {
              "Set-Cookie":
                "passport_manager=fixture; HttpOnly; Path=/; SameSite=Strict",
            },
            json: {
              revision: "first",
              names: ["Dad"],
              games: [
                {
                  gameId: "NYN202609140",
                  date: "09/14/2026",
                  homeTeam: "NYM",
                  awayTeam: "BAL",
                  venue: "Citi Field",
                  companions: ["Dad"],
                },
              ],
            },
          }
        : { status: 403, json: { error: "Connect to the manager." } },
    );
  });
  await page.goto("/companions");
  await page.getByLabel("Manager token", { exact: true }).fill("fixture");
  await page.getByRole("button", { name: "Connect", exact: true }).click();
  await expect(
    page.getByRole("checkbox", { name: "Dad", exact: true }),
  ).toBeChecked();
  const fresh = await context.newPage();
  await fresh.goto("/companions");
  await expect(
    fresh.getByRole("checkbox", { name: "Dad", exact: true }),
  ).toBeChecked();
  await expect(
    fresh.getByRole("heading", { name: "Connect to your local manager" }),
  ).toBeHidden();
  await fresh.close();
});

test("companion editor opened as a file shows the manager link without API requests", async ({
  page,
}) => {
  const requests = [];
  page.on("request", (request) => {
    if (request.url().includes("/api/")) requests.push(request.url());
  });
  await page.goto(
    new URL("../../baseball_processor/companion_manager.html", import.meta.url)
      .href,
  );
  await expect(
    page.getByRole("heading", { name: "Open the running companion editor" }),
  ).toBeVisible();
  await expect(
    page.getByRole("link", { name: "Open companion editor", exact: true }),
  ).toHaveAttribute("href", "http://localhost:5555/companions");
  await expect(
    page.getByRole("heading", { name: "Connect to your local manager" }),
  ).toBeHidden();
  expect(requests).toEqual([]);
});

async function collectionGoalsFixture(page, stale = false) {
  const metadata = {
    available: true,
    rosterFresh: true,
    rosterAsOf: stale ? "2020-01-01T00:00:00Z" : new Date().toISOString(),
  };
  const target = { playerId: "active", name: "Active Winner", mlbId: 123 };
  const sets = [
    {
      id: "mixed",
      title: "Mixed winners",
      library: "Awards",
      priority: 1,
      criteria: { awardKeys: ["mvp"] },
      total: 4,
      seen: 1,
      missing: 3,
      goalTotal: 2,
      activeMissing: 1,
      activeMissingPlayers: 1,
      activeTargets: [target],
      excludedMissing: 2,
      goalAvailable: true,
    },
    {
      id: "old",
      title: "1900 Award Class",
      library: "Seasons",
      priority: 2,
      criteria: { year: 1900 },
      total: 1,
      seen: 0,
      missing: 1,
      goalTotal: 0,
      activeMissing: 0,
      activeMissingPlayers: 0,
      activeTargets: [],
      goalAvailable: false,
    },
    {
      id: "retired",
      title: "Retired-only winners",
      library: "Seasons",
      priority: 3,
      criteria: { year: 2010 },
      total: 1,
      seen: 0,
      missing: 1,
      goalTotal: 0,
      activeMissing: 0,
      activeMissingPlayers: 0,
      activeTargets: [],
      goalAvailable: false,
    },
    {
      id: "complete",
      title: "Finished collection",
      library: "Seasons",
      priority: 4,
      criteria: { year: 2025 },
      total: 1,
      seen: 1,
      missing: 0,
      goalTotal: 1,
      activeMissing: 0,
      activeMissingPlayers: 0,
      activeTargets: [],
      goalAvailable: false,
      isComplete: true,
    },
  ];
  const groups = [
    {
      awardKey: "mvp",
      award: "MVP",
      items: [
        {
          id: "seen",
          playerId: "jose",
          name: "Seen Winner",
          year: 2025,
          checked: true,
          goalEligible: true,
        },
        {
          id: "old",
          playerId: "old",
          name: "Old Winner",
          year: 1900,
          checked: false,
          goalEligible: false,
        },
        {
          id: "retired",
          playerId: "retired",
          name: "Retired Winner",
          year: 2010,
          checked: false,
          goalEligible: false,
        },
        {
          id: "active",
          playerId: "active",
          name: "Active Winner",
          year: 2026,
          checked: false,
          goalEligible: true,
        },
      ],
    },
  ];
  await page.route("**/data-index-*.json", async (r) => {
    const data = await (await r.fetch()).json();
    await r.fulfill({
      json: { ...data, __collectionSets: sets, __collectionMeta: metadata },
    });
  });
  await page.route("**/data-awardChecklists-*.json", (r) =>
    r.fulfill({
      json: { metadata, groups, completionSets: sets, seenPlayers: {} },
    }),
  );
}

test("collections and planner suggest active targets and keep retired-only sets in history", async ({
  page,
}) => {
  await collectionGoalsFixture(page);
  await page.addInitScript(() =>
    localStorage.setItem(
      "passport:goals",
      JSON.stringify([
        { id: "old", name: "1900 Award Class", kind: "collection" },
        { id: "retired", name: "Retired-only winners", kind: "collection" },
      ]),
    ),
  );
  await page.goto("/#dashboard/collections");
  const mixed = page.getByRole("article", { name: "Mixed winners" });
  await expect(mixed).toContainText("1 / 2 eligible entries");
  await expect(mixed).toContainText("1 unseen active player");
  await expect(
    page.getByRole("article", { name: "1900 Award Class" }),
  ).toHaveCount(0);
  await expect(
    page.getByRole("article", { name: "Retired-only winners" }),
  ).toHaveCount(0);
  await mixed.getByRole("button", { name: "Pin goal", exact: true }).click();
  await page.getByRole("button", { name: "All history", exact: true }).click();
  await expect(
    page.getByRole("article", { name: "1900 Award Class" }),
  ).toBeVisible();
  await expect(
    page
      .getByRole("article", { name: "Retired-only winners" })
      .getByRole("button", { name: "Pin goal", exact: true }),
  ).toHaveCount(0);
  await expect(mixed).toContainText("1 / 4 entries");
  await page.getByRole("button", { name: "Completed", exact: true }).click();
  await expect(
    page.getByRole("article", { name: "Finished collection" }),
  ).toBeVisible();
  await expect(mixed).toHaveCount(0);
  await page.goto("/#dashboard/plan");
  await page.getByText("Other goals and watchlist", { exact: true }).click();
  await expect(
    page.getByRole("button", { name: "Pin Active Winner", exact: true }),
  ).toBeVisible();
  await expect(
    page.getByRole("button", { name: "Pin Retired Winner", exact: true }),
  ).toHaveCount(0);
  await page.goto("/#dashboard");
  await expect(
    page.getByRole("heading", { name: "Collections you can advance" }),
  ).toBeVisible();
  await expect(
    page.getByRole("button", { name: /Mixed winners/ }),
  ).toBeVisible();
  await expect(
    page.getByRole("button", { name: /Retired-only winners/ }),
  ).toHaveCount(0);
});

test("award detail checklists use the same attainable scope", async ({
  page,
}) => {
  await collectionGoalsFixture(page);
  await page.goto("/#players/awards");
  await expect(
    page.getByRole("heading", { name: "Collections you can still advance" }),
  ).toBeVisible();
  await expect(page.getByText("1900 Award Class", { exact: true })).toHaveCount(
    0,
  );
  await expect(page.getByText("Retired Winner", { exact: true })).toHaveCount(
    0,
  );
  await page
    .getByRole("button", { name: "Open checklist", exact: true })
    .first()
    .click();
  await expect(
    page.getByText("Active Winner", { exact: true }).first(),
  ).toBeVisible();
  await expect(page.getByText("Old Winner", { exact: true })).toHaveCount(0);
  await expect(page.getByText("Retired Winner", { exact: true })).toHaveCount(
    0,
  );
});

test("stale roster snapshots do not offer collection goals", async ({
  page,
}) => {
  await collectionGoalsFixture(page, true);
  await page.goto("/#dashboard/collections");
  await expect(
    page.getByText(/A fresh MLB roster check is needed/),
  ).toBeVisible();
  await expect(
    page.getByRole("article", { name: "Mixed winners" }),
  ).toHaveCount(0);
  await page.getByRole("button", { name: "All history", exact: true }).click();
  await expect(
    page.getByRole("article", { name: "Mixed winners" }),
  ).toBeVisible();
  await expect(
    page.getByRole("button", { name: "Pin goal", exact: true }),
  ).toHaveCount(0);
});
