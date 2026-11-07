import { readFileSync } from "node:fs";
import { join } from "node:path";
import { expect, type Page, test } from "@playwright/test";
import { STUB, signedIn, signIn } from "./support/session";

// The Diary against the stub API (e2e/stub-api.mjs). The stub assembles a day
// from the meals stored in it (sums of the known values only) or, with
// ?diary=<stem> on /__reset, serves the golden day and week as-is. It never
// decides anything: every number on screen is what the API returned.

const FIXTURES = join(process.cwd(), "../../packages/test-fixtures");
const SF_BISCUIT = (
  JSON.parse(readFileSync(join(FIXTURES, "responses/index.json"), "utf8")) as {
    products: Record<string, string>;
  }
).products.sf_biscuit as string;
const BREAKFAST = "d0000000-0000-4000-8000-000000000001";
const AUTH = { authorization: "Bearer e2e" };

const istDay = (offset = 0): string => {
  const d = new Date(Date.now() + 330 * 60_000);
  d.setUTCDate(d.getUTCDate() + offset);
  return d.toISOString().slice(0, 10);
};

/** Digits left on the page once dates, portions and day counts are removed. */
async function digits(page: Page): Promise<string> {
  return page.evaluate(() => {
    const root = (document.querySelector("main") as HTMLElement).cloneNode(
      true,
    ) as HTMLElement;
    for (const el of root.querySelectorAll("[data-allow-digits]")) el.remove();
    return (root.textContent ?? "").replace(/\D/g, "");
  });
}

test.describe("with the terms agreed", () => {
  test.beforeEach(async ({ context, request }) => {
    await signedIn(context, request);
  });

  test("log a product, edit grams, remove it", async ({ page, request }) => {
    const logged = await request.post(`${STUB}/v1/meals`, {
      headers: AUTH,
      data: { product_id: SF_BISCUIT, grams: 25 },
    });
    expect(logged.status()).toBe(201);

    await page.goto("/en/diary");
    await expect(
      page.getByRole("heading", { level: 1, name: "Diary" }),
    ).toBeVisible();
    await expect(page.getByTestId("day-title")).toHaveText("Today");
    await expect(
      page
        .getByText(
          "On the web, logging needs an internet connection. Items are not saved offline.",
        )
        .first(),
    ).toBeVisible();
    const row = page.getByTestId("entry-row");
    await expect(row).toHaveCount(1);
    await expect(row).toContainText("Sugar Free Biscuit");
    await expect(row).toContainText("25 g");

    // Edit grams: the day re-renders the stub's next response.
    await row.click();
    const dialog = page.getByTestId("edit-entry-dialog");
    const grams = dialog.getByLabel("Amount in grams");
    await grams.fill("50");
    await dialog.getByRole("button", { name: "Save" }).click();
    await expect(dialog).toBeHidden();
    await expect(page.getByTestId("entry-row")).toContainText("50 g");

    // Remove it (asks first).
    await page.getByTestId("entry-row").click();
    await page
      .getByTestId("edit-entry-dialog")
      .getByRole("button", { name: "Remove" })
      .click();
    await expect(
      page.getByText("Remove this item from your diary?"),
    ).toBeVisible();
    await page
      .getByTestId("confirm-dialog")
      .getByRole("button", { name: "Remove" })
      .click();
    await expect(page.getByTestId("entry-row")).toHaveCount(0);
    await expect(page.getByTestId("diary-empty")).toBeVisible();
  });

  test("quick add kcal only shows incomplete macros", async ({ page }) => {
    await page.goto("/en/diary");
    await page.getByRole("button", { name: "Add food", exact: true }).click();
    const panel = page.getByTestId("add-food-panel");
    await panel.getByRole("tab", { name: "Quick add" }).click();
    await panel.getByLabel("Calories").fill("450");
    await expect(
      panel.getByText(
        "Leave blank if you don't know. Blank is never counted as 0.",
      ),
    ).toBeVisible();
    await panel.getByRole("button", { name: "Save" }).click();
    await expect(panel).toBeHidden();

    const row = page.getByTestId("entry-row");
    await expect(row).toHaveCount(1);
    await expect(row).toContainText("Quick add");
    await expect(row).toContainText("Entered by you");
    await expect(row.getByTestId("entry-kcal")).toHaveText("450 kcal");
    for (const k of ["protein_g", "fat_g", "carbs_g"])
      await expect(page.getByTestId(`incomplete-${k}`)).toBeVisible();
    // Never 0 for an unknown value.
    await expect(page.getByTestId("value-protein_g")).toHaveCount(0);
  });

  test("copy yesterday's breakfast to today", async ({ page, request }) => {
    const logged = await request.post(`${STUB}/v1/meals`, {
      headers: AUTH,
      data: {
        product_id: SF_BISCUIT,
        grams: 25,
        meal_slot_id: BREAKFAST,
        local_date: istDay(-1),
      },
    });
    expect(logged.status()).toBe(201);

    await page.goto("/en/diary");
    await expect(page.getByTestId("entry-row")).toHaveCount(0);
    await page.getByRole("button", { name: "Previous day" }).click();
    await expect(page.getByTestId("entry-row")).toHaveCount(1);

    const breakfast = page
      .getByTestId("slot-section")
      .filter({ has: page.getByRole("heading", { name: "Breakfast" }) });
    await breakfast.getByRole("button", { name: "Copy this meal" }).click();
    const dialog = page.getByTestId("copy-dialog");
    await dialog.getByRole("button", { name: "Copy this meal" }).click();
    await expect(page.getByTestId("diary-notice")).toHaveText("1 item copied");

    await page.getByRole("button", { name: "Next day" }).click();
    await expect(page.getByTestId("day-title")).toHaveText("Today");
    const today = page
      .getByTestId("slot-section")
      .filter({ has: page.getByRole("heading", { name: "Breakfast" }) });
    await expect(today.getByTestId("entry-row")).toHaveCount(1);
    await expect(today.getByTestId("entry-row")).toContainText(
      "Sugar Free Biscuit",
    );
  });

  test("without health_data the diary works and shows the consent card", async ({
    page,
  }) => {
    await page.goto("/en/diary");
    const card = page.getByTestId("diary-consent");
    await expect(card).toBeVisible();
    await expect(card).toContainText(
      "To see your daily guide, allow SmartNutri to use your health details.",
    );
    await expect(page).toHaveURL(/\/en\/diary$/);
    // The diary still works.
    await page.getByRole("button", { name: "Add food", exact: true }).click();
    const panel = page.getByTestId("add-food-panel");
    await panel.getByRole("tab", { name: "Quick add" }).click();
    await panel.getByLabel("Calories").fill("200");
    await panel.getByRole("button", { name: "Save" }).click();
    await expect(page.getByTestId("entry-row")).toHaveCount(1);
    await expect(page.getByTestId("diary-consent")).toBeVisible();
  });

  test("/history redirects to /diary", async ({ page }) => {
    await page.goto("/en/history");
    await expect(page).toHaveURL(/\/en\/diary$/);
    await expect(
      page.getByRole("heading", { level: 1, name: "Diary" }),
    ).toBeVisible();
  });
});

test("golden day_quick_add_kcal_only: energy left, grey chips on the macros", async ({
  page,
  context,
  request,
}) => {
  await request.post(
    `${STUB}/__reset?terms=current&health_data=current&diary=day_quick_add_kcal_only`,
  );
  await signIn(context);
  await page.goto("/en/diary");
  await expect(page.getByTestId("value-energy_kcal")).toHaveText(
    "2,310 kcal left",
  );
  for (const k of ["protein_g", "fat_g", "carbs_g"]) {
    await expect(page.getByTestId(`incomplete-${k}`)).toHaveText(
      "Some items don't show this value, so the real total may be higher.",
    );
    await expect(page.getByTestId(`value-${k}`)).toHaveCount(0);
  }
  // The disclaimer sits where the targets show.
  await expect(page.getByTestId("diary-target-footer")).toContainText(
    "Pending clinician review",
  );
});

test("hide all numbers leaves no digits on day and week", async ({
  page,
  context,
  request,
}) => {
  await request.post(
    `${STUB}/__reset?terms=current&health_data=current&diary=day_hide_all`,
  );
  await signIn(context);
  await page.goto("/en/diary");
  await expect(page.getByTestId("slot-section")).toHaveCount(4);
  await expect(page.getByTestId("ring-fill")).toBeVisible();
  expect(await digits(page)).toBe("");

  await page.getByRole("button", { name: "This week" }).click();
  await expect(page.getByTestId("week-tile")).toHaveCount(7);
  await expect(page.getByTestId("week-bar").first()).toBeVisible();
  expect(await digits(page)).toBe("");
});
