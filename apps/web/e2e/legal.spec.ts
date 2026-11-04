import { expect, test } from "@playwright/test";

// Plan 8 Task 1: privacy and terms pages are public in en/hi/mr.

for (const locale of ["en", "hi", "mr"]) {
  for (const [path, heading] of [
    ["privacy", /Privacy Notice/],
    ["terms", /Terms of Use/],
  ] as const) {
    test(`/${locale}/${path} is public with hreflang links`, async ({
      page,
    }) => {
      const violations: string[] = [];
      page.on("console", (m) => {
        if (/content security policy/i.test(m.text()))
          violations.push(m.text());
      });
      const res = await page.goto(`/${locale}/${path}`);
      expect(res?.status()).toBe(200);
      await expect(page).toHaveURL(new RegExp(`/${locale}/${path}$`));
      await expect(
        page.getByRole("heading", { level: 1, name: heading }),
      ).toBeVisible();
      for (const l of ["en", "hi", "mr"])
        await expect(
          page.locator(`link[rel="alternate"][hreflang="${l}"]`),
        ).toHaveAttribute("href", new RegExp(`/${l}/${path}$`));
      expect(violations).toEqual([]);
    });
  }
}

test("the landing footer links to how we score, privacy and terms", async ({
  page,
}) => {
  await page.goto("/en");
  const footer = page.getByRole("contentinfo");
  for (const [name, href] of [
    ["How we score", "/en/how-we-score"],
    ["Privacy notice", "/en/privacy"],
    ["Terms of use", "/en/terms"],
  ])
    await expect(footer.getByRole("link", { name })).toHaveAttribute(
      "href",
      href,
    );
});
