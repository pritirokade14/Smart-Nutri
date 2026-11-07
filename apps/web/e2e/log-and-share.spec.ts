import { readFileSync } from "node:fs";
import { join } from "node:path";
import { expect, test } from "@playwright/test";
import { addMember, signedIn } from "./support/session";

// Scan-to-log and the diary against the stub API (e2e/stub-api.mjs): log the
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

test("log the biscuit, then the Diary lists it and it can be removed", async ({
  page,
}) => {
  const violations: string[] = [];
  page.on("console", (m) => {
    if (/content security policy/i.test(m.text())) violations.push(m.text());
  });

  await page.goto(`/en/product/${SF_BISCUIT}`);
  const mine = page.getByTestId("member-result");
  await expect(mine).toBeVisible();
  await mine.getByRole("button", { name: "I ate this" }).click();

  const dialog = page.getByRole("dialog", { name: "Log what was eaten" });
  await expect(dialog).toBeVisible();
  await expect(
    dialog.getByText(
      "On the web, logging needs an internet connection. Items are not saved offline.",
    ),
  ).toBeVisible();
  await expect(dialog.getByLabel("Who ate it?")).toHaveValue(
    /^a0000000-0000-4000-8000-/,
  );
  // One serving (25 g on this label) is the default.
  await expect(dialog.getByText("1 serving = 25 g")).toBeVisible();
  await dialog.getByRole("button", { name: "Save" }).click();
  await expect(dialog.getByText("Logged for you")).toBeVisible();
  await expect(dialog.getByText("25 g")).toBeVisible();
  await dialog.getByRole("button", { name: "Close" }).click();
  await expect(dialog).toBeHidden();

  await page.goto("/en/diary");
  await expect(
    page.getByRole("heading", { level: 1, name: "Diary" }),
  ).toBeVisible();
  await expect(page.getByTestId("day-title")).toHaveText("Today");
  const row = page.getByTestId("entry-row");
  await expect(row).toHaveCount(1);
  await expect(row).toContainText("Sugar Free Biscuit");
  await expect(row).toContainText("25 g");
  // The stub sends no band: it reads "Not enough data" (grey), never green.
  for (const badge of await page.getByTestId("band-badge").all())
    await expect(badge).toHaveAttribute("data-band", "unknown");
  await expect(page.getByText("Information, not medical advice.")).toHaveCount(
    1,
  );

  // Remove it again (asks first).
  await row.click();
  await page
    .getByTestId("edit-entry-dialog")
    .getByRole("button", { name: "Remove" })
    .click();
  await page
    .getByTestId("confirm-dialog")
    .getByRole("button", { name: "Remove" })
    .click();
  await expect(page.getByTestId("entry-row")).toHaveCount(0);
  await expect(page.getByTestId("diary-empty")).toBeVisible();
  expect(violations).toEqual([]);
});

test("Diary: earlier days, and the holder's own empty day", async ({
  page,
}) => {
  await page.goto("/en/diary");
  await expect(page.getByTestId("day-title")).toHaveText("Today");
  await expect(page.getByTestId("diary-empty")).toHaveText(
    "Nothing logged yet.",
  );
  await expect(page.getByRole("button", { name: "Next day" })).toBeDisabled();
  await page.getByRole("button", { name: "Previous day" }).click();
  await expect(page.getByTestId("day-title")).not.toHaveText("Today");
  await expect(page.getByRole("button", { name: "Next day" })).toBeEnabled();
});

test("Share falls back to copy link and WhatsApp without the Web Share API", async ({
  page,
  request,
}) => {
  await page.addInitScript(() => {
    Object.defineProperty(navigator, "share", {
      value: undefined,
      configurable: true,
    });
  });
  await addMember(request, {
    name: "Ravi Patil",
    relation: "parent",
    birth_year: 1960,
  });
  await page.goto(`/en/product/${SF_BISCUIT}`);
  await expect(page.getByTestId("member-result")).toHaveCount(2);
  await expect(
    page.getByText("We cannot suggest options for this product yet."),
  ).toBeVisible();
  await page.getByRole("button", { name: "Share", exact: true }).click();
  const dialog = page.getByTestId("share-dialog");
  await expect(dialog).toBeVisible();
  const preview = dialog.getByTestId("share-preview");
  await expect(preview).toContainText("Sugar Free Biscuit — Nutri-Score");
  // Ruling SH1: nobody's result is shared unless the user ticks them.
  await expect(preview).not.toContainText("Ravi");
  for (const box of await dialog.getByRole("checkbox").all())
    await expect(box).not.toBeChecked();
  await expect(
    dialog.getByText(
      "Only the product and its grade are shared, plus the result of anyone you tick. Health details stay private.",
    ),
  ).toBeVisible();
  await expect(dialog.getByRole("button", { name: "Copy link" })).toBeVisible();
  const wa = dialog.getByRole("link", { name: "Share on WhatsApp" });
  await expect(wa).toHaveAttribute("href", /^https:\/\/wa\.me\/\?text=/);

  // Opt Ravi in: his first name and status only.
  await dialog.getByRole("checkbox", { name: /^Ravi: / }).check();
  await expect(preview).toContainText("Ravi: ");
  await expect(preview).not.toContainText("Patil");
  expect(decodeURIComponent((await wa.getAttribute("href")) ?? "")).toContain(
    "Ravi: ",
  );

  // And out again: his part disappears from the message and the link.
  await dialog.getByRole("checkbox", { name: /^Ravi: / }).uncheck();
  await expect(preview).not.toContainText("Ravi");
  const href = (await wa.getAttribute("href")) ?? "";
  expect(decodeURIComponent(href)).not.toContain("Ravi");
});
