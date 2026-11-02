import { expect, test } from "@playwright/test";

test("signed-out /en/home lands on sign-in", async ({ page }) => {
  await page.goto("/en/home");
  await expect(page).toHaveURL(/\/en\/sign-in\?next=%2Fen%2Fhome/);
  await expect(page.getByRole("heading", { name: "Sign in" })).toBeVisible();
});

test("security headers are set", async ({ request }) => {
  const res = await request.get("/en", { maxRedirects: 0 });
  expect(res.headers()["x-frame-options"]).toBe("DENY");
  expect(res.headers()["content-security-policy"]).toMatch(
    /script-src 'self' 'nonce-[^']+' 'strict-dynamic'/,
  );
});

test("page hydrates under the CSP", async ({ page }) => {
  const violations: string[] = [];
  page.on("console", (m) => {
    if (m.text().includes("Content Security Policy")) violations.push(m.text());
  });
  await page.goto("/en/sign-in");
  await page.getByRole("button", { name: "Continue with email" }).click();
  await expect(page.getByLabel("Email address")).toBeVisible();
  expect(violations).toEqual([]);
});
