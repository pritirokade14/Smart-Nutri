import { readFileSync } from "node:fs";
import { join } from "node:path";
import { cleanup, screen, waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { PortionPicker } from "@/features/foods/components/PortionPicker";
import { MESSAGES } from "../../support/analyze-fixtures";
import { apiStub, envelope, json } from "../../support/api-stub";
import { digitsOutsideAllowed, renderIntl } from "../../support/diary-render";
import {
  DAL_HIT,
  DAL_ID,
  DISH_HIT,
  DISH_ID,
  dalDetail,
} from "../../support/foods-fixtures";

vi.mock("@/lib/supabase/client", () => ({
  createSupabaseBrowserClient: () => ({
    auth: { getSession: async () => ({ data: { session: null } }) },
  }),
}));
const fetchMock = vi.hoisted(() => {
  const fn = vi.fn();
  globalThis.fetch = fn as unknown as typeof fetch;
  return fn;
});
const track = vi.hoisted(() => vi.fn());
vi.mock("@/lib/analytics", () => ({ track }));

const en = MESSAGES.en;
const DAL_PATH = `/v1/foods/food/${DAL_ID}`;

function open(hit = DAL_HIT) {
  const onLogged = vi.fn();
  renderIntl(
    <PortionPicker
      hit={hit}
      slotId="d0000000-0000-4000-8000-000000000002"
      onLogged={onLogged}
      onCancel={vi.fn()}
    />,
  );
  return onLogged;
}

beforeEach(() => {
  fetchMock.mockReset();
  track.mockReset();
});
afterEach(cleanup);

describe("PortionPicker", () => {
  it("picker offers only the API's units", async () => {
    apiStub(fetchMock).on("GET", DAL_PATH, dalDetail());
    open();
    const chips = await screen.findByTestId("unit-chips");
    const codes = within(chips)
      .getAllByRole("button")
      .map((b) => b.getAttribute("data-testid"));
    expect(codes).toEqual(["unit-g", "unit-katori", "unit-katori_medium"]);
    // Katori sizes show their ml; the medium one is smaller than the default.
    expect(within(chips).getByText("medium katori · 155 ml")).toBeTruthy();
    expect(within(chips).getByText("katori · 200 ml")).toBeTruthy();
    // piece does not resolve: only offered as "set grams", never as a chip.
    expect(screen.queryByTestId("unit-piece")).toBeNull();
  });

  it("default unit preselected", async () => {
    apiStub(fetchMock).on("GET", DAL_PATH, dalDetail());
    open();
    expect(
      (await screen.findByTestId("unit-katori")).getAttribute("aria-pressed"),
    ).toBe("true");
    expect(screen.getByTestId("unit-g").getAttribute("aria-pressed")).toBe(
      "false",
    );
  });

  it("grams always shown", async () => {
    apiStub(fetchMock).on("GET", DAL_PATH, dalDetail());
    open();
    expect((await screen.findByTestId("grams-hint")).textContent).toBe(
      "1 katori ≈ 142 g",
    );
    await userEvent.click(screen.getByTestId("unit-katori_medium"));
    // The API's number as it is, not rounded or converted.
    expect(screen.getByTestId("grams-hint").textContent).toBe(
      "1 medium katori ≈ 110.05 g",
    );
  });

  it("edit grams saves override and reloads", async () => {
    const own = dalDetail((d) => {
      d.units[1] = { ...d.units[1], grams_per_unit: 130, user_override: true };
    });
    const api = apiStub(fetchMock)
      .on("GET", DAL_PATH, dalDetail())
      .on("PUT", `${DAL_PATH}/portions/katori`, json(200, own))
      .on("DELETE", `${DAL_PATH}/portions/katori`, json(204));
    open();
    await userEvent.click(
      await screen.findByRole("button", { name: en.unit.edit_grams }),
    );
    const input = screen.getByLabelText(en.unit.edit_grams);
    await userEvent.clear(input);
    await userEvent.type(input, "130");
    await userEvent.click(
      screen.getByRole("button", { name: en.meals.log.save }),
    );
    await waitFor(() =>
      expect(screen.getByTestId("grams-hint").textContent).toContain("130 g"),
    );
    expect(api.callsTo("PUT", `${DAL_PATH}/portions/katori`)[0].body).toEqual({
      grams_per_unit: 130,
    });
    expect(screen.getByText(en.unit.your_value)).toBeTruthy();
    // Back to the standard value.
    api.on("GET", DAL_PATH, dalDetail());
    await userEvent.click(
      screen.getByRole("button", { name: en.unit.reset_grams }),
    );
    await waitFor(() =>
      expect(screen.getByTestId("grams-hint").textContent).toBe(
        "1 katori ≈ 142 g",
      ),
    );
    expect(api.callsTo("DELETE", `${DAL_PATH}/portions/katori`)).toHaveLength(
      1,
    );
  });

  it("settable unit sets grams", async () => {
    const withPiece = dalDetail((d) => {
      d.units.push({
        code: "piece",
        kind: "count",
        ml: null,
        grams_per_unit: 40,
        source: "portion_user",
        user_override: true,
      });
      d.settable_units = [];
    });
    const api = apiStub(fetchMock)
      .on("GET", DAL_PATH, dalDetail())
      .on("PUT", `${DAL_PATH}/portions/piece`, json(200, withPiece));
    open();
    await userEvent.click(
      await screen.findByRole("button", { name: "Set grams for piece" }),
    );
    await userEvent.type(screen.getByLabelText("Set grams for piece"), "40");
    await userEvent.click(
      screen.getByRole("button", { name: en.meals.log.save }),
    );
    // The new unit is offered and selected.
    await waitFor(() =>
      expect(
        screen.getByTestId("unit-piece").getAttribute("aria-pressed"),
      ).toBe("true"),
    );
    expect(api.callsTo("PUT", `${DAL_PATH}/portions/piece`)[0].body).toEqual({
      grams_per_unit: 40,
    });
  });

  it("preview comes from the API's grams and the shared fixture, unknown shows not known", async () => {
    apiStub(fetchMock).on("GET", DAL_PATH, dalDetail());
    open();
    await screen.findByTestId("portion-preview");
    // katori_cooked_dal in units/conversions.json
    expect(screen.getByTestId("preview-energy_kcal").textContent).toBe(
      "170.4 kcal",
    );
    expect(screen.getByTestId("preview-protein_g").textContent).toBe("9.9 g");
    // The eight rows, in order; a missing value is "Not known", never 0.
    expect(
      Array.from(
        screen
          .getByTestId("portion-preview")
          .querySelectorAll("[data-testid^=preview-]"),
      ).map((e) => e.getAttribute("data-testid")),
    ).toEqual([
      "preview-energy_kcal",
      "preview-protein_g",
      "preview-carbs_g",
      "preview-sugars_g",
      "preview-fat_g",
      "preview-sat_fat_g",
      "preview-fibre_g",
      "preview-salt_g",
    ]);
    expect(screen.getByTestId("preview-sat_fat_g").textContent).toBe(
      en.foods.not_known,
    );
    expect(screen.getByText(en.foods.preview_note)).toBeTruthy();
    await userEvent.click(screen.getByRole("button", { name: "1½" }));
    expect(screen.getByTestId("preview-energy_kcal").textContent).toBe(
      "255.6 kcal",
    );
  });

  it("an incomplete recipe shows the at-least note", async () => {
    apiStub(fetchMock).on(
      "GET",
      DAL_PATH,
      dalDetail((d) => {
        d.recipe_incomplete = ["fibre_g"];
      }),
    );
    open();
    expect((await screen.findByTestId("recipe-incomplete")).textContent).toBe(
      en.recipes.incomplete,
    );
  });

  it("hide_all shows no preview digits", async () => {
    apiStub(fetchMock).on(
      "GET",
      DAL_PATH,
      dalDetail((d) => {
        d.numbers_hidden = { energy: true, macros: true };
        d.per_100 = Object.fromEntries(
          Object.keys(d.per_100).map((k) => [k, null]),
        ) as typeof d.per_100;
      }),
    );
    open();
    await screen.findByTestId("grams-hint");
    expect(screen.queryByTestId("portion-preview")).toBeNull();
    expect(screen.queryByText(en.foods.not_known)).toBeNull();
    expect(screen.queryByText(en.foods.preview_note)).toBeNull();
    // Only grams, ml sizes and the quantity are left.
    expect(digitsOutsideAllowed()).toEqual([]);
  });

  it("hide_energy hides only the calories row", async () => {
    apiStub(fetchMock).on(
      "GET",
      DAL_PATH,
      dalDetail((d) => {
        d.numbers_hidden = { energy: true, macros: false };
        d.per_100 = { ...d.per_100, energy_kcal: null };
      }),
    );
    open();
    await screen.findByTestId("portion-preview");
    expect(screen.queryByTestId("preview-energy_kcal")).toBeNull();
    expect(screen.getByTestId("preview-protein_g").textContent).toBe("9.9 g");
  });

  it("dish shows ingredients and review note", async () => {
    const tadka = JSON.parse(
      readFileSync(
        join(process.cwd(), "../../packages/test-fixtures/foods/dishes.json"),
        "utf8",
      ),
    ).dishes.dal_tadka;
    apiStub(fetchMock).on(
      "GET",
      `/v1/foods/food/${DISH_ID}`,
      dalDetail((d) => {
        d.id = DISH_ID;
        d.name = "Dal tadka";
        d.per_100 = tadka.per_100;
        d.attributions = [
          "attribution.smartnutri_recipe",
          "attribution.usda_fdc",
        ];
        d.dish = {
          cooked_weight_g: tadka.cooked_weight_g,
          servings: null,
          ingredients: [
            { name: "Toor dal, dry", grams: 100 },
            { name: "Ghee", grams: 10 },
          ],
        };
      }),
    );
    open(DISH_HIT);
    const list = await screen.findByTestId("dish-ingredients");
    expect(within(list).getByText(en.foods.dish_ingredients)).toBeTruthy();
    expect(within(list).getByText(/Toor dal, dry/)).toBeTruthy();
    expect(screen.getByTestId("review-pending").textContent).toBe(
      en.foods.review_pending,
    );
    // Unknown dish values read "Not known" (never 0).
    expect(screen.getByTestId("preview-sugars_g").textContent).toBe(
      en.foods.not_known,
    );
    // Credits: the recipe line and the USDA FDC line.
    const credit = screen.getByTestId("source-credit").textContent as string;
    expect(credit).toContain(en.attribution.usda_fdc);
    expect(credit).toContain(en.attribution.smartnutri_recipe);
  });

  it("saves the food with quantity and unit, no grams", async () => {
    const api = apiStub(fetchMock)
      .on("GET", DAL_PATH, dalDetail())
      .on("POST", "/v1/meals", json(201, { id: "c1" }));
    const onLogged = open();
    await userEvent.click(
      await screen.findByRole("button", { name: en.foods.portion.save }),
    );
    await waitFor(() => expect(onLogged).toHaveBeenCalled());
    const body = api.callsTo("POST", "/v1/meals")[0].body as Record<
      string,
      unknown
    >;
    expect(body).toMatchObject({
      food_id: DAL_ID,
      quantity: 1,
      unit: "katori",
      meal_slot_id: "d0000000-0000-4000-8000-000000000002",
    });
    expect(body).not.toHaveProperty("grams");
    expect(track.mock.calls).toEqual([
      ["diary_entry_added", { method: "search" }],
    ]);
  });

  it("unit_grams_unknown maps to message", async () => {
    apiStub(fetchMock)
      .on("GET", DAL_PATH, dalDetail())
      .on("POST", "/v1/meals", json(422, envelope("unit_grams_unknown")));
    const onLogged = open();
    await userEvent.click(
      await screen.findByRole("button", { name: en.foods.portion.save }),
    );
    expect((await screen.findByRole("alert")).textContent).toBe(
      en.error.unit_grams_unknown,
    );
    expect(onLogged).not.toHaveBeenCalled();
    expect(track).not.toHaveBeenCalled();
  });

  it("quantity_out_of_range maps to message", async () => {
    apiStub(fetchMock)
      .on("GET", DAL_PATH, dalDetail())
      .on("POST", "/v1/meals", json(422, envelope("quantity_out_of_range")));
    open();
    await userEvent.click(
      await screen.findByRole("button", { name: en.foods.portion.save }),
    );
    expect((await screen.findByRole("alert")).textContent).toBe(
      en.error.quantity_out_of_range,
    );
  });
});
