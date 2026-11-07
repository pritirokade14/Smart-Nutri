import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { cleanup, render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { NextIntlClientProvider } from "next-intl";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import type { MealOut } from "@/features/diary/api/diary";
import type { MealSlotOut } from "@/features/diary/api/mealSlots";
import { EditEntryDialog } from "@/features/diary/components/EditEntryDialog";
import { SlotSection } from "@/features/diary/components/SlotSection";
import { clientMessages } from "@/i18n/client-messages";
import { MESSAGES } from "../../support/analyze-fixtures";
import { apiStub } from "../../support/api-stub";
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
vi.mock("@/lib/analytics", () => ({ track: vi.fn() }));

const en = MESSAGES.en;
const day = diaryDay("day_complete_under");
const ENTRY = day.slots.flatMap((s) => s.entries)[0] as MealOut;
const SLOTS = day.slots.map(
  (s, i) =>
    ({
      id: s.slot_id,
      member_id: day.member_id,
      position: i,
      label_key: s.label_key,
      custom_label: s.custom_label,
      default_time_window: null,
      is_default: true,
      archived: false,
    }) as MealSlotOut,
);

const wrap = (ui: React.ReactNode) => (
  <QueryClientProvider client={new QueryClient()}>
    <NextIntlClientProvider locale="en" messages={clientMessages(en)}>
      {ui}
    </NextIntlClientProvider>
  </QueryClientProvider>
);

beforeEach(() => {
  fetchMock.mockReset();
});
afterEach(cleanup);

describe("moving an entry", () => {
  it("move sends only meal_slot_id", async () => {
    const other = SLOTS.find((s) => s.id !== ENTRY.meal_slot_id) as MealSlotOut;
    const api = apiStub(fetchMock).on("PATCH", `/v1/meals/${ENTRY.id}`, {
      ...ENTRY,
      meal_slot_id: other.id,
    });
    render(
      wrap(<EditEntryDialog entry={ENTRY} slots={SLOTS} onClose={vi.fn()} />),
    );
    await userEvent.selectOptions(
      screen.getByLabelText(en.diary.move),
      other.id,
    );
    await userEvent.click(
      screen.getByRole("button", { name: en.meals.log.save }),
    );
    await waitFor(() =>
      expect(api.callsTo("PATCH", `/v1/meals/${ENTRY.id}`)).toHaveLength(1),
    );
    expect(api.callsTo("PATCH", `/v1/meals/${ENTRY.id}`)[0]?.body).toEqual({
      meal_slot_id: other.id,
    });
  });

  it("removed slot shows badge and move", async () => {
    const removed = {
      ...(day.slots[0] as (typeof day.slots)[number]),
      archived: true,
    };
    const entry = removed.entries[0] as MealOut;
    const active = SLOTS.filter((s) => s.id !== removed.slot_id);
    const onEdit = vi.fn();
    render(wrap(<SlotSection slot={removed} onEdit={onEdit} />));
    expect(screen.getByTestId("slot-removed").textContent).toBe(
      en.diary.slots.removed,
    );
    cleanup();
    render(
      wrap(<EditEntryDialog entry={entry} slots={active} onClose={vi.fn()} />),
    );
    const select = screen.getByLabelText(en.diary.move) as HTMLSelectElement;
    expect(select.value).toBe(removed.slot_id);
    expect(select.selectedOptions[0]?.textContent).toBe(en.diary.slots.removed);
    expect(select.options.length).toBe(active.length + 1);
  });
});
