import { cleanup, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { createTranslator } from "next-intl";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import type { MealOut } from "@/features/diary/api/diary";
import { AddFoodPanel } from "@/features/diary/components/AddFoodPanel";
import { EntryRow } from "@/features/diary/components/EntryRow";
import type { FoodUnitOut } from "@/features/foods/api/foods";
import { FoodSearch } from "@/features/foods/components/FoodSearch";
import { PortionPicker } from "@/features/foods/components/PortionPicker";
import { portionLine } from "@/features/foods/lib/portionLine";
import { unitChipLabel, unitLabel } from "@/features/foods/lib/unitLabel";
import { MESSAGES } from "../../support/analyze-fixtures";
import { apiStub, envelope, json } from "../../support/api-stub";
import { diaryDay } from "../../support/diary-fixtures";
import { renderIntl } from "../../support/diary-render";
import { DAL_ID, dalDetail } from "../../support/foods-fixtures";

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
vi.mock("@/lib/analytics", () => ({ track: vi.fn() }));

const en = MESSAGES.en;
const tr = (k: string, v?: Record<string, string | number>) =>
  createTranslator({ locale: "en", messages: en })(k as never, v as never);
const SLOT = "d0000000-0000-4000-8000-000000000002";
const SLOTS = {
  items: [
    {
      id: SLOT,
      member_id: "m",
      position: 0,
      label_key: "diary.slot.lunch",
      custom_label: null,
      default_time_window: null,
      is_default: true,
      archived: false,
    },
  ],
  suggested_slot_id: SLOT,
};
const RECENT = {
  source_kind: "food",
  product_id: null,
  food_id: "f1",
  barcode: null,
  name: "Whole wheat roti",
  grade: null,
  grams: 136,
  basis: "g",
  quantity: 2,
  unit: "roti",
  unit_source: "portion",
  meal_slot_id: SLOT,
  last_eaten_at: "2026-11-06T07:45:00Z",
  attribution: null,
  attributions: [],
};

beforeEach(() => {
  fetchMock.mockReset();
});
afterEach(cleanup);

function panel(recents: object[], log?: Response) {
  const api = apiStub(fetchMock)
    .on("GET", "/v1/meal-slots", SLOTS)
    .on("GET", "/v1/diary/recents", { items: recents })
    .on("POST", "/v1/meals", log ?? json(201, { id: "m1" }));
  renderIntl(
    <AddFoodPanel
      date="2026-11-07"
      today="2026-11-07"
      slotId={SLOT}
      onClose={vi.fn()}
      onLogged={vi.fn()}
    />,
  );
  return api;
}

describe("unitLabel", () => {
  it("an unknown code shows the code itself", () => {
    expect(unitLabel(tr, "bowl_xl", 2)).toBe("bowl_xl");
    expect(unitLabel(tr, "roti", 2)).toBe("rotis");
  });

  it("the ml chip shows whenever ml is set, but never for ml itself", () => {
    const u = (
      code: string,
      kind: FoodUnitOut["kind"],
      ml: number | null,
    ): FoodUnitOut => ({
      code,
      kind,
      ml,
      grams_per_unit: 10,
      source: "density",
      user_override: false,
    });
    expect(unitChipLabel(tr, u("glass", "count", 250))).toBe("glass · 250 ml");
    expect(unitChipLabel(tr, u("ml", "volume", 1))).toBe("ml");
    expect(unitChipLabel(tr, u("roti", "count", null))).toBe("roti");
  });
});

describe("portionLine", () => {
  it("grams, ml, and the approximate mark", () => {
    expect(
      portionLine(tr, { quantity: 2, unit: "roti", grams: 136, basis: "g" }),
    ).toBe("2 rotis · 136 g");
    expect(
      portionLine(tr, {
        quantity: 2,
        unit: "roti",
        grams: 136,
        basis: "g",
        unitSource: "portion",
      }),
    ).toBe("2 rotis · ≈ 136 g");
    expect(
      portionLine(tr, {
        quantity: 1,
        unit: "glass",
        grams: 200,
        basis: "ml",
        unitSource: "density",
      }),
    ).toBe("1 glass · ≈ 200 ml");
    expect(portionLine(tr, { grams: 350, basis: "ml" })).toBe("350 ml");
    expect(portionLine(tr, { grams: 350 })).toBe("350 g");
    expect(
      portionLine(tr, {
        quantity: 1,
        unit: "g",
        grams: 5,
        unitSource: "grams",
      }),
    ).toBe("5 g");
  });
});

describe("entry row", () => {
  const BASE = diaryDay("day_complete_under").slots.flatMap(
    (s) => s.entries,
  )[0] as MealOut;
  it("formats amounts and marks approximate grams", () => {
    renderIntl(
      <EntryRow
        entry={{
          ...BASE,
          quantity: 1.5,
          unit: "katori",
          grams: 213.04,
          basis: "g",
          unit_source: "density",
        }}
        onEdit={vi.fn()}
      />,
    );
    expect(screen.getByTestId("entry-portion").textContent).toBe(
      "1.5 katoris · ≈ 213 g",
    );
  });
});

describe("recents", () => {
  it("show grams like Android and the approximate mark", async () => {
    panel([RECENT]);
    expect((await screen.findByTestId("recent-item")).textContent).toContain(
      "2 rotis · ≈ 136 g",
    );
  });

  it("an ml recent shows ml", async () => {
    panel([
      {
        ...RECENT,
        basis: "ml",
        quantity: null,
        unit: null,
        unit_source: null,
        grams: 200,
      },
    ]);
    expect((await screen.findByTestId("recent-item")).textContent).toContain(
      "200 ml",
    );
  });

  it("a custom food and a recipe recent log by their own ids", async () => {
    const api = panel([
      {
        ...RECENT,
        source_kind: "custom_food",
        food_id: null,
        custom_food_id: "cf1",
        name: "Ladoo",
      },
      {
        ...RECENT,
        source_kind: "recipe",
        food_id: null,
        recipe_id: "r1",
        name: "Rice and dal",
        unit: "serving",
        quantity: 1,
      },
    ]);
    const items = await screen.findAllByTestId("recent-item");
    await userEvent.click(items[0]);
    await waitFor(() =>
      expect(api.callsTo("POST", "/v1/meals")).toHaveLength(1),
    );
    expect(api.callsTo("POST", "/v1/meals")[0].body).toMatchObject({
      custom_food_id: "cf1",
    });
    await userEvent.click(items[1]);
    await waitFor(() =>
      expect(api.callsTo("POST", "/v1/meals")).toHaveLength(2),
    );
    expect(api.callsTo("POST", "/v1/meals")[1].body).toMatchObject({
      recipe_id: "r1",
    });
  });

  it("a retired dish shows food_retired", async () => {
    panel([RECENT], json(422, envelope("food_retired")));
    await userEvent.click(await screen.findByTestId("recent-item"));
    expect((await screen.findByRole("alert")).textContent).toBe(
      en.error.food_retired,
    );
  });
});

describe("portion picker errors and kinds", () => {
  it("unit_grams_unknown shows its message", async () => {
    apiStub(fetchMock)
      .on("GET", `/v1/foods/food/${DAL_ID}`, dalDetail())
      .on("POST", "/v1/meals", () => json(422, envelope("unit_grams_unknown")));
    renderIntl(
      <PortionPicker
        hit={{ kind: "food", id: DAL_ID, name: "Dal", is_dish: false }}
        slotId={SLOT}
        onLogged={vi.fn()}
        onCancel={vi.fn()}
      />,
    );
    await userEvent.click(
      await screen.findByRole("button", { name: en.foods.portion.save }),
    );
    expect((await screen.findByRole("alert")).textContent).toBe(
      en.error.unit_grams_unknown,
    );
  });

  it("a custom food logs by custom_food_id", async () => {
    const api = apiStub(fetchMock)
      .on("GET", "/v1/foods/custom_food/cf1", {
        ...dalDetail(),
        kind: "custom_food",
        id: "cf1",
      })
      .on("POST", "/v1/meals", () => json(201, { id: "m1" }));
    renderIntl(
      <PortionPicker
        hit={{ kind: "custom_food", id: "cf1", name: "Ladoo", is_dish: false }}
        slotId={SLOT}
        onLogged={vi.fn()}
        onCancel={vi.fn()}
      />,
    );
    await userEvent.click(
      await screen.findByRole("button", { name: en.foods.portion.save }),
    );
    await waitFor(() =>
      expect(api.callsTo("POST", "/v1/meals")).toHaveLength(1),
    );
    expect(api.callsTo("POST", "/v1/meals")[0].body).toMatchObject({
      custom_food_id: "cf1",
    });
  });
});

describe("search groups", () => {
  it("shows my foods first and a typed barcode through foods_by_barcode", async () => {
    const api = apiStub(fetchMock)
      .on("GET", "/v1/foods/search", {
        items: [
          {
            kind: "custom_food",
            id: "cf1",
            name: "Ladoo",
            brand: null,
            group: "mine",
            is_dish: false,
            grade: null,
            attribution: null,
            attributions: [],
          },
        ],
        partial: false,
        failed_sources: [],
      })
      .on("GET", "/v1/foods/barcode/8901234567890", {
        ...dalDetail(),
        kind: "off",
        id: "8901234567890",
        name: "Biscuit",
        attributions: ["attribution.off"],
      });
    const onPick = vi.fn();
    const onBarcodeProduct = vi.fn();
    renderIntl(
      <FoodSearch onPick={onPick} onBarcodeProduct={onBarcodeProduct} />,
    );
    await userEvent.type(
      screen.getByPlaceholderText(en.foods.search_placeholder),
      "8901234567890",
    );
    const code = await screen.findByTestId("barcode-hit");
    expect(code.textContent).toContain("Biscuit");
    await userEvent.click(code);
    // A product / OFF item keeps the verdict flow: never the portion picker.
    expect(onPick).not.toHaveBeenCalled();
    expect(onBarcodeProduct).toHaveBeenCalledWith("8901234567890");
    expect(api.callsTo("GET", "/v1/foods/barcode/8901234567890")).toHaveLength(
      1,
    );
  });

  it("a typed barcode that is my own food goes to the portion picker", async () => {
    apiStub(fetchMock)
      .on("GET", "/v1/foods/search", {
        items: [],
        partial: false,
        failed_sources: [],
      })
      .on("GET", "/v1/foods/barcode/8901234567891", {
        ...dalDetail(),
        kind: "custom_food",
        id: "cf1",
        name: "Ladoo",
      });
    const onPick = vi.fn();
    const onBarcodeProduct = vi.fn();
    renderIntl(
      <FoodSearch onPick={onPick} onBarcodeProduct={onBarcodeProduct} />,
    );
    await userEvent.type(
      screen.getByPlaceholderText(en.foods.search_placeholder),
      "8901234567891",
    );
    await userEvent.click(await screen.findByTestId("barcode-hit"));
    expect(onBarcodeProduct).not.toHaveBeenCalled();
    expect(onPick).toHaveBeenCalledWith(
      expect.objectContaining({ kind: "custom_food", id: "cf1" }),
      true,
    );
  });

  it("the mine group comes first with its kind chip", async () => {
    apiStub(fetchMock).on("GET", "/v1/foods/search", {
      items: [
        {
          kind: "recipe",
          id: "r1",
          name: "Rice and dal",
          brand: null,
          group: "mine",
          is_dish: false,
          grade: null,
          attribution: null,
          attributions: [],
        },
      ],
      partial: false,
      failed_sources: [],
    });
    renderIntl(<FoodSearch onPick={vi.fn()} />);
    await userEvent.type(
      screen.getByPlaceholderText(en.foods.search_placeholder),
      "rice",
    );
    const mine = await screen.findByTestId("food-group-mine");
    expect(mine.textContent).toContain(en.foods.group.mine);
    expect(mine.textContent).toContain(en.foods.kind.recipe);
  });
});
