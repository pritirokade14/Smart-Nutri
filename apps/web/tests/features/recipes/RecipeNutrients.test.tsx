import { cleanup, screen } from "@testing-library/react";
import { afterEach, describe, expect, it } from "vitest";
import { RecipeNutrients } from "@/features/recipes/components/RecipeNutrients";
import { MESSAGES } from "../../support/analyze-fixtures";
import { digitsOutsideAllowed, renderIntl } from "../../support/diary-render";
import { recipeOut } from "../../support/foods-fixtures";

const en = MESSAGES.en;
afterEach(cleanup);

describe("RecipeNutrients", () => {
  it("renders recipes/expected recipe_missing_fibre: fibre is at least, with the marker", () => {
    renderIntl(<RecipeNutrients recipe={recipeOut("recipe_missing_fibre")} />);
    const fibre = screen.getByTestId("per-100g-fibre_g");
    expect(fibre.textContent).toContain("At least 2.1 g");
    expect(screen.getByTestId("per-100g-fibre_g-incomplete").textContent).toBe(
      en.recipes.incomplete,
    );
    // A complete nutrient is a plain value with no marker.
    expect(screen.getByTestId("per-100g-protein_g").textContent).toBe("5 g");
    expect(screen.queryByTestId("per-100g-protein_g-incomplete")).toBeNull();
  });

  it("incomplete recipe nutrient renders at least, never a plain number", () => {
    renderIntl(
      <RecipeNutrients
        recipe={recipeOut("recipe_all_unknown_sat_fat", {
          incomplete_nutrients: ["energy_kcal"],
        })}
      />,
    );
    const energy = screen.getByTestId("per-100g-energy_kcal").textContent;
    expect(energy).toMatch(/^At least /);
    expect(screen.getByTestId("per-100g-energy_kcal-incomplete")).toBeTruthy();
  });

  it("an unknown value reads not known, never 0", () => {
    renderIntl(
      <RecipeNutrients recipe={recipeOut("recipe_all_unknown_sat_fat")} />,
    );
    expect(screen.getByTestId("per-100g-sat_fat_g").textContent).toBe(
      en.foods.not_known,
    );
  });

  it("hide_all shows no digits", () => {
    const base = recipeOut("recipe_missing_fibre");
    const { container } = renderIntl(
      <RecipeNutrients
        recipe={{
          ...base,
          per_100g: Object.fromEntries(
            Object.keys(base.per_100g).map((k) => [k, null]),
          ) as typeof base.per_100g,
          per_serving: null,
          numbers_hidden: { energy: true, macros: true },
        }}
      />,
    );
    expect(container.textContent).toBe("");
    expect(digitsOutsideAllowed()).toEqual([]);
  });

  it("per serving shows when the API sends it", () => {
    renderIntl(<RecipeNutrients recipe={recipeOut("recipe_servings_4")} />);
    expect(screen.getByTestId("per-serving-energy_kcal")).toBeTruthy();
  });
});
