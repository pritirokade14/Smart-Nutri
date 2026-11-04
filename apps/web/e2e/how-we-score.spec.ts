import { readFileSync } from "node:fs";
import { join } from "node:path";
import { expect, test } from "@playwright/test";

// Plan 7 Task 11: how-we-score is reachable without login in en, hi and mr,
// has hreflang links, and contains no member data.

const title = (locale: string) =>
  (
    JSON.parse(
      readFileSync(
        join(process.cwd(), `../../packages/i18n/messages/${locale}.json`),
        "utf8",
      ),
    ) as { methodology: { title: string } }
  ).methodology.title;

for (const locale of ["en", "hi", "mr"] as const) {
  test(`/${locale}/how-we-score is public, with hreflang links and no member data`, async ({
    page,
  }) => {
    const violations: string[] = [];
    page.on("console", (m) => {
      if (/content security policy/i.test(m.text())) violations.push(m.text());
    });
    const res = await page.goto(`/${locale}/how-we-score`);
    expect(res?.status()).toBe(200);
    await expect(page).toHaveURL(new RegExp(`/${locale}/how-we-score$`));
    await expect(
      page.getByRole("heading", { level: 1, name: title(locale) }),
    ).toBeVisible();
    for (const l of ["en", "hi", "mr"])
      await expect(
        page.locator(`link[rel="alternate"][hreflang="${l}"]`),
      ).toHaveAttribute("href", new RegExp(`/${l}/how-we-score$`));
    // Rendered from the API: the pending-review banner and live values.
    await expect(page.getByTestId("pending-review")).toBeVisible();
    await expect(page.getByTestId("methodology-high_in")).toContainText("22.5");
    // Generic rules only: no session, no member, no verdict.
    await expect(page.getByTestId("verdict-card")).toHaveCount(0);
    const text = (await page.locator("body").textContent()) ?? "";
    expect(text).not.toContain("e2e@example.test");
    expect(violations).toEqual([]);
  });
}

test("Nutri-Score is labelled calculated by SmartNutri", async ({ page }) => {
  await page.goto("/en/how-we-score");
  await expect(
    page.getByTestId("methodology-nutriscore_2023").getByRole("heading"),
  ).toContainText("calculated by SmartNutri");
});

for (const locale of ["en", "hi", "mr"] as const) {
  test(`/${locale}/how-we-score does not scroll sideways at 390 px`, async ({
    page,
  }) => {
    await page.setViewportSize({ width: 390, height: 844 });
    await page.goto(`/${locale}/how-we-score`);
    await expect(page.getByTestId("pending-review")).toBeVisible();
    const overflow = await page.evaluate(
      () => document.documentElement.scrollWidth - window.innerWidth,
    );
    expect(overflow).toBeLessThanOrEqual(0);
  });
}
