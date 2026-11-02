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
  // Messages are scoped for client components, so the anonymous HTML carries
  // no verdict catalogue at all.
  const raw = (
    await (await page.request.get("/en/p/8901063201089")).text()
  ).toLowerCase();
  expect(raw).not.toContain("verdict");
});

test("unknown barcode is a 404", async ({ page }) => {
  const res = await page.goto("/en/p/8901063209999");
  expect(res?.status()).toBe(404);
});
