import { expect, test } from "@playwright/test";

// A signed-in Supabase session can't be faked here without stubbing auth, so
// the e2e covers the signed-out gate around the scan → result flow. The
// verdict rendering (every shared fixture, en/hi/mr) is covered by the Vitest
// component tests in tests/features/analysis.

test("signed-out /en/scan (manual barcode form) lands on sign-in with next", async ({
  page,
}) => {
  await page.goto("/en/scan");
  await expect(page).toHaveURL(/\/en\/sign-in\?next=%2Fen%2Fscan$/);
  await expect(page.getByRole("heading", { name: "Sign in" })).toBeVisible();
});

test("signed-out result URL for a barcode lands on sign-in carrying the result path", async ({
  page,
}) => {
  const res = await page.goto("/en/result/8901063201089");
  await expect(page).toHaveURL(
    /\/en\/sign-in\?next=%2Fen%2Fresult%2F8901063201089$/,
  );
  expect(res?.status()).toBe(200);
  // Nothing from the result page was rendered.
  await expect(page.getByTestId("verdict-card")).toHaveCount(0);
});

test("hi result URL keeps the locale through sign-in", async ({ page }) => {
  await page.goto("/hi/result/8901063201089");
  await expect(page).toHaveURL(
    /\/hi\/sign-in\?next=%2Fhi%2Fresult%2F8901063201089$/,
  );
});

test("public product CTA sends a signed-out user to sign-in for the result", async ({
  page,
}) => {
  await page.goto("/en/p/8901063201089");
  await page.getByRole("link", { name: "Check it for your family" }).click();
  await expect(page).toHaveURL(
    /\/en\/sign-in\?next=\/en\/result\/8901063201089$/,
  );
});
