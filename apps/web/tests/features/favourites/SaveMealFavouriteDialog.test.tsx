import { cleanup, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { SaveMealFavouriteDialog } from "@/features/favourites/components/SaveMealFavouriteDialog";
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
const SLOT = "d0000000-0000-4000-8000-000000000001";

beforeEach(() => {
  fetchMock.mockReset();
  track.mockReset();
});
afterEach(cleanup);

function open(locale: "en" | "hi" | "mr" = "en") {
  const onSaved = vi.fn();
  const onClose = vi.fn();
  renderIntl(
    <SaveMealFavouriteDialog
      fromDate="2026-11-07"
      fromSlotId={SLOT}
      onClose={onClose}
      onSaved={onSaved}
    />,
    locale,
  );
  return { onSaved, onClose };
}

describe("SaveMealFavouriteDialog", () => {
  it.each(["hi", "mr"] as const)(
    "name kept exactly as typed in %s",
    async (locale) => {
      const api = apiStub(fetchMock).on("POST", "/v1/favourites/meals", (_c) =>
        json(201, { id: "x" }),
      );
      const { onSaved } = open(locale);
      const name = " माझा नाश्ता  ";
      await userEvent.type(screen.getByRole("textbox"), name);
      await userEvent.click(
        screen.getByRole("button", {
          name: MESSAGES[locale].favourites.save_meal,
        }),
      );
      await waitFor(() => expect(onSaved).toHaveBeenCalled());
      expect(api.callsTo("POST", "/v1/favourites/meals")[0].body).toMatchObject(
        {
          name,
          from_date: "2026-11-07",
          from_slot_id: SLOT,
        },
      );
    },
  );

  it("empty slot shows copy_source_empty message", async () => {
    apiStub(fetchMock).on(
      "POST",
      "/v1/favourites/meals",
      json(422, envelope("copy_source_empty")),
    );
    open();
    await userEvent.type(screen.getByRole("textbox"), "Usual");
    await userEvent.click(
      screen.getByRole("button", { name: en.favourites.save_meal }),
    );
    expect((await screen.findByRole("alert")).textContent).toBe(
      en.error.copy_source_empty,
    );
  });

  it("blocks a blank or over-long name", async () => {
    const api = apiStub(fetchMock);
    open();
    const save = screen.getByRole("button", { name: en.favourites.save_meal });
    expect((save as HTMLButtonElement).disabled).toBe(true);
    await userEvent.type(screen.getByRole("textbox"), "x".repeat(41));
    expect((save as HTMLButtonElement).disabled).toBe(true);
    expect(api.calls).toHaveLength(0);
  });

  it("name never in analytics", async () => {
    apiStub(fetchMock).on(
      "POST",
      "/v1/favourites/meals",
      json(201, { id: "x" }),
    );
    const { onSaved } = open();
    await userEvent.type(screen.getByRole("textbox"), "My usual breakfast");
    await userEvent.click(
      screen.getByRole("button", { name: en.favourites.save_meal }),
    );
    await waitFor(() => expect(onSaved).toHaveBeenCalled());
    expect(JSON.stringify(track.mock.calls)).not.toContain("usual");
  });
});
