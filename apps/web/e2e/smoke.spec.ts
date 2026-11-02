import { expect, test } from "@playwright/test";

test("en landing renders", async ({ page }) => {
  await page.goto("/en");
  await expect(
    page.getByRole("heading", { name: "SmartNutri AI" }),
  ).toBeVisible();
});

test("hi sets html lang", async ({ page }) => {
  await page.goto("/hi");
  await expect(page.locator("html")).toHaveAttribute("lang", "hi");
});
