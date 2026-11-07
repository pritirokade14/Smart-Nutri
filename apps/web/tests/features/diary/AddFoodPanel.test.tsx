import { cleanup, screen, waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { AddFoodPanel } from "@/features/diary/components/AddFoodPanel";
import { MESSAGES } from "../../support/analyze-fixtures";
import { apiStub, envelope, json } from "../../support/api-stub";
import { renderIntl } from "../../support/diary-render";

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
const SLOTS = ["breakfast", "lunch", "snack", "dinner"].map((k, i) => ({
  id: `d0000000-0000-4000-8000-00000000000${i + 1}`,
  member_id: "m",
  position: i,
  label_key: `diary.slot.${k}`,
  custom_label: null,
  default_time_window: null,
  is_default: true,
  archived: false,
}));
const LUNCH = SLOTS[1].id;
const RECENT = {
  source_kind: "product",
  product_id: "0eb5b5a8-5b74-5f9d-83a8-ec3fa0508011",
  barcode: null,
  name: "Dal rice plate",
  grade: null,
  grams: 350,
  meal_slot_id: LUNCH,
  last_eaten_at: "2026-11-06T07:45:00Z",
  attribution: null,
};
const MEAL = { id: "c1" };

function stub(slotsOk = true) {
  return apiStub(fetchMock)
    .on(
      "GET",
      "/v1/meal-slots",
      slotsOk
        ? { items: SLOTS, suggested_slot_id: SLOTS[0].id }
        : json(404, envelope("not_found")),
    )
    .on("GET", "/v1/diary/recents", { items: [RECENT] })
    .on("POST", "/v1/meals", (_c) => json(201, MEAL));
}

function open(over: { date?: string; slotId?: string } = {}) {
  const onLogged = vi.fn();
  renderIntl(
    <AddFoodPanel
      date={over.date ?? "2026-11-07"}
      today="2026-11-07"
      slotId={over.slotId}
      onClose={vi.fn()}
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

describe("AddFoodPanel", () => {
  it("recent tap logs the last grams into the slot", async () => {
    const api = stub();
    const onLogged = open({ slotId: LUNCH });
    await userEvent.click(await screen.findByTestId("recent-item"));
    await waitFor(() => expect(onLogged).toHaveBeenCalled());
    const sent = api.callsTo("POST", "/v1/meals")[0].body as Record<
      string,
      unknown
    >;
    expect(sent).toMatchObject({
      product_id: RECENT.product_id,
      grams: 350,
      meal_slot_id: LUNCH,
    });
    // Today: no local_date and no eaten_at (the server's clock decides).
    expect(sent).not.toHaveProperty("local_date");
    expect(sent).not.toHaveProperty("eaten_at");
    expect(typeof sent.client_id).toBe("string");
    // The recents were asked for the same slot.
    expect(
      api.callsTo("GET", "/v1/diary/recents").at(-1)?.query.get("slot_id"),
    ).toBe(LUNCH);
  });

  it("past day sends local_date not eaten_at", async () => {
    const api = stub();
    open({ date: "2026-11-05", slotId: LUNCH });
    await userEvent.click(await screen.findByTestId("recent-item"));
    await waitFor(() =>
      expect(api.callsTo("POST", "/v1/meals")).toHaveLength(1),
    );
    const sent = api.callsTo("POST", "/v1/meals")[0].body as Record<
      string,
      unknown
    >;
    expect(sent.local_date).toBe("2026-11-05");
    expect(sent).not.toHaveProperty("eaten_at");
  });

  it("slot chips preselect the tapped slot", async () => {
    stub();
    open({ slotId: LUNCH });
    const chips = await screen.findByTestId("slot-chips");
    expect(
      within(chips)
        .getByRole("button", { name: en.diary.slot.lunch })
        .getAttribute("aria-pressed"),
    ).toBe("true");
    expect(
      within(chips)
        .getByRole("button", { name: en.diary.slot.breakfast })
        .getAttribute("aria-pressed"),
    ).toBe("false");
  });

  it("without a tapped slot the server's suggestion is preselected", async () => {
    stub();
    open();
    const chips = await screen.findByTestId("slot-chips");
    expect(
      within(chips)
        .getByRole("button", { name: en.diary.slot.breakfast })
        .getAttribute("aria-pressed"),
    ).toBe("true");
  });

  it("picking another chip logs into it", async () => {
    const api = stub();
    open({ slotId: LUNCH });
    const chips = await screen.findByTestId("slot-chips");
    await userEvent.click(
      within(chips).getByRole("button", { name: en.diary.slot.dinner }),
    );
    await userEvent.click(await screen.findByTestId("recent-item"));
    await waitFor(() =>
      expect(api.callsTo("POST", "/v1/meals")).toHaveLength(1),
    );
    expect(
      (api.callsTo("POST", "/v1/meals")[0].body as { meal_slot_id: string })
        .meal_slot_id,
    ).toBe(SLOTS[3].id);
  });

  it("no slot list hides chips and sends no slot", async () => {
    const api = stub(false);
    open();
    await userEvent.click(await screen.findByTestId("recent-item"));
    await waitFor(() =>
      expect(api.callsTo("POST", "/v1/meals")).toHaveLength(1),
    );
    expect(screen.queryByTestId("slot-chips")).toBeNull();
    expect(api.callsTo("POST", "/v1/meals")[0].body).not.toHaveProperty(
      "meal_slot_id",
    );
  });

  it("logged entry sends diary_entry_added with method only", async () => {
    stub();
    open({ slotId: LUNCH });
    await userEvent.click(await screen.findByTestId("recent-item"));
    await waitFor(() => expect(track).toHaveBeenCalled());
    expect(track.mock.calls).toEqual([
      ["diary_entry_added", { method: "recent" }],
    ]);
  });

  it("offline log shows the online-only note and keeps the panel", async () => {
    stub();
    open({ slotId: LUNCH });
    const item = await screen.findByTestId("recent-item");
    fetchMock.mockRejectedValue(new TypeError("offline"));
    await userEvent.click(item);
    const alert = await screen.findByRole("alert");
    expect(alert.textContent).toBe(en.meals.online_only);
    expect(screen.getByTestId("add-food-panel")).toBeTruthy();
    expect(track).not.toHaveBeenCalled();
  });

  it("search is a segment; scan and label stay linked", async () => {
    stub();
    open();
    const links = await screen.findByTestId("add-food-links");
    const hrefs = within(links)
      .getAllByRole("link")
      .map((a) => a.getAttribute("href"));
    expect(hrefs).toEqual(["/en/scan", "/en/scan/label"]);
    expect(screen.getByRole("tab", { name: en.search.title })).toBeTruthy();
  });
});
