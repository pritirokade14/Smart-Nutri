import { readFileSync } from "node:fs";
import { join } from "node:path";
import { expect, test } from "@playwright/test";
import { STUB, signedIn } from "./support/session";

// Favourites and saved meals against the stub API (e2e/stub-api.mjs).

const FIXTURES = join(process.cwd(), "../../packages/test-fixtures");
const SF_BISCUIT = (
  JSON.parse(readFileSync(join(FIXTURES, "responses/index.json"), "utf8")) as {
    products: Record<string, string>;
  }
).products.sf_biscuit as string;
const BREAKFAST = "d0000000-0000-4000-8000-000000000001";
const DAL = "f0000000-0000-4000-8000-000000000001";
const AUTH = { authorization: "Bearer e2e" };

const istDay = (offset = 0): string => {
  const d = new Date(Date.now() + 330 * 60_000);
  d.setUTCDate(d.getUTCDate() + offset);
  return d.toISOString().slice(0, 10);
};

test.describe("diary favourites", () => {
  test.beforeEach(async ({ context, request }) => {
    await signedIn(context, request);
  });

  test("star a recent, find it under Favourites, one tap logs it", async ({
    page,
    request,
  }) => {
    const seeded = await request.post(`${STUB}/v1/meals`, {
      headers: AUTH,
      data: {
        food_id: DAL,
        quantity: 1,
        unit: "katori",
        meal_slot_id: BREAKFAST,
      },
    });
    expect(seeded.status()).toBe(201);

    await page.goto("/en/diary");
    await expect(page.getByTestId("entry-row")).toHaveCount(1);
    await page.getByRole("button", { name: "Add food", exact: true }).click();
    const panel = page.getByTestId("add-food-panel");
    await panel
      .getByTestId("recents")
      .getByRole("button", { name: "Add to favourites" })
      .click();
    await expect(
      panel.getByRole("button", { name: "Remove from favourites" }),
    ).toBeVisible();

    await panel.getByRole("tab", { name: "Favourites" }).click();
    await expect(panel.getByTestId("favourite-item")).toHaveCount(1);
    await expect(panel.getByTestId("favourite-item")).toContainText("dal");
    await panel.getByTestId("favourite-food").click();
    await expect(panel).toBeHidden();
    await expect(page.getByTestId("entry-row")).toHaveCount(2);

    // Unstar from the Favourites tab: the row goes.
    await page.getByRole("button", { name: "Add food", exact: true }).click();
    await panel.getByRole("tab", { name: "Favourites" }).click();
    await panel.getByRole("button", { name: "Remove from favourites" }).click();
    await expect(panel.getByTestId("favourites-empty")).toHaveText(
      "No favourites yet",
    );
  });

  test("save Breakfast as a favourite meal, log it again the next day", async ({
    page,
    request,
  }) => {
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
    await page.getByRole("button", { name: "Previous day" }).click();
    await expect(page.getByTestId("entry-row")).toHaveCount(1);
    const breakfast = page
      .getByTestId("slot-section")
      .filter({ has: page.getByRole("heading", { name: "Breakfast" }) });
    await breakfast
      .getByRole("button", { name: "Save as favourite meal" })
      .click();
    const dialog = page.getByTestId("save-meal-dialog");
    await dialog.getByLabel("Meal name").fill("My usual breakfast");
    await dialog
      .getByRole("button", { name: "Save as favourite meal" })
      .click();
    await expect(page.getByTestId("diary-notice")).toHaveText(
      "Added to favourites",
    );

    await page.getByRole("button", { name: "Next day" }).click();
    await expect(page.getByTestId("day-title")).toHaveText("Today");
    await expect(page.getByTestId("entry-row")).toHaveCount(0);
    await page.getByRole("button", { name: "Add food", exact: true }).click();
    const panel = page.getByTestId("add-food-panel");
    await panel.getByRole("tab", { name: "Favourites" }).click();
    await expect(panel.getByTestId("favourite-item")).toContainText(
      "My usual breakfast",
    );
    await expect(panel.getByTestId("favourite-meal-items")).toHaveText(
      "1 item",
    );
    await panel.getByRole("button", { name: "Log again" }).click();
    await expect(panel).toBeHidden();
    await expect(page.getByTestId("diary-notice")).toHaveText("1 item copied");
    await expect(page.getByTestId("entry-row")).toHaveCount(1);
    await expect(page.getByTestId("entry-row")).toContainText(
      "Sugar Free Biscuit",
    );
  });
});
