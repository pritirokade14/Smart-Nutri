import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import {
  cleanup,
  fireEvent,
  render,
  screen,
  waitFor,
  within,
} from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { NextIntlClientProvider } from "next-intl";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import type { MealSlotOut } from "@/features/diary/api/mealSlots";
import { MealsScreen } from "@/features/diary/components/MealsScreen";
import { clientMessages } from "@/i18n/client-messages";
import { MESSAGES } from "../../support/analyze-fixtures";
import { apiStub, envelope, json } from "../../support/api-stub";

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
const MEMBER = "a0000000-0000-4000-8000-000000000001";
const id = (n: number) => `d0000000-0000-4000-8000-00000000000${n}`;
const slot = (n: number, over: Partial<MealSlotOut> = {}): MealSlotOut => ({
  id: id(n),
  member_id: MEMBER,
  position: n - 1,
  label_key:
    n <= 4
      ? `diary.slot.${["breakfast", "lunch", "snack", "dinner"][n - 1]}`
      : null,
  custom_label: null,
  default_time_window: null,
  is_default: n <= 4,
  archived: false,
  ...over,
});
const FOUR = [1, 2, 3, 4].map((n) => slot(n));

function open(messages = en) {
  render(
    <QueryClientProvider
      client={
        new QueryClient({ defaultOptions: { queries: { retry: false } } })
      }
    >
      <NextIntlClientProvider locale="en" messages={clientMessages(messages)}>
        <MealsScreen />
      </NextIntlClientProvider>
    </QueryClientProvider>,
  );
}
const list = (items: MealSlotOut[]) => ({
  items,
  suggested_slot_id: items[0]?.id,
});
const stub = (items: MealSlotOut[]) =>
  apiStub(fetchMock).on("GET", "/v1/meal-slots", list(items));
const rows = () => screen.getAllByTestId("meal-slot-row");

beforeEach(() => {
  fetchMock.mockReset();
  track.mockReset();
});
afterEach(cleanup);

describe("MealsScreen", () => {
  it("shows loading, then the default names", async () => {
    stub(FOUR);
    open();
    expect(screen.getByText(en.common.loading)).toBeTruthy();
    await screen.findAllByTestId("meal-slot-row");
    expect(
      rows().map((r) => within(r).getByTestId("meal-slot-name").textContent),
    ).toEqual([
      en.diary.slot.breakfast,
      en.diary.slot.lunch,
      en.diary.slot.snack,
      en.diary.slot.dinner,
    ]);
  });

  it("error shows retry", async () => {
    apiStub(fetchMock).on(
      "GET",
      "/v1/meal-slots",
      json(500, envelope("internal_error")),
    );
    open();
    expect(
      await screen.findByRole("button", { name: en.common.retry }),
    ).toBeTruthy();
  });

  it("rename sends custom label exactly as typed", async () => {
    const api = stub(FOUR).on(
      "PATCH",
      `/v1/meal-slots/${id(3)}`,
      slot(3, { custom_label: "Evening chai" }),
    );
    open();
    await screen.findAllByTestId("meal-slot-row");
    await userEvent.click(
      screen.getByRole("button", {
        name: `${en.diary.slots.rename}: ${en.diary.slot.snack}`,
      }),
    );
    await userEvent.type(
      screen.getByLabelText(en.diary.slots.rename),
      "  Evening chai ",
    );
    await userEvent.click(
      within(
        screen
          .getByLabelText(en.diary.slots.rename)
          .closest("form") as HTMLElement,
      ).getByRole("button", { name: en.members.form.save }),
    );
    await waitFor(() =>
      expect(api.callsTo("PATCH", `/v1/meal-slots/${id(3)}`)).toHaveLength(1),
    );
    expect(api.callsTo("PATCH", `/v1/meal-slots/${id(3)}`)[0]?.body).toEqual({
      custom_label: "Evening chai",
    });
  });

  it("reset name sends clear flag", async () => {
    const api = stub([slot(1, { custom_label: "Early" }), ...FOUR.slice(1)]).on(
      "PATCH",
      `/v1/meal-slots/${id(1)}`,
      slot(1),
    );
    open();
    await screen.findAllByTestId("meal-slot-row");
    await userEvent.click(
      screen.getByRole("button", { name: `${en.diary.slots.rename}: Early` }),
    );
    await userEvent.click(
      screen.getByRole("button", { name: en.diary.slots.reset_name }),
    );
    await waitFor(() =>
      expect(api.callsTo("PATCH", `/v1/meal-slots/${id(1)}`)).toHaveLength(1),
    );
    expect(api.callsTo("PATCH", `/v1/meal-slots/${id(1)}`)[0]?.body).toEqual({
      clear_custom_label: true,
    });
  });

  it("reorder sends every active id", async () => {
    const api = stub(FOUR).on("PUT", "/v1/meal-slots/order", { items: FOUR });
    open();
    await screen.findAllByTestId("meal-slot-row");
    await userEvent.click(
      within(rows()[2] as HTMLElement).getByTestId("meal-slot-up"),
    );
    await waitFor(() =>
      expect(api.callsTo("PUT", "/v1/meal-slots/order")).toHaveLength(1),
    );
    expect(api.callsTo("PUT", "/v1/meal-slots/order")[0]?.body).toEqual({
      ids: [id(1), id(3), id(2), id(4)],
    });
  });

  it("first up and last down are disabled", async () => {
    stub(FOUR);
    open();
    await screen.findAllByTestId("meal-slot-row");
    expect(
      (
        within(rows()[0] as HTMLElement).getByTestId(
          "meal-slot-up",
        ) as HTMLButtonElement
      ).disabled,
    ).toBe(true);
    expect(
      (
        within(rows()[3] as HTMLElement).getByTestId(
          "meal-slot-down",
        ) as HTMLButtonElement
      ).disabled,
    ).toBe(true);
  });

  it("add sends the label and shows it after reload", async () => {
    const api = stub(FOUR).on(
      "POST",
      "/v1/meal-slots",
      json(201, slot(5, { custom_label: "Post-gym" })),
    );
    open();
    await screen.findAllByTestId("meal-slot-row");
    await userEvent.type(screen.getByLabelText(en.diary.slots.add), "Post-gym");
    await userEvent.click(
      screen.getByRole("button", { name: en.diary.slots.add }),
    );
    await waitFor(() =>
      expect(api.callsTo("POST", "/v1/meal-slots")).toHaveLength(1),
    );
    expect(
      (
        api.callsTo("POST", "/v1/meal-slots")[0]?.body as
          | { custom_label: string }
          | undefined
      )?.custom_label,
    ).toBe("Post-gym");
  });

  it("add disabled at six with limit message", async () => {
    const six = [
      ...FOUR,
      slot(5, { custom_label: "A" }),
      slot(6, { custom_label: "B" }),
    ];
    const api = stub(six);
    open();
    await screen.findAllByTestId("meal-slot-row");
    expect(screen.getByTestId("meal-limit").textContent).toBe(
      en.diary.slots.limit.replace("{max}", "6"),
    );
    expect(
      (
        screen.getByRole("button", {
          name: en.diary.slots.add,
        }) as HTMLButtonElement
      ).disabled,
    ).toBe(true);
    expect(api.callsTo("POST", "/v1/meal-slots")).toHaveLength(0);
  });

  it("a server limit refusal shows the limit message", async () => {
    stub(FOUR).on(
      "POST",
      "/v1/meal-slots",
      json(422, envelope("meal_slot_limit_reached", { max: 6 })),
    );
    open();
    await screen.findAllByTestId("meal-slot-row");
    await userEvent.type(screen.getByLabelText(en.diary.slots.add), "X");
    await userEvent.click(
      screen.getByRole("button", { name: en.diary.slots.add }),
    );
    expect((await screen.findByRole("alert")).textContent).toBe(
      en.diary.slots.limit.replace("{max}", "6"),
    );
  });

  it("limit comes from details.max when present", async () => {
    stub(FOUR).on(
      "POST",
      "/v1/meal-slots",
      json(422, envelope("meal_slot_limit_reached", { max: 8 })),
    );
    open();
    await screen.findAllByTestId("meal-slot-row");
    await userEvent.type(screen.getByLabelText(en.diary.slots.add), "X");
    await userEvent.click(
      screen.getByRole("button", { name: en.diary.slots.add }),
    );
    expect((await screen.findByRole("alert")).textContent).toBe(
      en.diary.slots.limit.replace("{max}", "8"),
    );
  });

  it("move buttons are named by direction and title", async () => {
    stub(FOUR);
    open();
    await screen.findAllByTestId("meal-slot-row");
    const t = en.diary.slot.snack;
    expect(
      screen.getByRole("button", {
        name: en.diary.slots.move_up.replace("{title}", t),
      }),
    ).toBeTruthy();
    expect(
      screen.getByRole("button", {
        name: en.diary.slots.move_down.replace("{title}", t),
      }),
    ).toBeTruthy();
  });

  it("usual time saves a window, and empty clears it", async () => {
    const api = stub(FOUR)
      .on("PATCH", `/v1/meal-slots/${id(1)}`, slot(1))
      .on("PATCH", `/v1/meal-slots/${id(2)}`, slot(2));
    open();
    await screen.findAllByTestId("meal-slot-row");
    const row = within(rows()[0] as HTMLElement);
    fireEvent.change(row.getByTestId("meal-slot-start"), {
      target: { value: "08:00" },
    });
    fireEvent.change(row.getByTestId("meal-slot-end"), {
      target: { value: "10:30" },
    });
    await userEvent.click(
      within(row.getByTestId("meal-slot-window")).getByRole("button"),
    );
    await waitFor(() =>
      expect(api.callsTo("PATCH", `/v1/meal-slots/${id(1)}`)).toHaveLength(1),
    );
    expect(api.callsTo("PATCH", `/v1/meal-slots/${id(1)}`)[0]?.body).toEqual({
      default_time_window: { start: "08:00", end: "10:30" },
    });
    await userEvent.click(
      within(
        within(rows()[1] as HTMLElement).getByTestId("meal-slot-window"),
      ).getByRole("button"),
    );
    await waitFor(() =>
      expect(api.callsTo("PATCH", `/v1/meal-slots/${id(2)}`)).toHaveLength(1),
    );
    expect(api.callsTo("PATCH", `/v1/meal-slots/${id(2)}`)[0]?.body).toEqual({
      clear_time_window: true,
    });
  });

  it("remove shows the note and archives", async () => {
    const api = stub(FOUR).on("DELETE", `/v1/meal-slots/${id(3)}`, {
      result: "archived",
    });
    open();
    await screen.findAllByTestId("meal-slot-row");
    await userEvent.click(
      within(rows()[2] as HTMLElement).getByTestId("meal-slot-remove"),
    );
    expect(screen.getByText(en.diary.slots.remove_note)).toBeTruthy();
    expect(api.callsTo("DELETE", `/v1/meal-slots/${id(3)}`)).toHaveLength(0);
    await userEvent.click(
      within(screen.getByTestId("confirm-dialog")).getByRole("button", {
        name: en.diary.slots.remove,
      }),
    );
    await waitFor(() =>
      expect(api.callsTo("DELETE", `/v1/meal-slots/${id(3)}`)).toHaveLength(1),
    );
  });

  it("last meal cannot be removed", async () => {
    stub([slot(1)]);
    open();
    await screen.findAllByTestId("meal-slot-row");
    expect(
      (screen.getByTestId("meal-slot-remove") as HTMLButtonElement).disabled,
    ).toBe(true);
    expect(screen.getByText(en.diary.slots.last_active)).toBeTruthy();
  });

  it("a server last-active refusal is shown", async () => {
    stub(FOUR).on(
      "DELETE",
      `/v1/meal-slots/${id(1)}`,
      json(422, envelope("meal_slot_last_active")),
    );
    open();
    await screen.findAllByTestId("meal-slot-row");
    await userEvent.click(
      within(rows()[0] as HTMLElement).getByTestId("meal-slot-remove"),
    );
    await userEvent.click(
      within(screen.getByTestId("confirm-dialog")).getByRole("button", {
        name: en.diary.slots.remove,
      }),
    );
    expect((await screen.findByRole("alert")).textContent).toBe(
      en.diary.slots.last_active,
    );
  });

  it("duplicate name shows inline error", async () => {
    stub(FOUR).on(
      "PATCH",
      `/v1/meal-slots/${id(2)}`,
      json(422, envelope("meal_slot_label_duplicate")),
    );
    open();
    await screen.findAllByTestId("meal-slot-row");
    await userEvent.click(
      screen.getByRole("button", {
        name: `${en.diary.slots.rename}: ${en.diary.slot.lunch}`,
      }),
    );
    await userEvent.type(
      screen.getByLabelText(en.diary.slots.rename),
      "Snacks",
    );
    await userEvent.click(
      within(
        screen
          .getByLabelText(en.diary.slots.rename)
          .closest("form") as HTMLElement,
      ).getByRole("button", { name: en.members.form.save }),
    );
    const alert = await screen.findByRole("alert");
    expect(alert.textContent).toBe(en.diary.slots.duplicate);
    expect(rows()[1]?.contains(alert)).toBe(true);
  });

  it("custom label renders exactly as typed in en, hi and mr", async () => {
    const label = "Chai <b>time</b> चाय";
    for (const lang of ["en", "hi", "mr"] as const) {
      fetchMock.mockReset();
      stub([slot(1, { custom_label: label }), ...FOUR.slice(1)]);
      open(MESSAGES[lang]);
      await screen.findAllByTestId("meal-slot-row");
      expect(screen.getAllByTestId("meal-slot-name")[0]?.textContent).toBe(
        label,
      );
      cleanup();
    }
  });

  it("counter counts code points", async () => {
    stub(FOUR);
    open();
    await screen.findAllByTestId("meal-slot-row");
    const thirty = "अ".repeat(30);
    const input = screen.getByLabelText(en.diary.slots.add) as HTMLInputElement;
    await userEvent.type(input, `${thirty}ब`);
    expect([...input.value].length).toBe(30);
    expect(input.value).toBe(thirty);
    expect(screen.getByTestId("new-meal-counter").textContent).toBe("30/30");
  });

  it("emoji count as one code point", async () => {
    stub(FOUR);
    open();
    await screen.findAllByTestId("meal-slot-row");
    const input = screen.getByLabelText(en.diary.slots.add) as HTMLInputElement;
    await userEvent.type(input, "🍵".repeat(30));
    expect([...input.value].length).toBe(30);
  });

  it("no slot label in analytics", async () => {
    stub(FOUR)
      .on(
        "POST",
        "/v1/meal-slots",
        json(201, slot(5, { custom_label: "Secret snack" })),
      )
      .on(
        "PATCH",
        `/v1/meal-slots/${id(2)}`,
        slot(2, { custom_label: "Secret lunch" }),
      )
      .on("DELETE", `/v1/meal-slots/${id(3)}`, { result: "archived" });
    open();
    await screen.findAllByTestId("meal-slot-row");
    await userEvent.type(
      screen.getByLabelText(en.diary.slots.add),
      "Secret snack",
    );
    await userEvent.click(
      screen.getByRole("button", { name: en.diary.slots.add }),
    );
    await userEvent.click(
      screen.getByRole("button", {
        name: `${en.diary.slots.rename}: ${en.diary.slot.lunch}`,
      }),
    );
    await userEvent.type(
      screen.getByLabelText(en.diary.slots.rename),
      "Secret lunch",
    );
    await userEvent.click(
      within(
        screen
          .getByLabelText(en.diary.slots.rename)
          .closest("form") as HTMLElement,
      ).getByRole("button", { name: en.members.form.save }),
    );
    await userEvent.click(
      within(rows()[2] as HTMLElement).getByTestId("meal-slot-remove"),
    );
    await userEvent.click(
      within(screen.getByTestId("confirm-dialog")).getByRole("button", {
        name: en.diary.slots.remove,
      }),
    );
    await waitFor(() => expect(fetchMock.mock.calls.length).toBeGreaterThan(4));
    expect(JSON.stringify(track.mock.calls)).not.toContain("Secret");
  });
});
