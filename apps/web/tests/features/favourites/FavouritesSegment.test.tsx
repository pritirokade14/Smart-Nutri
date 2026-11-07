import { cleanup, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { FavouritesSegment } from "@/features/favourites/components/FavouritesSegment";
import { MESSAGES } from "../../support/analyze-fixtures";
import { apiStub, envelope, json } from "../../support/api-stub";
import { digitsOutsideAllowed, renderIntl } from "../../support/diary-render";

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
const base = {
  member_id: "m",
  created_at: "2026-11-06T07:00:00Z",
  barcode: null,
  product_id: null,
  food_id: null,
  custom_food_id: null,
  recipe_id: null,
  source_kind: null,
  default_quantity: null,
  default_unit: null,
  items: null,
  attributions: [],
};
const ROTI = {
  ...base,
  id: "f1",
  kind: "food",
  source_kind: "food",
  food_id: "f0000000-0000-4000-8000-000000000002",
  name: "Roti",
  default_quantity: 2,
  default_unit: "roti",
  item_count: 1,
  attributions: ["attribution.usda_fdc"],
};
const MEAL = {
  ...base,
  id: "f2",
  kind: "meal",
  name: "मेरा नाश्ता",
  item_count: 3,
};
const SLOT = "d0000000-0000-4000-8000-000000000001";

function stub(items: object[]) {
  return apiStub(fetchMock)
    .on("GET", "/v1/favourites", { items })
    .on("POST", "/v1/meals", (_c) => json(201, { id: "c1" }));
}
function open() {
  const onLogged = vi.fn();
  renderIntl(
    <FavouritesSegment
      slotId={SLOT}
      localDate="2026-11-05"
      onLogged={onLogged}
    />,
  );
  return onLogged;
}

beforeEach(() => {
  fetchMock.mockReset();
  track.mockReset();
});
afterEach(cleanup);

describe("FavouritesSegment", () => {
  it("food favourite tap logs the default portion with method favourite", async () => {
    const api = stub([ROTI]);
    const onLogged = open();
    await userEvent.click(await screen.findByTestId("favourite-food"));
    await waitFor(() => expect(onLogged).toHaveBeenCalled());
    const [call] = api.callsTo("POST", "/v1/meals");
    expect(call.body).toMatchObject({
      food_id: ROTI.food_id,
      quantity: 2,
      unit: "roti",
      meal_slot_id: SLOT,
      local_date: "2026-11-05",
    });
    expect(track.mock.calls).toEqual([
      ["diary_entry_added", { method: "favourite" }],
    ]);
    expect(screen.getByTestId("source-credit")).toBeTruthy();
  });

  it("meal favourite log again sends client_id and reports a count only", async () => {
    const api = stub([MEAL]).on("POST", "/v1/favourites/f2/log", (_c) =>
      json(201, { created: [{ id: "a" }, { id: "b" }, { id: "c" }] }),
    );
    const onLogged = open();
    expect(await screen.findByText("मेरा नाश्ता")).toBeTruthy();
    await userEvent.click(
      screen.getByRole("button", { name: en.favourites.log_again }),
    );
    await waitFor(() => expect(onLogged).toHaveBeenCalledWith(3));
    const [call] = api.callsTo("POST", "/v1/favourites/f2/log");
    expect(call.body).toMatchObject({
      meal_slot_id: SLOT,
      local_date: "2026-11-05",
    });
    expect((call.body as { client_id: string }).client_id).toMatch(
      /[0-9a-f-]{36}/,
    );
    // The name never reaches analytics.
    expect(JSON.stringify(track.mock.calls)).not.toContain("मेरा");
  });

  it("shows no numbers on a row except the item count", async () => {
    stub([MEAL, { ...ROTI, default_quantity: null, default_unit: null }]);
    open();
    await screen.findByText("मेरा नाश्ता");
    expect(digitsOutsideAllowed()).toEqual([]);
  });

  it("retry reuses the client_id", async () => {
    let n = 0;
    const api = stub([MEAL]).on("POST", "/v1/favourites/f2/log", (_c) => {
      n += 1;
      return n === 1
        ? json(503, envelope("internal_error"))
        : json(200, { created: [{ id: "a" }] });
    });
    const onLogged = open();
    const btn = await screen.findByRole("button", {
      name: en.favourites.log_again,
    });
    await userEvent.click(btn);
    await screen.findByRole("alert");
    await userEvent.click(btn);
    await waitFor(() => expect(onLogged).toHaveBeenCalledWith(1));
    const ids = api
      .callsTo("POST", "/v1/favourites/f2/log")
      .map((c) => (c.body as { client_id: string }).client_id);
    expect(ids).toHaveLength(2);
    expect(ids[0]).toBe(ids[1]);
  });

  it("food favourites key client_id by favourite and regenerate after success", async () => {
    let n = 0;
    const DAL = {
      ...ROTI,
      id: "f3",
      name: "Dal",
      food_id: "f0000000-0000-4000-8000-000000000003",
    };
    const api = stub([ROTI, DAL]).on("POST", "/v1/meals", (_c) => {
      n += 1;
      return n === 1
        ? json(503, envelope("internal_error"))
        : json(201, { id: `c${n}` });
    });
    const onLogged = open();
    const rows = await screen.findAllByTestId("favourite-food");
    await userEvent.click(rows[0]);
    await screen.findByRole("alert");
    await userEvent.click(rows[1]);
    await waitFor(() => expect(onLogged).toHaveBeenCalledTimes(1));
    await userEvent.click(rows[1]);
    await waitFor(() => expect(onLogged).toHaveBeenCalledTimes(2));
    const ids = api
      .callsTo("POST", "/v1/meals")
      .map((c) => (c.body as { client_id: string }).client_id);
    expect(ids).toHaveLength(3);
    expect(ids[0]).not.toBe(ids[1]);
    expect(ids[2]).not.toBe(ids[1]);
  });

  it("food_retired shows its message", async () => {
    stub([MEAL]).on(
      "POST",
      "/v1/favourites/f2/log",
      json(422, envelope("food_retired")),
    );
    open();
    await userEvent.click(
      await screen.findByRole("button", { name: en.favourites.log_again }),
    );
    expect((await screen.findByRole("alert")).textContent).toBe(
      en.error.food_retired,
    );
  });

  it("empty state", async () => {
    stub([]);
    open();
    expect((await screen.findByTestId("favourites-empty")).textContent).toBe(
      en.favourites.empty,
    );
  });
});
