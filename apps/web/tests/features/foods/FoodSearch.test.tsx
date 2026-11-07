import { cleanup, screen, waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { AddFoodPanel } from "@/features/diary/components/AddFoodPanel";
import { FoodSearch } from "@/features/foods/components/FoodSearch";
import { MESSAGES } from "../../support/analyze-fixtures";
import { apiStub, json } from "../../support/api-stub";
import { renderIntl } from "../../support/diary-render";
import {
  DAL_HIT,
  DAL_ID,
  DISH_HIT,
  dalDetail,
  ROTI_HIT,
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
const SLOT = "d0000000-0000-4000-8000-000000000002";

beforeEach(() => {
  fetchMock.mockReset();
  track.mockReset();
});
afterEach(cleanup);

const search = (out: object) =>
  apiStub(fetchMock).on("GET", "/v1/foods/search", out);
const type = async (text: string) =>
  userEvent.type(
    screen.getByPlaceholderText(en.foods.search_placeholder),
    text,
  );

describe("FoodSearch", () => {
  it("groups indian before packaged", async () => {
    // The API orders the items; the groups keep the Indian group on top.
    search({
      items: [ROTI_HIT, DAL_HIT, DISH_HIT],
      partial: false,
      failed_sources: [],
    });
    renderIntl(<FoodSearch onPick={vi.fn()} />);
    await type("dal");
    await screen.findAllByTestId("food-hit");
    const groups = screen
      .getAllByTestId(/^food-group-/)
      .map((g) => g.getAttribute("data-testid"));
    expect(groups).toEqual(["food-group-indian", "food-group-packaged"]);
    const indian = screen.getByTestId("food-group-indian");
    expect(within(indian).getByText(en.foods.group.indian)).toBeTruthy();
    // A dish is badged as one.
    expect(within(indian).getByText(en.foods.kind.dish)).toBeTruthy();
    expect(within(indian).getByText(en.foods.kind.food)).toBeTruthy();
    expect(
      within(screen.getByTestId("food-group-packaged")).getByText(
        en.foods.kind.product,
      ),
    ).toBeTruthy();
  });

  it("partial shows note not empty state", async () => {
    search({ items: [], partial: true, failed_sources: ["off"] });
    renderIntl(<FoodSearch onPick={vi.fn()} />);
    await type("roti");
    expect((await screen.findByTestId("food-partial")).textContent).toBe(
      en.foods.partial_results,
    );
    expect(screen.queryByTestId("food-no-results")).toBeNull();
  });

  it("no results only when nothing came back and nothing failed", async () => {
    search({ items: [], partial: false, failed_sources: [] });
    renderIntl(<FoodSearch onPick={vi.fn()} />);
    await type("zzzz");
    expect((await screen.findByTestId("food-no-results")).textContent).toBe(
      en.foods.no_results,
    );
  });

  it("hits show credit", async () => {
    search({ items: [DISH_HIT], partial: false, failed_sources: [] });
    renderIntl(<FoodSearch onPick={vi.fn()} />);
    await type("dal");
    const hit = await screen.findByTestId("food-hit");
    expect(hit.textContent).toContain(en.attribution.usda_fdc);
    expect(hit.textContent).toContain(en.attribution.smartnutri_recipe);
  });

  it("debounces and waits for two letters", async () => {
    const api = search({
      items: [DAL_HIT],
      partial: false,
      failed_sources: [],
    });
    renderIntl(<FoodSearch onPick={vi.fn()} />);
    await type("d");
    await new Promise((r) => setTimeout(r, 450));
    expect(api.callsTo("GET", "/v1/foods/search")).toHaveLength(0);
    await type("al");
    await screen.findByTestId("food-hit");
    expect(api.callsTo("GET", "/v1/foods/search")).toHaveLength(1);
    expect(api.callsTo("GET", "/v1/foods/search")[0].query.get("q")).toBe(
      "dal",
    );
  });

  it("search tap sends diary_entry_added method search only", async () => {
    const api = apiStub(fetchMock)
      .on("GET", "/v1/meal-slots", {
        items: [
          {
            id: SLOT,
            member_id: "m",
            position: 1,
            label_key: "diary.slot.lunch",
            custom_label: null,
            default_time_window: null,
            is_default: true,
            archived: false,
          },
        ],
        suggested_slot_id: SLOT,
      })
      .on("GET", "/v1/diary/recents", { items: [] })
      .on("GET", "/v1/foods/search", {
        items: [DAL_HIT],
        partial: false,
        failed_sources: [],
      })
      .on("GET", `/v1/foods/food/${DAL_ID}`, dalDetail())
      .on("POST", "/v1/meals", json(201, { id: "c1" }));
    const onLogged = vi.fn();
    renderIntl(
      <AddFoodPanel
        date="2026-11-07"
        today="2026-11-07"
        slotId={SLOT}
        onClose={vi.fn()}
        onLogged={onLogged}
      />,
    );
    await userEvent.click(
      await screen.findByRole("tab", { name: en.search.title }),
    );
    await type("dal");
    await userEvent.click(await screen.findByTestId("food-hit"));
    // Picking a hit logs nothing and tracks nothing yet.
    await screen.findByTestId("portion-picker");
    expect(track).not.toHaveBeenCalled();
    expect(api.callsTo("POST", "/v1/meals")).toHaveLength(0);
    await userEvent.click(
      screen.getByRole("button", { name: en.foods.portion.save }),
    );
    await waitFor(() => expect(onLogged).toHaveBeenCalled());
    expect(track.mock.calls).toEqual([
      ["diary_entry_added", { method: "search" }],
    ]);
    expect(api.callsTo("POST", "/v1/meals")[0].body).toMatchObject({
      food_id: DAL_ID,
      quantity: 1,
      unit: "katori",
      meal_slot_id: SLOT,
    });
  });
});
