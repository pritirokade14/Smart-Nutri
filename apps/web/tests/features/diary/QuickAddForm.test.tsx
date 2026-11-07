import { cleanup, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { QuickAddForm } from "@/features/diary/components/QuickAddForm";
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

function open(slotId: string | null = "slot-1", localDate?: string) {
  const onLogged = vi.fn();
  renderIntl(
    <QuickAddForm slotId={slotId} localDate={localDate} onLogged={onLogged} />,
  );
  return onLogged;
}
const save = () =>
  userEvent.click(screen.getByRole("button", { name: en.meals.log.save }));
type Body = {
  client_id: string;
  meal_slot_id?: string;
  local_date?: string;
  quick: Record<string, unknown>;
};
const posted = (api: ReturnType<typeof apiStub>) =>
  api.callsTo("POST", "/v1/meals").map((c) => c.body as Body);

beforeEach(() => {
  fetchMock.mockReset();
  track.mockReset();
});
afterEach(cleanup);

describe("QuickAddForm", () => {
  it("kcal only sends nulls for blanks", async () => {
    const api = apiStub(fetchMock).on("POST", "/v1/meals", (_c) =>
      json(201, {}),
    );
    const onLogged = open();
    await userEvent.type(
      screen.getByLabelText(en.diary.quick_add.energy),
      "450",
    );
    await save();
    await waitFor(() => expect(onLogged).toHaveBeenCalled());
    const [body] = posted(api);
    expect(body.quick).toEqual({
      name: null,
      energy_kcal: 450,
      protein_g: null,
      fat_g: null,
      carbs_g: null,
      fibre_g: null,
    });
    expect(body.meal_slot_id).toBe("slot-1");
    expect(body).not.toHaveProperty("local_date");
  });

  it("shows the blank-is-unknown note", () => {
    open();
    expect(screen.getByText(en.foods.blank_is_unknown)).toBeTruthy();
  });

  it("kcal required", async () => {
    const api = apiStub(fetchMock);
    open();
    await userEvent.type(
      screen.getByLabelText(en.diary.quick_add.protein),
      "10",
    );
    await save();
    expect((await screen.findByRole("alert")).textContent).toBe(
      en.error.quick_add_energy_required,
    );
    expect(api.calls).toHaveLength(0);
  });

  it("a blank is never sent as 0 and a typed 0 for protein is kept as 0", async () => {
    const api = apiStub(fetchMock).on("POST", "/v1/meals", (_c) =>
      json(201, {}),
    );
    open();
    await userEvent.type(
      screen.getByLabelText(en.diary.quick_add.energy),
      "100",
    );
    await userEvent.type(
      screen.getByLabelText(en.diary.quick_add.protein),
      "0",
    );
    await save();
    await waitFor(() => expect(posted(api)).toHaveLength(1));
    expect(posted(api)[0].quick.protein_g).toBe(0);
    expect(posted(api)[0].quick.fat_g).toBeNull();
  });

  it("a past day sends local_date", async () => {
    const api = apiStub(fetchMock).on("POST", "/v1/meals", (_c) =>
      json(201, {}),
    );
    open("slot-1", "2026-11-05");
    await userEvent.type(
      screen.getByLabelText(en.diary.quick_add.energy),
      "100",
    );
    await save();
    await waitFor(() => expect(posted(api)).toHaveLength(1));
    expect(posted(api)[0].local_date).toBe("2026-11-05");
    expect(posted(api)[0]).not.toHaveProperty("eaten_at");
  });

  it("no slot list sends no slot", async () => {
    const api = apiStub(fetchMock).on("POST", "/v1/meals", (_c) =>
      json(201, {}),
    );
    open(null);
    await userEvent.type(
      screen.getByLabelText(en.diary.quick_add.energy),
      "100",
    );
    await save();
    await waitFor(() => expect(posted(api)).toHaveLength(1));
    expect(posted(api)[0]).not.toHaveProperty("meal_slot_id");
  });

  it("quick add name never in analytics", async () => {
    apiStub(fetchMock).on("POST", "/v1/meals", (_c) => json(201, {}));
    open();
    await userEvent.type(
      screen.getByLabelText(en.diary.quick_add.name_label),
      "Secret chai ☕",
    );
    await userEvent.type(
      screen.getByLabelText(en.diary.quick_add.energy),
      "120",
    );
    await save();
    await waitFor(() => expect(track).toHaveBeenCalled());
    expect(track.mock.calls).toEqual([
      ["diary_entry_added", { method: "quick_add" }],
    ]);
    expect(JSON.stringify(track.mock.calls)).not.toMatch(/chai|120/);
  });

  it("offline log shows the online-only note and keeps the form", async () => {
    open();
    const kcal = screen.getByLabelText(en.diary.quick_add.energy);
    await userEvent.type(kcal, "450");
    fetchMock.mockRejectedValue(new TypeError("offline"));
    await save();
    expect((await screen.findByRole("alert")).textContent).toBe(
      en.meals.online_only,
    );
    expect((kcal as HTMLInputElement).value).toBe("450");
    expect(track).not.toHaveBeenCalled();
  });

  it("a retry after an error reuses the client_id", async () => {
    const api = apiStub(fetchMock).on("POST", "/v1/meals", (_c, n) =>
      n === 1 ? json(503, envelope("internal_error")) : json(201, {}),
    );
    open();
    await userEvent.type(
      screen.getByLabelText(en.diary.quick_add.energy),
      "450",
    );
    await save();
    await screen.findByRole("alert");
    await save();
    await waitFor(() => expect(posted(api)).toHaveLength(2));
    expect(posted(api)[1].client_id).toBe(posted(api)[0].client_id);
  });

  it("an API error maps to its message", async () => {
    apiStub(fetchMock).on(
      "POST",
      "/v1/meals",
      json(422, envelope("meal_slot_archived")),
    );
    open();
    await userEvent.type(
      screen.getByLabelText(en.diary.quick_add.energy),
      "450",
    );
    await save();
    expect((await screen.findByRole("alert")).textContent).toBe(
      en.error.meal_slot_archived,
    );
  });
});
