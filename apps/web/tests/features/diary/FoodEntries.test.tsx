import { cleanup, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import type { MealOut } from "@/features/diary/api/diary";
import { EditEntryDialog } from "@/features/diary/components/EditEntryDialog";
import { EntryRow } from "@/features/diary/components/EntryRow";
import { MESSAGES } from "../../support/analyze-fixtures";
import { apiStub } from "../../support/api-stub";
import { diaryDay } from "../../support/diary-fixtures";
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
vi.mock("@/lib/analytics", () => ({ track: vi.fn() }));

const en = MESSAGES.en;
const BASE = diaryDay("day_complete_under").slots.flatMap(
  (s) => s.entries,
)[0] as MealOut;
const ROTI: MealOut = {
  ...BASE,
  source_kind: "food",
  quantity: 2,
  unit: "roti",
  grams: 136,
  basis: "g",
  attributions: ["attribution.usda_fdc"],
  portion_units: [
    { code: "g", grams_per_unit: 1 },
    { code: "roti", grams_per_unit: 68 },
  ],
};

beforeEach(() => {
  fetchMock.mockReset();
});
afterEach(cleanup);

describe("food entries", () => {
  it("shows the portion line and the USDA credit", () => {
    renderIntl(<EntryRow entry={ROTI} onEdit={vi.fn()} />);
    expect(screen.getByTestId("entry-portion").textContent).toBe(
      "2 rotis · 136 g",
    );
    expect(screen.getByTestId("source-credit").textContent).toBe(
      en.attribution.usda_fdc,
    );
  });

  it("an ml entry shows ml", () => {
    renderIntl(
      <EntryRow
        entry={{ ...ROTI, unit: "glass", quantity: 1, grams: 250, basis: "ml" }}
        onEdit={vi.fn()}
      />,
    );
    expect(screen.getByTestId("entry-portion").textContent).toBe(
      "1 glass · 250 ml",
    );
  });

  it("an older grams entry keeps the grams line, no credit", () => {
    renderIntl(
      <EntryRow
        entry={{ ...BASE, unit: null, quantity: null, attributions: [] }}
        onEdit={vi.fn()}
      />,
    );
    expect(screen.getByTestId("entry-portion").textContent).toBe(
      en.diary.grams_line.replace("{grams}", String(BASE.grams)),
    );
    expect(screen.queryByTestId("source-credit")).toBeNull();
  });

  it("edit offers the entry's units and sends quantity and unit only", async () => {
    const api = apiStub(fetchMock).on("PATCH", `/v1/meals/${ROTI.id}`, {
      ...ROTI,
      quantity: 3,
    });
    const onClose = vi.fn();
    renderIntl(<EditEntryDialog entry={ROTI} onClose={onClose} />);
    expect(screen.getByTestId("edit-unit-g")).toBeTruthy();
    expect(screen.getByTestId("edit-unit-roti")).toBeTruthy();
    // No nutrient preview while editing.
    expect(screen.queryByTestId("portion-preview")).toBeNull();
    const qty = screen.getByLabelText(en.foods.portion.quantity);
    await userEvent.clear(qty);
    await userEvent.type(qty, "3");
    await userEvent.click(
      screen.getByRole("button", { name: en.meals.log.save }),
    );
    await waitFor(() => expect(onClose).toHaveBeenCalled());
    expect(api.callsTo("PATCH", `/v1/meals/${ROTI.id}`)[0].body).toEqual({
      quantity: 3,
      unit: "roti",
    });
  });

  it("an entry without portion units edits grams as before", () => {
    renderIntl(
      <EditEntryDialog
        entry={{ ...BASE, unit: null, quantity: null, portion_units: [] }}
        onClose={vi.fn()}
      />,
    );
    expect(screen.getByLabelText(en.meals.log.amount_grams)).toBeTruthy();
    expect(screen.queryByTestId("edit-portion")).toBeNull();
  });
});
