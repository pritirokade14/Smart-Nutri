import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { cleanup, render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { NextIntlClientProvider } from "next-intl";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import type { MealOut } from "@/features/diary/api/diary";
import { EditEntryDialog } from "@/features/diary/components/EditEntryDialog";
import { clientMessages } from "@/i18n/client-messages";
import { MESSAGES } from "../../support/analyze-fixtures";
import { apiStub, envelope, json } from "../../support/api-stub";
import { diaryDay } from "../../support/diary-fixtures";

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
const entries = diaryDay("day_complete_under").slots.flatMap((s) => s.entries);
const OATS = entries[0] as MealOut;
const QUICK = diaryDay("day_quick_add_kcal_only").slots.flatMap(
  (s) => s.entries,
)[0] as MealOut;

function open(entry: MealOut, onClose = vi.fn()) {
  render(
    <QueryClientProvider
      client={
        new QueryClient({ defaultOptions: { queries: { retry: false } } })
      }
    >
      <NextIntlClientProvider locale="en" messages={clientMessages(en)}>
        <EditEntryDialog entry={entry} onClose={onClose} />
      </NextIntlClientProvider>
    </QueryClientProvider>,
  );
  return onClose;
}

beforeEach(() => {
  fetchMock.mockReset();
  track.mockReset();
});
afterEach(cleanup);

describe("EditEntryDialog", () => {
  it("edit grams sends only grams", async () => {
    const api = apiStub(fetchMock).on("PATCH", `/v1/meals/${OATS.id}`, {
      ...OATS,
      grams: 80,
    });
    const onClose = open(OATS);
    const input = screen.getByLabelText(en.meals.log.amount_grams);
    await userEvent.clear(input);
    await userEvent.type(input, "80");
    await userEvent.click(
      screen.getByRole("button", { name: en.meals.log.save }),
    );
    await waitFor(() => expect(onClose).toHaveBeenCalled());
    const sent = api.callsTo("PATCH", `/v1/meals/${OATS.id}`)[0].body as Record<
      string,
      unknown
    >;
    expect(sent).toEqual({ grams: 80 });
  });

  it("unchanged grams send nothing", async () => {
    const api = apiStub(fetchMock);
    const onClose = open(OATS);
    await userEvent.click(
      screen.getByRole("button", { name: en.meals.log.save }),
    );
    expect(onClose).toHaveBeenCalled();
    expect(api.calls).toHaveLength(0);
  });

  it("an invalid amount is refused before any request", async () => {
    const api = apiStub(fetchMock);
    open(OATS);
    const input = screen.getByLabelText(en.meals.log.amount_grams);
    await userEvent.clear(input);
    await userEvent.type(input, "0");
    await userEvent.click(
      screen.getByRole("button", { name: en.meals.log.save }),
    );
    expect(api.calls).toHaveLength(0);
    expect(input.getAttribute("aria-invalid")).toBe("true");
  });

  it("remove asks, then deletes", async () => {
    const api = apiStub(fetchMock).on(
      "DELETE",
      `/v1/meals/${OATS.id}`,
      new Response(null, { status: 204 }),
    );
    const onClose = open(OATS);
    await userEvent.click(
      screen.getByRole("button", { name: en.diary.delete }),
    );
    expect(screen.getByText(en.diary.delete_confirm)).toBeTruthy();
    expect(api.calls).toHaveLength(0);
    const confirm = screen.getByTestId("confirm-dialog");
    await userEvent.click(
      confirm.querySelector("button:last-of-type") as HTMLElement,
    );
    await waitFor(() => expect(onClose).toHaveBeenCalled());
    expect(api.callsTo("DELETE", `/v1/meals/${OATS.id}`)).toHaveLength(1);
    expect(track).toHaveBeenCalledWith("meal_removed");
  });

  it("cancelling the confirmation deletes nothing", async () => {
    const api = apiStub(fetchMock);
    open(OATS);
    await userEvent.click(
      screen.getByRole("button", { name: en.diary.delete }),
    );
    const confirm = screen.getByTestId("confirm-dialog");
    await userEvent.click(
      confirm.querySelector("button:first-of-type") as HTMLElement,
    );
    expect(screen.queryByTestId("confirm-dialog")).toBeNull();
    expect(api.calls).toHaveLength(0);
  });

  it("offline edit shows the online-only message", async () => {
    fetchMock.mockRejectedValue(new TypeError("offline"));
    const onClose = open(OATS);
    const input = screen.getByLabelText(en.meals.log.amount_grams);
    await userEvent.clear(input);
    await userEvent.type(input, "90");
    await userEvent.click(
      screen.getByRole("button", { name: en.meals.log.save }),
    );
    const alert = await screen.findByRole("alert");
    expect(alert.textContent).toBe(en.meals.online_only);
    expect(onClose).not.toHaveBeenCalled();
  });

  it("an API error shows its localised message", async () => {
    apiStub(fetchMock).on(
      "PATCH",
      `/v1/meals/${OATS.id}`,
      json(422, envelope("eaten_at_out_of_range")),
    );
    open(OATS);
    const input = screen.getByLabelText(en.meals.log.amount_grams);
    await userEvent.clear(input);
    await userEvent.type(input, "90");
    await userEvent.click(
      screen.getByRole("button", { name: en.meals.log.save }),
    );
    expect((await screen.findByRole("alert")).textContent).toBe(
      en.error.eaten_at_out_of_range,
    );
  });

  it("a quick add edits its own fields, blanks stay null", async () => {
    const api = apiStub(fetchMock).on("PATCH", `/v1/meals/${QUICK.id}`, QUICK);
    open(QUICK);
    expect(screen.queryByLabelText(en.meals.log.amount_grams)).toBeNull();
    const kcal = screen.getByLabelText(en.diary.quick_add.energy);
    await userEvent.clear(kcal);
    await userEvent.type(kcal, "500");
    await userEvent.click(
      screen.getByRole("button", { name: en.meals.log.save }),
    );
    await waitFor(() =>
      expect(api.callsTo("PATCH", `/v1/meals/${QUICK.id}`)).toHaveLength(1),
    );
    const sent = api.callsTo("PATCH", `/v1/meals/${QUICK.id}`)[0].body as {
      quick: Record<string, unknown>;
    };
    expect(Object.keys(sent)).toEqual(["quick"]);
    expect(sent.quick).toMatchObject({
      energy_kcal: 500,
      protein_g: null,
      fat_g: null,
      carbs_g: null,
      fibre_g: null,
    });
  });

  it("a quick add with hidden numbers cannot be edited blind", () => {
    open({
      ...QUICK,
      nutrients: { ...QUICK.nutrients, energy_kcal: null },
    });
    expect(screen.queryByLabelText(en.diary.quick_add.energy)).toBeNull();
  });
});
