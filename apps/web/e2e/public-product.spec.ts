import { expect, test } from "@playwright/test";

test("public product page renders without login, no CSP violations, no verdict", async ({
  page,
}) => {
  const violations: string[] = [];
  page.on("console", (m) => {
    if (/content security policy/i.test(m.text())) violations.push(m.text());
  });
  await page.addInitScript(() => {
    document.addEventListener("securitypolicyviolation", (e) => {
      console.error(`Content Security Policy violation ${e.violatedDirective}`);
    });
  });
  const res = await page.goto("/en/p/8901063201089");
  expect(res?.status()).toBe(200);
  expect(page.url()).toContain("/en/p/8901063201089");
  await expect(page.getByRole("heading", { name: "Parle-G" })).toBeVisible();
  await expect(page.getByText(/calculated by SmartNutri/i)).toBeVisible();
  await page.waitForLoadState("networkidle");
  expect(violations).toEqual([]);
  // The root layout serializes the whole message catalogue (which has verdict.*
  // keys) for client components, so assert on the rendered page content and on
  // verdict UI markers instead of the raw HTML string.
  const main = (await page.locator("main").innerHTML()).toLowerCase();
  expect(main).not.toContain("verdict");
  const raw = (
    await (await page.request.get("/en/p/8901063201089")).text()
  ).toLowerCase();
  expect(raw).not.toContain("verdict-card");
  expect(raw).not.toContain("data-testid");
});

test("unknown barcode is a 404", async ({ page }) => {
  const res = await page.goto("/en/p/8901063209999");
  expect(res?.status()).toBe(404);
});
