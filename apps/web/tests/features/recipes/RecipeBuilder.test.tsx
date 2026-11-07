import { cleanup, screen, waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { RecipeBuilder } from "@/features/recipes/components/RecipeBuilder";
import { MESSAGES } from "../../support/analyze-fixtures";
import { apiStub, envelope, json } from "../../support/api-stub";
import { digitsOutsideAllowed, renderIntl } from "../../support/diary-render";
import {
  DAL_HIT,
  DAL_ID,
  dalDetail,
  recipeOut,
} from "../../support/foods-fixtures";

vi.mock("@/lib/supabase/client", () => ({
  createSupabaseBrowserClient: () => ({
    auth: { getSession: async () => ({ data: { session: null } }) },
  }),
}));
const push = vi.hoisted(() => vi.fn());
vi.mock("next/navigation", () => ({
  useRouter: () => ({ push, replace: vi.fn(), refresh: vi.fn() }),
}));
const fetchMock = vi.hoisted(() => {
  const fn = vi.fn();
  globalThis.fetch = fn as unknown as typeof fetch;
  return fn;
});
const track = vi.hoisted(() => vi.fn());
vi.mock("@/lib/analytics", () => ({ track }));

const en = MESSAGES.en;
const RID = "e0000000-0000-4000-8000-000000000001";

beforeEach(() => {
  fetchMock.mockReset();
  push.mockReset();
});
afterEach(cleanup);

function stub() {
  return apiStub(fetchMock)
    .on("GET", "/v1/foods/search", {
      items: [DAL_HIT],
      partial: false,
      failed_sources: [],
    })
    .on("GET", `/v1/foods/food/${DAL_ID}`, dalDetail())
    .on("POST", "/v1/meals", () => json(201, { id: "m1" }))
    .on("POST", "/v1/recipes", () =>
      json(201, recipeOut("recipe_missing_fibre")),
    );
}

async function addDal() {
  await userEvent.click(
    screen.getByRole("button", { name: en.recipes.add_ingredient }),
  );
  const dialog = await screen.findByTestId("ingredient-dialog");
  await userEvent.type(
    within(dialog).getByPlaceholderText(en.foods.search_placeholder),
    "dal",
  );
  await userEvent.click(await within(dialog).findByTestId("food-hit"));
  await userEvent.click(
    await within(dialog).findByRole("button", { name: en.foods.portion.save }),
  );
}

describe("RecipeBuilder", () => {
  it("adds ingredient through picker without logging", async () => {
    const api = stub();
    renderIntl(<RecipeBuilder />);
    await addDal();
    const rows = await screen.findAllByTestId("recipe-ingredient");
    expect(rows[0].textContent).toContain("Toor dal, cooked");
    expect(api.callsTo("POST", "/v1/meals")).toHaveLength(0);
    expect(track).not.toHaveBeenCalled();
  });

  it("no numbers before save", async () => {
    stub();
    renderIntl(<RecipeBuilder />);
    await addDal();
    await screen.findAllByTestId("recipe-ingredient");
    expect(screen.queryByTestId("recipe-nutrients")).toBeNull();
    expect(digitsOutsideAllowed()).toEqual([]);
  });

  it("save sends the ingredients, servings and cooked weight, then shows at least", async () => {
    const api = stub();
    renderIntl(<RecipeBuilder />);
    await userEvent.type(
      screen.getByLabelText(en.recipes.name),
      "Rice and dal",
    );
    await addDal();
    await screen.findAllByTestId("recipe-ingredient");
    await userEvent.type(screen.getByLabelText(en.recipes.servings), "2");
    await userEvent.type(
      screen.getByLabelText(en.recipes.cooked_weight),
      "400",
    );
    expect(screen.getByText(en.recipes.cooked_weight_tip)).toBeTruthy();
    await userEvent.click(
      screen.getByRole("button", { name: en.recipes.save }),
    );
    const fibre = await screen.findByTestId("per-100g-fibre_g");
    expect(fibre.textContent).toContain("At least");
    const sent = api.callsTo("POST", "/v1/recipes")[0].body as Record<
      string,
      unknown
    >;
    expect(sent).toMatchObject({
      name: "Rice and dal",
      servings: 2,
      cooked_weight_g: 400,
      ingredients: [{ food_id: DAL_ID, quantity: 1, unit: "katori" }],
    });
  });

  it("unavailable ingredient blocks save", async () => {
    const base = recipeOut("recipe_complete");
    const gone = {
      ...base,
      ingredients: [
        {
          ...base.ingredients[0],
          available: false,
          food_id: null,
          custom_food_id: "c1",
        },
      ],
    };
    const api = apiStub(fetchMock).on("GET", `/v1/recipes/${RID}`, gone);
    renderIntl(<RecipeBuilder id={RID} />);
    expect(
      (await screen.findByTestId("ingredient-unavailable")).textContent,
    ).toBe(en.recipes.ingredient_unavailable);
    const save = screen.getByRole("button", { name: en.recipes.save });
    expect((save as HTMLButtonElement).disabled).toBe(true);
    // Replacing it (remove, then add) lifts the block.
    await userEvent.click(
      within(screen.getByTestId("recipe-ingredient")).getByRole("button", {
        name: en.diary.delete,
      }),
    );
    expect(screen.queryByTestId("ingredient-unavailable")).toBeNull();
    expect((save as HTMLButtonElement).disabled).toBe(false);
    expect(api.callsTo("PUT", `/v1/recipes/${RID}`)).toHaveLength(0);
  });

  it("log a serving opens the recipe picker", async () => {
    const api = apiStub(fetchMock)
      .on("GET", `/v1/recipes/${RID}`, recipeOut("recipe_servings_4"))
      .on("GET", `/v1/foods/recipe/${RID}`, {
        ...dalDetail(),
        kind: "recipe",
        id: RID,
        name: "Rice and dal",
        units: [
          {
            code: "serving",
            kind: "serving",
            ml: null,
            grams_per_unit: 200,
            source: "serving",
            user_override: false,
          },
        ],
        default_unit: "serving",
        settable_units: [],
      })
      .on("POST", "/v1/meals", () => json(201, { id: "m1" }));
    renderIntl(<RecipeBuilder id={RID} />);
    await userEvent.click(
      await screen.findByRole("button", { name: en.recipes.log_serving }),
    );
    const dialog = await screen.findByTestId("log-recipe-dialog");
    await userEvent.click(
      await within(dialog).findByRole("button", {
        name: en.foods.portion.save,
      }),
    );
    await waitFor(() =>
      expect(api.callsTo("POST", "/v1/meals")).toHaveLength(1),
    );
    expect(api.callsTo("POST", "/v1/meals")[0].body).toMatchObject({
      recipe_id: RID,
      quantity: 1,
      unit: "serving",
    });
    expect(track).toHaveBeenCalledWith("diary_entry_added", {
      method: "recipe",
    });
  });

  it("a retired dish ingredient shows its message", async () => {
    apiStub(fetchMock)
      .on("GET", "/v1/foods/search", {
        items: [DAL_HIT],
        partial: false,
        failed_sources: [],
      })
      .on("GET", `/v1/foods/food/${DAL_ID}`, dalDetail())
      .on("POST", "/v1/recipes", () => json(422, envelope("food_retired")));
    renderIntl(<RecipeBuilder />);
    await userEvent.type(screen.getByLabelText(en.recipes.name), "X");
    await addDal();
    await screen.findAllByTestId("recipe-ingredient");
    await userEvent.click(
      screen.getByRole("button", { name: en.recipes.save }),
    );
    expect((await screen.findByRole("alert")).textContent).toBe(
      en.error.food_retired,
    );
  });
});
