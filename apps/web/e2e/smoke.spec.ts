import { expect, test } from "@playwright/test";

test("en landing renders the hero and the brand", async ({ page }) => {
  await page.goto("/en");
  await expect(
    page.getByRole("heading", {
      level: 1,
      name: "Know if a packaged food is right for each member of your family",
    }),
  ).toBeVisible();
  await expect(
    page.getByRole("link", { name: "SmartNutri AI" }).first(),
  ).toBeVisible();
  await expect(page.getByRole("link", { name: "Get started" })).toHaveAttribute(
    "href",
    "/en/sign-in",
  );
});

test("hi sets html lang", async ({ page }) => {
  await page.goto("/hi");
  await expect(page.locator("html")).toHaveAttribute("lang", "hi");
});

test("language switcher keeps the page", async ({ page }) => {
  await page.goto("/en/sign-in");
  await page
    .getByRole("navigation", { name: "Language" })
    .getByRole("link", { name: "मराठी" })
    .click();
  await expect(page).toHaveURL(/\/mr\/sign-in$/);
  await expect(page.locator("html")).toHaveAttribute("lang", "mr");
});

test("fonts are self-hosted (no third-party font requests)", async ({
  page,
}) => {
  const external: string[] = [];
  page.on("request", (r) => {
    const u = new URL(r.url());
    if (r.resourceType() === "font" && u.host !== new URL(page.url()).host)
      external.push(r.url());
  });
  await page.goto("/hi");
  await page.waitForLoadState("networkidle");
  expect(external).toEqual([]);
});
