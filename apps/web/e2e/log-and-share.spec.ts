import { readFileSync } from "node:fs";
import { join } from "node:path";
import { expect, test } from "@playwright/test";
import { addMember, signedIn } from "./session";

// Scan-to-log and history against the stub API (e2e/stub-api.mjs): log the
// sugar-free biscuit for Dad from his result card, then find it in History
// with today's sugar total against the daily limit. The stub serves canned
// snapshots (per_100g x grams / 100) and never decides a band.

const FIXTURES = join(process.cwd(), "../../packages/test-fixtures");
const SF_BISCUIT = (
  JSON.parse(readFileSync(join(FIXTURES, "responses/index.json"), "utf8")) as {
    products: Record<string, string>;
  }
).products.sf_biscuit as string;

test.beforeEach(async ({ context, request }) => {
  await signedIn(context, request);
});

test("log the biscuit for Dad, then History shows today's sugar", async ({
  page,
  request,
}) => {
  const violations: string[] = [];
  page.on("console", (m) => {
    if (/content security policy/i.test(m.text())) violations.push(m.text());
  });
  await addMember(request, {
    name: "Dad",
    relation: "parent",
    birth_year: 1960,
  });

  await page.goto(`/en/product/${SF_BISCUIT}`);
  const dad = page
    .getByTestId("member-result")
    .filter({ has: page.getByRole("heading", { name: /for Dad$/ }) });
  await expect(dad).toBeVisible();
  await dad.getByRole("button", { name: "I ate this" }).click();

  const dialog = page.getByRole("dialog", { name: "Log what was eaten" });
  await expect(dialog).toBeVisible();
  await expect(
    dialog.getByText(
      "On the web, logging needs an internet connection. Items are not saved offline.",
    ),
  ).toBeVisible();
  await expect(dialog.getByLabel("Who ate it?")).toHaveValue(
    /^b0000000-0000-4000-8000-/,
  );
  // One serving (25 g on this label) is the default.
  await expect(dialog.getByText("1 serving = 25 g")).toBeVisible();
  await dialog.getByRole("button", { name: "Save" }).click();
  await expect(dialog.getByText("Logged for Dad")).toBeVisible();
  await expect(dialog.getByText("25 g")).toBeVisible();
  await dialog.getByRole("button", { name: "Close" }).click();
  await expect(dialog).toBeHidden();

  await page.goto("/en/history");
  await expect(
    page.getByRole("heading", { level: 1, name: "History" }),
  ).toBeVisible();
  await page.getByLabel("Family member").selectOption({ label: "Dad" });
  await expect(page.getByTestId("day-title")).toHaveText("Today");
  // 25 g at 2 g sugars per 100 g = 0.5 g, against Dad's 25 g daily limit.
  await expect(
    page.getByTestId("day-sugars_g").getByTestId("day-value"),
  ).toHaveText("0.5 g of 25 g");
  // The stub sends no band: it reads "Not enough data" (grey), never green.
  await expect(
    page.getByTestId("day-sugars_g").getByTestId("band-badge"),
  ).toHaveAttribute("data-band", "unknown");
  const row = page.getByTestId("meal-row");
  await expect(row).toHaveCount(1);
  await expect(row).toContainText("Sugar Free Biscuit");
  await expect(row).toContainText("25 g");
  await expect(page.getByTestId("weekly-dashboard")).toBeVisible();
  await expect(
    page.getByTestId("nutrient-sugars_g").getByTestId("day-bar"),
  ).toHaveCount(7);
  await expect(page.getByText("Information, not medical advice.")).toHaveCount(
    1,
  );

  // Remove it again (asks first).
  await row.getByRole("button", { name: "Remove" }).click();
  await page
    .getByTestId("confirm-dialog")
    .getByRole("button", { name: "Remove" })
    .click();
  await expect(page.getByTestId("meal-row")).toHaveCount(0);
  await expect(page.getByTestId("day-list-empty")).toBeVisible();
  expect(violations).toEqual([]);
});

test("History: earlier days, and the holder's own empty day", async ({
  page,
}) => {
  await page.goto("/en/history");
  await expect(page.getByTestId("day-title")).toHaveText("Today");
  await expect(page.getByTestId("day-totals-empty")).toHaveText(
    "Nothing logged on this day.",
  );
  await expect(page.getByRole("button", { name: "Next day" })).toBeDisabled();
  await page.getByRole("button", { name: "Previous day" }).click();
  await expect(page.getByTestId("day-title")).not.toHaveText("Today");
  await expect(page.getByRole("button", { name: "Next day" })).toBeEnabled();
});
