import { test, expect } from "@playwright/test";

test("retired 42 separates regular uniforms from Jackie Robinson Day tributes", async ({ page }) => {
  await page.goto("/#trivia/jerseys");
  await page.getByRole("button", { name: "All numbers", exact: true }).click();
  await page.getByRole("button", { name: "#42 2 seen", exact: true }).click();
  await expect(page.getByText("Retired across MLB in 1997.", { exact: false })).toBeVisible();
  const regular = page.getByRole("region", { name: "Regular number 42 uniforms" });
  await expect(regular).toContainText("Mariano Rivera");
  await expect(regular).toContainText("08/22/2008");
  await expect(regular).not.toContainText("José Ramírez");
  await page.getByText("Jackie Robinson Day tributes (1)", { exact: true }).click();
  await expect(page.getByText("Jackie Robinson Day tribute", { exact: true })).toBeVisible();
  await expect(page.getByText("04/15/2023", { exact: true })).toBeVisible();
});

test("a spring sighting neither hides an MLB sighting nor double-counts the player", async ({ page }) => {
  await page.goto("/#trivia/jerseys");
  await page.getByRole("button", { name: "All numbers", exact: true }).click();
  const zero = page.getByRole("button", { name: "#0 1 seen", exact: true });
  await zero.click();
  await expect(page.getByRole("heading", { name: "#0 — 1 player", exact: true })).toBeVisible();
  await expect(page.getByText("09/14/2024", { exact: true })).toBeVisible();
  await page.getByLabel("Include ST", { exact: true }).check();
  await expect(zero).toBeVisible();
  await expect(page.getByText("03/01/2023", { exact: true })).toBeVisible();
});
