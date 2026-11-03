import { expect, test } from "@playwright/test";

// As in scan-manual.spec.ts, a signed-in Supabase session can't be faked here,
// so the e2e covers the signed-out gate around the label flow (upload, confirm,
// manual entry, saved-product result). The flow itself (upload → confirm →
// save → result, every warning case) is covered by the Vitest component tests
// in tests/features/scan over the real generated client and a stubbed fetch.

const SCAN_ID = "0b6c1f8e-3c1a-4f0e-9a51-1d2e3f4a5b6c";
const PRODUCT_ID = "7d1d2f8a-1111-4c3b-9a0e-0123456789ab";

for (const path of [
  "/en/scan/label",
  `/en/scan/confirm/${SCAN_ID}`,
  "/en/scan/manual",
  `/en/product/${PRODUCT_ID}`,
]) {
  test(`signed-out ${path} lands on sign-in with next, rendering nothing`, async ({
    page,
  }) => {
    await page.goto(`${path}?barcode=8901063201089`);
    const next = encodeURIComponent(path).replace(
      /[.*+?^${}()|[\]\\]/g,
      "\\$&",
    );
    await expect(page).toHaveURL(new RegExp(`/en/sign-in\\?next=${next}$`));
    await expect(page.getByRole("heading", { name: "Sign in" })).toBeVisible();
    await expect(
      page.getByRole("button", { name: "Confirm and save" }),
    ).toHaveCount(0);
    await expect(page.getByTestId("verdict-card")).toHaveCount(0);
  });
}

test("hi label URL keeps the locale through sign-in", async ({ page }) => {
  await page.goto("/hi/scan/label?barcode=8901063201089");
  await expect(page).toHaveURL(/\/hi\/sign-in\?next=%2Fhi%2Fscan%2Flabel$/);
});
