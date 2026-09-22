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
  await page.getByRole("button", { name: /3 Record book/ }).click();
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
