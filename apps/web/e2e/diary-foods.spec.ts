import { expect, test } from "@playwright/test";
import { STUB, signedIn, signIn } from "./support/session";

// Food search, the household-unit portion picker and food entries against the
// stub API (e2e/stub-api.mjs), spec 9.6 e2e 1 adapted.

test.describe("diary foods", () => {
  test.beforeEach(async ({ context, request }) => {
    await signedIn(context, request);
  });

  test("search roti and dal, pick units, edit to 3 roti, delete", async ({
    page,
  }) => {
    await page.goto("/en/diary");
    await page.getByRole("button", { name: "Add food", exact: true }).click();
    const panel = page.getByTestId("add-food-panel");
    await panel.getByRole("tab", { name: "Search products" }).click();

    // Roti: the packaged one; 2 roti, with the grams shown.
    await panel.getByPlaceholder("Search foods, dishes or brands").fill("roti");
    await expect(panel.getByTestId("food-group-packaged")).toBeVisible();
    await panel.getByTestId("food-hit").click();
    await expect(panel.getByTestId("grams-hint")).toHaveText("1 roti ≈ 68 g");
    await panel.getByLabel("Amount", { exact: true }).fill("2");
    await expect(panel.getByTestId("preview-energy_kcal")).toBeVisible();
    await panel.getByRole("button", { name: "Add", exact: true }).click();
    await expect(panel).toBeHidden();
    const roti = page.getByTestId("entry-row").filter({ hasText: "roti" });
    await expect(roti.getByTestId("entry-portion")).toHaveText(
      "2 rotis · ≈ 136 g",
    );

    // Dal: cooked toor dal in katori, with its size and grams.
    await page.getByRole("button", { name: "Add food", exact: true }).click();
    await panel.getByRole("tab", { name: "Search products" }).click();
    await panel.getByPlaceholder("Search foods, dishes or brands").fill("dal");
    await expect(panel.getByTestId("food-group-indian")).toBeVisible();
    await expect(panel.getByTestId("food-hit")).toContainText(
      "Nutrition data: USDA FoodData Central",
    );
    await panel.getByTestId("food-hit").click();
    await expect(panel.getByTestId("unit-katori")).toHaveAttribute(
      "aria-pressed",
      "true",
    );
    await expect(panel.getByTestId("unit-katori")).toContainText("200 ml");
    await expect(panel.getByTestId("grams-hint")).toHaveText(
      "1 katori ≈ 142 g",
    );
    await expect(panel.getByTestId("preview-energy_kcal")).toHaveText(
      "170.4 kcal",
    );
    await expect(panel.getByTestId("preview-sat_fat_g")).toHaveText(
      "Not known",
    );
    await panel.getByRole("button", { name: "Add", exact: true }).click();
    await expect(panel).toBeHidden();
    const dal = page.getByTestId("entry-row").filter({ hasText: "dal" });
    await expect(dal.getByTestId("entry-portion")).toHaveText(
      "1 katori · ≈ 142 g",
    );
    await expect(dal.getByTestId("source-credit")).toContainText(
      "USDA FoodData Central",
    );

    // Edit the roti to 3: the grams come from the API.
    await roti.click();
    const edit = page.getByTestId("edit-entry-dialog");
    await edit.getByLabel("Amount", { exact: true }).fill("3");
    await edit.getByRole("button", { name: "Save" }).click();
    await expect(edit).toBeHidden();
    await expect(
      page
        .getByTestId("entry-row")
        .filter({ hasText: "roti" })
        .getByTestId("entry-portion"),
    ).toHaveText("3 rotis · ≈ 204 g");

    // Delete both.
    for (let left = 2; left > 0; left--) {
      await page.getByTestId("entry-row").first().click();
      await page
        .getByTestId("edit-entry-dialog")
        .getByRole("button", { name: "Remove" })
        .click();
      await page
        .getByTestId("confirm-dialog")
        .getByRole("button", { name: "Remove" })
        .click();
      await expect(page.getByTestId("entry-row")).toHaveCount(left - 1);
    }
    await expect(page.getByTestId("diary-empty")).toBeVisible();
  });

  test("hide-all numbers: the picker shows grams and no preview", async ({
    page,
    context,
    request,
  }) => {
    await request.post(`${STUB}/__reset?terms=current&health_data=current`);
    await signIn(context);
    const saved = await request.put(`${STUB}/v1/targets/settings`, {
      headers: { authorization: "Bearer e2e" },
      data: {
        direction: "lose",
        activity_level: "light",
        pregnant_or_breastfeeding: false,
        numbers_display: "hide_all",
      },
    });
    expect(saved.ok()).toBe(true);
    await page.goto("/en/diary");
    await page.getByRole("button", { name: "Add food", exact: true }).click();
    const panel = page.getByTestId("add-food-panel");
    await panel.getByRole("tab", { name: "Search products" }).click();
    await panel.getByPlaceholder("Search foods, dishes or brands").fill("dal");
    await panel.getByTestId("food-hit").click();
    await expect(panel.getByTestId("grams-hint")).toHaveText(
      "1 katori ≈ 142 g",
    );
    await expect(panel.getByTestId("portion-preview")).toHaveCount(0);
  });

  test("how we score explains the food data", async ({ page }) => {
    await page.goto("/en/how-we-score");
    await expect(page.getByTestId("methodology-food_data")).toContainText(
      "USDA FoodData Central",
    );
  });
});
