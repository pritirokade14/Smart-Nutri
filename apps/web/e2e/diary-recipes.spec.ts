import { expect, test } from "@playwright/test";
import { signedIn } from "./support/session";

// Custom foods and recipes against the stub API (spec 9.6 e2e 5): create a
// food with a blank nutrient, build a recipe from two ingredients with 2
// servings and a cooked weight, see "At least" on the incomplete nutrient,
// then log one serving.

test.describe("diary recipes", () => {
  test.beforeEach(async ({ context, request }) => {
    await signedIn(context, request);
  });

  test("custom food, recipe with at least, log a serving", async ({ page }) => {
    // 1. A custom food: fibre left blank (unknown, never 0).
    await page.goto("/en/diary/foods/new");
    await page.getByLabel("Name", { exact: true }).fill("Homemade ladoo");
    await page.getByLabel("Energy (kcal)").fill("400");
    await page.getByLabel("Protein (g)").fill("6");
    await page.getByRole("button", { name: "Save food" }).click();
    await page.waitForURL("**/diary/my-foods");
    await expect(page.getByTestId("my-food")).toContainText("Homemade ladoo");

    // 2. A recipe: dal from the catalogue + the ladoo, 2 servings, 400 g cooked.
    await page.goto("/en/diary/recipes/new");
    await page.getByLabel("Recipe name").fill("Dal and ladoo");

    await page.getByRole("button", { name: "Add ingredient" }).click();
    const dialog = page.getByTestId("ingredient-dialog");
    await dialog.getByPlaceholder("Search foods, dishes or brands").fill("dal");
    await dialog.getByTestId("food-hit").click();
    await dialog.getByRole("button", { name: "Add", exact: true }).click();
    await expect(dialog).toBeHidden();

    await page.getByRole("button", { name: "Add ingredient" }).click();
    await dialog
      .getByPlaceholder("Search foods, dishes or brands")
      .fill("ladoo");
    await expect(dialog.getByTestId("food-group-mine")).toBeVisible();
    await dialog.getByTestId("food-hit").click();
    await dialog.getByRole("button", { name: "Add", exact: true }).click();
    await expect(page.getByTestId("recipe-ingredient")).toHaveCount(2);
    // Before saving: the ingredient list only, no nutrient numbers.
    await expect(page.getByTestId("recipe-nutrients")).toBeHidden();

    await page.getByLabel("Number of servings").fill("2");
    await page.getByLabel("Cooked weight (g)").fill("400");
    await page
      .getByRole("button", { name: "Save recipe", exact: true })
      .click();

    // 3. Fibre is known for the dal only: "At least", with the marker.
    const fibre = page.getByTestId("per-100g-fibre_g");
    await expect(fibre).toContainText("At least");
    await expect(page.getByTestId("per-100g-fibre_g-incomplete")).toBeVisible();
    await expect(page.getByTestId("per-100g-protein_g")).not.toContainText(
      "At least",
    );

    // 4. Log one serving: it shows on the day, with the USDA credit.
    await page.getByRole("button", { name: "Log a serving" }).click();
    const log = page.getByTestId("log-recipe-dialog");
    await log.getByRole("button", { name: "Add", exact: true }).click();
    await page.waitForURL("**/diary");
    const row = page
      .getByTestId("entry-row")
      .filter({ hasText: "Dal and ladoo" });
    await expect(row).toBeVisible();
    await expect(row.getByTestId("entry-portion")).toContainText("1 serving");
    await expect(row.getByTestId("source-credit")).toContainText(
      "USDA FoodData Central",
    );
    // The day total is flagged: the recipe's fibre is a lower bound.
    await expect(row.getByTestId("entry-incomplete")).toBeVisible();
  });
});
