import { expect, test } from "@playwright/test";

// The flake was a page.goto timeout waiting for the full load event (and
// networkidle) under load. Not reproduced in 60/60 runs (slowest ~2 s), so
// navigation waits for domcontentloaded with a 30 s cap, then for "load".
test.describe.configure({ timeout: 90_000 });

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
  const res = await page.goto("/en/p/8901063201089", {
    waitUntil: "domcontentloaded",
    timeout: 30_000,
  });
  expect(res?.status()).toBe(200);
  expect(page.url()).toContain("/en/p/8901063201089");
  await expect(page.getByRole("heading", { name: "Parle-G" })).toBeVisible();
  await expect(page.getByText(/calculated by SmartNutri/i)).toBeVisible();
  await page.waitForLoadState("load", { timeout: 30_000 });
  expect(violations).toEqual([]);
  // Messages are scoped for client components, so the anonymous HTML carries
  // no verdict catalogue at all.
  const raw = (
    await (await page.request.get("/en/p/8901063201089")).text()
  ).toLowerCase();
  expect(raw).not.toContain("verdict");
});

test("unknown barcode is a 404", async ({ page }) => {
  const res = await page.goto("/en/p/8901063209999", {
    waitUntil: "domcontentloaded",
    timeout: 30_000,
  });
  expect(res?.status()).toBe(404);
});
