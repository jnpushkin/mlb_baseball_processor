import { test, expect } from "@playwright/test";

test("Special highlights connect moments to games without loading full player libraries", async ({
  page,
}) => {
  const libraries = [];
  page.on("request", (r) => libraries.push(r.url()));
  await page.goto("/#special");
  await expect(
    page.getByRole("heading", { name: "The games that stay with you" }),
  ).toBeVisible();
  await expect(
    page.getByRole("region", { name: "Latest special visit" }),
  ).toContainText("Test Pitcher");
  expect(
    libraries.some(
      (url) =>
        url.includes("data-playerGames-") ||
        url.includes("data-pitcherGames-") ||
        url.includes("data-awardChecklists-"),
    ),
  ).toBe(false);
  await page.getByLabel("Find a moment", { exact: true }).fill("Jose");
  await page.getByLabel("Moment type", { exact: true }).selectOption("homer");
  const moment = page.getByRole("article", {
    name: "Landmark home run: José Ramírez",
  });
  await expect(moment).toBeVisible();
  await expect(
    page.getByRole("article", { name: "MLB debut: José Ramírez" }),
  ).toHaveCount(0);
  await moment.getByRole("button", { name: "Open game" }).click();
  await expect(page.getByRole("dialog", { name: /SF at BAL/ })).toContainText(
    "09/14/2026",
  );
  await page.keyboard.press("Escape");
  await expect(page.getByLabel("Find a moment", { exact: true })).toHaveValue(
    "Jose",
  );
  await page
    .getByLabel("Find a moment", { exact: true })
    .fill("No such player");
  await expect(page.getByText("No moments match these filters.")).toBeVisible();
  await page.getByRole("button", { name: "Clear moment filters" }).click();
  await expect(
    page.getByRole("article", { name: "MLB debut: José Ramírez" }),
  ).toBeVisible();
});

test("record filters and keyboard dialogs reveal every tied game", async ({
  page,
}) => {
  await page.goto("/#special/records");
  await page
    .getByLabel("Record category", { exact: true })
    .selectOption("extremes");
  await page
    .getByLabel("Search records", { exact: true })
    .fill("combined runs");
  const record = page.getByRole("button", {
    name: /Most Combined Runs.*Explore record/,
  });
  await record.focus();
  await page.keyboard.press("Enter");
  const dialog = page.getByRole("dialog", {
    name: "Most Combined Runs",
    exact: true,
  });
  await expect(dialog).toBeVisible();
  await expect(dialog.getByRole("button", { name: "Open game" })).toHaveCount(
    2,
  );
  await expect(dialog).toContainText("09/14/2026");
  await expect(dialog).toContainText("09/14/2025");
  await page.keyboard.press("Escape");
  await expect(record).toBeFocused();
  await record.click();
  await dialog.getByRole("button", { name: "Open game" }).last().click();
  await expect(page.getByRole("dialog", { name: /SF at BAL/ })).toContainText(
    "09/14/2025",
  );
  await page.keyboard.press("Escape");
  await page
    .getByLabel("Search records", { exact: true })
    .fill("No such record");
  await expect(page.getByText("No records match these filters.")).toBeVisible();
  await page.getByRole("button", { name: "Clear filters" }).click();
  await expect(
    page.getByRole("button", { name: /Coldest Game.*Explore record/ }),
  ).toBeVisible();
});

test("Special links and Back retain the highlights landing page", async ({
  page,
}) => {
  await page.goto("/#special");
  await page.getByRole("button", { name: /6 Record book/ }).click();
  await expect(page).toHaveURL(/#special\/records$/);
  await expect(
    page.getByRole("heading", { name: "Personal Record Book" }),
  ).toBeVisible();
  await page.goBack();
  await expect(page).toHaveURL(/#special$/);
  await expect(
    page.getByRole("heading", { name: "The games that stay with you" }),
  ).toBeVisible();
});

test("Special views work on a phone in dark mode with direct recap links", async ({
  page,
}) => {
  await page.setViewportSize({ width: 390, height: 844 });
  await page.addInitScript(() =>
    localStorage.setItem("baseballDarkMode", "true"),
  );
  for (const [route, heading] of [
    ["special", "The games that stay with you"],
    ["special/records", "Personal Record Book"],
    ["special/debuts", "MLB Debuts Witnessed"],
    ["special/finals", "Final MLB Games Witnessed"],
    ["special/splash", "Signature Home Runs"],
  ]) {
    await page.goto(`/#${route}`);
    await expect(
      page.getByRole("heading", { name: heading, exact: true }),
    ).toBeVisible();
    expect(
      await page.evaluate(
        () => document.documentElement.scrollWidth <= window.innerWidth,
      ),
    ).toBe(true);
    if (
      ["special/debuts", "special/finals", "special/splash"].includes(route)
    ) {
      await page.getByRole("button", { name: "Open game" }).first().click();
      await expect(
        page.getByRole("dialog", { name: /SF at BAL/ }),
      ).toBeVisible();
      await page.keyboard.press("Escape");
    }
  }
});

test("record views distinguish totals and support ballpark search across entry types", async ({
  page,
}) => {
  await page.goto("/#special/records");
  const results = page.getByTestId("record-results");
  await expect(results.getByRole("article")).toHaveCount(3);
  await expect(
    page.getByRole("region", {
      name: "Latest game in the record book",
      exact: true,
    }),
  ).toContainText("09/14/2026");
  await page
    .getByRole("button", { name: "Totals & averages 2", exact: true })
    .click();
  await expect(results.getByRole("article")).toHaveCount(2);
  const total = results.getByRole("article", {
    name: "Total Hits Across All Games",
    exact: true,
  });
  await expect(total).toContainText("1,234");
  await expect(total).toContainText("hits");
  await expect(total.getByRole("button")).toHaveCount(0);
  await expect(
    results.getByRole("article", { name: "Average Attendance", exact: true }),
  ).toContainText("Based on 3 games");
  await page.getByLabel("Search records", { exact: true }).fill("harp helu");
  await expect(
    page.getByRole("button", { name: "Everything 6", exact: true }),
  ).toHaveAttribute("aria-pressed", "true");
  await expect(results.getByRole("article")).toHaveCount(2);
  await expect(
    results.getByRole("article", { name: "Coldest Game", exact: true }),
  ).toBeVisible();
  await page
    .getByRole("button", { name: "Clear filters", exact: true })
    .click();
  await expect(results.getByRole("article")).toHaveCount(3);
});

test("record chronology and related-game search retain the selected view", async ({
  page,
}) => {
  await page.goto("/#special/records");
  const results = page.getByTestId("record-results");
  await page.getByLabel("Record order", { exact: true }).selectOption("oldest");
  await expect(results.getByRole("article").first()).toHaveAttribute(
    "aria-label",
    "Coldest Game",
  );
  await page.getByLabel("Record order", { exact: true }).selectOption("recent");
  await expect(results.getByRole("article").last()).toHaveAttribute(
    "aria-label",
    "Coldest Game",
  );
  await page
    .getByRole("button", { name: "Milestone counts 1", exact: true })
    .click();
  await results
    .getByRole("button", { name: /1-Run Games.*Explore record/ })
    .click();
  const dialog = page.getByRole("dialog", { name: "1-Run Games", exact: true });
  await expect(
    dialog.getByRole("button", { name: "Open game", exact: true }),
  ).toHaveCount(3);
  await dialog.getByLabel("Find a related game", { exact: true }).fill("2025");
  await expect(
    dialog.getByRole("button", { name: "Open game", exact: true }),
  ).toHaveCount(1);
  await expect(dialog).toContainText("09/14/2025");
  await dialog
    .getByLabel("Find a related game", { exact: true })
    .fill("missing team");
  await expect(
    dialog.getByText("No related games match this search."),
  ).toBeVisible();
  await dialog.getByLabel("Find a related game", { exact: true }).fill("2025");
  await dialog.getByRole("button", { name: "Open game", exact: true }).click();
  await expect(page.getByRole("dialog", { name: /SF at BAL/ })).toContainText(
    "09/14/2025",
  );
  await page.keyboard.press("Escape");
  await expect(
    page.getByRole("button", { name: "Milestone counts 1", exact: true }),
  ).toHaveAttribute("aria-pressed", "true");
  await expect(page.getByLabel("Record order", { exact: true })).toHaveValue(
    "recent",
  );
});
