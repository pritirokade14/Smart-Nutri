import { readFileSync } from "node:fs";
import { join } from "node:path";
import { expect, test } from "@playwright/test";
import { STUB, signedIn } from "./support/session";

// The Meals screen against the stub API (e2e/stub-api.mjs), spec 9.6 e2e 9.

const FIXTURES = join(process.cwd(), "../../packages/test-fixtures");
const SF_BISCUIT = (
  JSON.parse(readFileSync(join(FIXTURES, "responses/index.json"), "utf8")) as {
    products: Record<string, string>;
  }
).products.sf_biscuit as string;
const AUTH = { authorization: "Bearer e2e" };

test.describe("meals", () => {
  test.beforeEach(async ({ context, request }) => {
    await signedIn(context, request);
  });

  test("rename Snacks to Evening chai, add a fifth meal, log into it, remove it, the entry stays on its day, a seventh meal is refused", async ({
    page,
    request,
  }) => {
    // Reached from the Diary menu.
    await page.goto("/en/diary");
    await page.getByRole("button", { name: "More" }).click();
    await page.getByRole("menuitem", { name: "Edit meals" }).click();
    await expect(
      page.getByRole("heading", { level: 1, name: "Edit meals" }),
    ).toBeVisible();
    await expect(page.getByTestId("meal-slot-row")).toHaveCount(4);

    // Rename Snacks.
    await page.getByRole("button", { name: "Rename: Snacks" }).click();
    const renameInput = page.getByLabel("Rename", { exact: true });
    await renameInput.fill("Evening chai");
    // Submit the rename form itself: each row also has a "Save" for its usual time.
    await renameInput
      .locator("xpath=ancestor::form[1]")
      .getByRole("button", { name: "Save", exact: true })
      .click();
    await expect(page.getByTestId("meal-slot-name").nth(2)).toHaveText(
      "Evening chai",
    );

    // A fifth meal.
    await page.getByLabel("Add a meal", { exact: true }).fill("Post-gym");
    await page.getByRole("button", { name: "Add a meal", exact: true }).click();
    await expect(page.getByTestId("meal-slot-row")).toHaveCount(5);
    await expect(page.getByTestId("meal-slot-name").nth(4)).toHaveText(
      "Post-gym",
    );

    // Log into it (the browser would do this from the Add food panel).
    const slots = await (
      await request.get(`${STUB}/v1/meal-slots`, { headers: AUTH })
    ).json();
    const fifth = slots.items.find(
      (s: { custom_label: string | null }) => s.custom_label === "Post-gym",
    );
    const logged = await request.post(`${STUB}/v1/meals`, {
      headers: AUTH,
      data: { product_id: SF_BISCUIT, grams: 25, meal_slot_id: fifth.id },
    });
    expect(logged.status()).toBe(201);

    // Remove it: the note is shown first.
    await page.reload();
    await page
      .getByRole("button", { name: "Remove this meal: Post-gym" })
      .click();
    await expect(
      page.getByText("Food you already logged here stays in your diary."),
    ).toBeVisible();
    await page
      .getByTestId("confirm-dialog")
      .getByRole("button", { name: "Remove this meal" })
      .click();
    await expect(page.getByTestId("meal-slot-row")).toHaveCount(4);

    // The entry stays on its day, under the removed meal.
    await page.goto("/en/diary");
    const section = page.locator('[data-testid="slot-section"]', {
      hasText: "Post-gym",
    });
    await expect(section.getByTestId("slot-removed")).toHaveText(
      "Removed meal",
    );
    await expect(section.getByTestId("entry-row")).toContainText(
      "Sugar Free Biscuit",
    );

    // A seventh meal is refused: add two more (six), then the add is off.
    await page.goto("/en/diary/meals");
    for (const [n, label] of [
      [5, "Tea"],
      [6, "Supper"],
    ] as const) {
      await page.getByLabel("Add a meal", { exact: true }).fill(label);
      await page
        .getByRole("button", { name: "Add a meal", exact: true })
        .click();
      await expect(page.getByTestId("meal-slot-row")).toHaveCount(n);
      await expect(page.getByLabel("Add a meal", { exact: true })).toHaveValue(
        "",
      );
    }
    await expect(page.getByTestId("meal-slot-row")).toHaveCount(6);
    await expect(page.getByTestId("meal-limit")).toHaveText(
      "You can have up to 6 meals.",
    );
    await expect(
      page.getByRole("button", { name: "Add a meal", exact: true }),
    ).toBeDisabled();
    const seventh = await request.post(`${STUB}/v1/meal-slots`, {
      headers: AUTH,
      data: { custom_label: "Seventh" },
    });
    expect(seventh.status()).toBe(422);
    expect((await seventh.json()).error.code).toBe("meal_slot_limit_reached");
  });

  test("reorder with the buttons, and Profile links to the screen", async ({
    page,
  }) => {
    await page.goto("/en/profile/guide");
    await page.getByTestId("settings-meals-link").click();
    await expect(page.getByTestId("meals-screen")).toBeVisible();
    await page
      .getByTestId("meal-slot-row")
      .nth(1)
      .getByTestId("meal-slot-up")
      .click();
    await expect(page.getByTestId("meal-slot-name").first()).toHaveText(
      "Lunch",
    );
    await page.reload();
    await expect(page.getByTestId("meal-slot-name").first()).toHaveText(
      "Lunch",
    );
  });
});
