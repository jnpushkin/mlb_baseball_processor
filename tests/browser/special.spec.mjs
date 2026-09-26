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

test("record filters, ties, rankings, history, and game return retain context", async ({
  page,
}) => {
  await page.goto("/#special/records");
  await page
    .getByRole("group", { name: "Record category" })
    .getByRole("button", { name: "Games", exact: true })
    .click();
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
  await expect(
    dialog.getByRole("button", { name: "Open game", exact: true }),
  ).toHaveCount(3);
  await expect(page).toHaveURL(/record=combined-runs/);
  await dialog.getByRole("button", { name: "Top five", exact: true }).click();
  await expect(dialog).toContainText("Top five places, including ties.");
  await dialog
    .getByRole("button", { name: "Record history", exact: true })
    .click();
  await expect(dialog).toContainText("First witnessed");
  await expect(dialog).toContainText("Tied record");
  await dialog.getByLabel("Find a related game", { exact: true }).fill("2025");
  await expect(
    dialog.getByRole("button", { name: "Open game", exact: true }),
  ).toHaveCount(1);
  await dialog.getByRole("button", { name: "Open game", exact: true }).click();
  await expect(page.getByRole("dialog", { name: /SF at BAL/ })).toContainText(
    "09/14/2025",
  );
  await page.keyboard.press("Escape");
  await expect(
    dialog.getByLabel("Find a related game", { exact: true }),
  ).toHaveValue("2025");
  await expect(
    dialog.getByRole("button", { name: "Record history", exact: true }),
  ).toHaveAttribute("aria-pressed", "true");
  await page.keyboard.press("Escape");
  await expect(record).toBeFocused();
  await expect(page.getByLabel("Search records", { exact: true })).toHaveValue(
    "combined runs",
  );
});

test("personal scopes recompute the best and survive shared record links", async ({
  page,
}) => {
  await page.goto("/#special/records");
  const hottest = page.getByRole("article", {
    name: "Hottest Game",
    exact: true,
  });
  await expect(hottest).toContainText("100");
  await page
    .getByLabel("Records for", { exact: true })
    .selectOption("orioles-dad");
  await expect(hottest).toContainText("45");
  await expect(hottest).not.toContainText("100");
  await hottest.getByRole("button").click();
  const url = page.url();
  await page.goto(url);
  const dialog = page.getByRole("dialog", {
    name: "Hottest Game",
    exact: true,
  });
  await expect(dialog).toContainText("Orioles games with Dad");
  await expect(dialog).toContainText("45");
  await expect(
    dialog.getByRole("button", { name: "Open game", exact: true }),
  ).toHaveCount(1);
  await page.keyboard.press("Escape");
  await expect(page.getByRole("dialog")).toHaveCount(0);
  await expect(page.getByLabel("Records for", { exact: true })).toHaveValue(
    "orioles-dad",
  );
  await page.getByText("More filters", { exact: false }).click();
  await page.getByLabel("Season", { exact: true }).selectOption("2025");
  await expect(
    page.getByText("No games match these filters.", { exact: true }),
  ).toBeVisible();
  await page
    .getByRole("button", { name: "Reset game filters", exact: true })
    .click();
  await expect(hottest).toContainText("100");
});

test("search preserves category and sort and features the matching record holder", async ({
  page,
}) => {
  await page.goto("/#special/records");
  const category = page.getByRole("group", { name: "Record category" });
  await category.getByRole("button", { name: "Games", exact: true }).click();
  await page.getByLabel("Record order", { exact: true }).selectOption("az");
  await page.getByLabel("Search records", { exact: true }).fill("harp helu");
  const card = page.getByRole("article", {
    name: "Most Combined Runs",
    exact: true,
  });
  await expect(card).toContainText("Alfredo Harp Helú Stadium");
  await expect(
    category.getByRole("button", { name: "Games", exact: true }),
  ).toHaveAttribute("aria-pressed", "true");
  await page.getByLabel("Search records", { exact: true }).fill("");
  await expect(
    category.getByRole("button", { name: "Games", exact: true }),
  ).toHaveAttribute("aria-pressed", "true");
  await expect(page.getByLabel("Record order", { exact: true })).toHaveValue(
    "az",
  );
  await page.getByLabel("Search records", { exact: true }).fill("nonexistent");
  await expect(
    page.getByText("No records match these filters.", { exact: true }),
  ).toBeVisible();
  await page
    .getByRole("button", { name: "Clear search and category", exact: true })
    .click();
  await expect(page.getByLabel("Record order", { exact: true })).toHaveValue(
    "az",
  );
});

test("counts and totals live in their own sections with game drilldowns", async ({
  page,
}) => {
  await page.goto("/#special/records");
  await page
    .getByRole("link", { name: "Milestone counts", exact: true })
    .click();
  await expect(
    page.getByRole("heading", { name: "Milestone counts", exact: true }),
  ).toBeVisible();
  await page
    .getByRole("button", { name: /1-Run Games.*Explore record/ })
    .click();
  const dialog = page.getByRole("dialog", { name: "1-Run Games", exact: true });
  await expect(
    dialog.getByRole("button", { name: "Open game", exact: true }),
  ).toHaveCount(3);
  await dialog
    .getByRole("button", { name: "Open game", exact: true })
    .first()
    .click();
  await expect(page.getByRole("dialog", { name: /SF at BAL/ })).toBeVisible();
  await page.keyboard.press("Escape");
  await expect(dialog).toBeVisible();
  await page.keyboard.press("Escape");
  await page.goto("/#dashboard/totals");
  await expect(
    page.getByRole("heading", {
      name: "Lifetime totals & averages",
      exact: true,
    }),
  ).toBeVisible();
  await expect(
    page.getByRole("article", {
      name: "Total Hits Across All Games",
      exact: true,
    }),
  ).toContainText("1,234");
});

test("Special links and Back retain highlights", async ({ page }) => {
  await page.goto("/#special");
  await page.getByRole("button", { name: /\d+ Record book/ }).click();
  await expect(
    page.getByRole("heading", { name: "Personal records", exact: true }),
  ).toBeVisible();
  await page.goBack();
  await expect(
    page.getByRole("heading", {
      name: "The games that stay with you",
      exact: true,
    }),
  ).toBeVisible();
});

test("phone layout is compact, has no overflow, and supports dark-mode dialogs", async ({
  page,
}) => {
  await page.setViewportSize({ width: 390, height: 844 });
  await page.addInitScript(() =>
    localStorage.setItem("baseballDarkMode", "true"),
  );
  for (const [route, heading] of [
    ["special", "The games that stay with you"],
    ["special/records", "Personal records"],
    ["special/debuts", "MLB Debuts Witnessed"],
    ["special/finals", "Final MLB Games Witnessed"],
    ["special/splash", "Signature Home Runs"],
  ]) {
    await page.goto("/#" + route);
    await expect(
      page.getByRole("heading", { name: heading, exact: true }),
    ).toBeVisible();
    expect(
      await page.evaluate(
        () => document.documentElement.scrollWidth <= innerWidth,
      ),
    ).toBe(true);
    if (route === "special/records") {
      const first = page
        .getByTestId("record-results")
        .getByRole("article")
        .first();
      const box = await first.boundingBox();
      expect(box.y).toBeLessThan(850);
      expect(box.height).toBeLessThan(200);
      await first.getByRole("button").click();
      await expect(page.getByRole("dialog")).toBeVisible();
      await page
        .getByRole("dialog")
        .getByRole("button", { name: "Top five", exact: true })
        .click();
      expect(
        await page.evaluate(
          () => document.documentElement.scrollWidth <= innerWidth,
        ),
      ).toBe(true);
      await page.keyboard.press("Escape");
    }
  }
});
