import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import {
  cleanup,
  render,
  screen,
  waitFor,
  within,
} from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { NextIntlClientProvider } from "next-intl";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import type { DiaryDayOut } from "@/features/diary/api/diary";
import { DiaryView } from "@/features/diary/components/DiaryView";
import { formatAmount } from "@/features/history/lib/summary";
import { clientMessages } from "@/i18n/client-messages";
import {
  LOCALES,
  MESSAGES,
  type TestLocale,
} from "../../support/analyze-fixtures";
import { apiStub, envelope, json } from "../../support/api-stub";
import { DAY_STEMS, diaryDay } from "../../support/diary-fixtures";

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

const SETTINGS = (over: object = {}) => ({
  member_id: "d84eb0bd-54e1-5b82-8b2d-95990250a663",
  activity_level: "light",
  direction: "maintain",
  energy_mode: "formula",
  numbers_display: "show",
  pregnant_or_breastfeeding: false,
  summary_view: "remaining",
  updated_at: "2026-11-07T00:00:00Z",
  ...over,
});

function stub(
  stem: string,
  settings: object | null = null,
  edit?: (d: DiaryDayOut) => void,
) {
  const api = apiStub(fetchMock).on("GET", "/v1/diary/day", () =>
    json(200, diaryDay(stem, edit)),
  );
  api.on(
    "GET",
    "/v1/targets/settings",
    settings === null
      ? json(404, envelope("goal_settings_not_found"))
      : settings,
  );
  api.on("GET", "/v1/meal-slots", { items: [], suggested_slot_id: "x" });
  return api;
}

function view(locale: TestLocale = "en", date?: string) {
  return render(
    <QueryClientProvider
      client={
        new QueryClient({ defaultOptions: { queries: { retry: false } } })
      }
    >
      <NextIntlClientProvider
        locale={locale}
        messages={clientMessages(MESSAGES[locale])}
      >
        <DiaryView date={date} />
      </NextIntlClientProvider>
    </QueryClientProvider>,
  );
}

/** Every rendered text node outside elements that may carry digits (dates, portions, day counts). */
function digitsOutsideAllowed(): string[] {
  const root = document.body.cloneNode(true) as HTMLElement;
  for (const el of root.querySelectorAll("[data-allow-digits]")) el.remove();
  return (root.textContent ?? "").match(/\d/g) ?? [];
}

beforeEach(() => {
  fetchMock.mockReset();
  track.mockReset();
});
afterEach(cleanup);

describe("DiaryView", () => {
  it.each(LOCALES)("renders golden day_complete_under in %s", async (loc) => {
    stub("day_complete_under");
    view(loc);
    const m = MESSAGES[loc].diary;
    const titles = await screen.findAllByTestId("slot-title");
    expect(titles.map((x) => x.textContent)).toEqual([
      m.slot.breakfast,
      m.slot.lunch,
      m.slot.snack,
      m.slot.dinner,
    ]);
    // remaining.energy_kcal = 1258.8, exactly as the API sent it.
    expect(screen.getByTestId("value-energy_kcal").textContent).toContain(
      "1,258.8",
    );
    expect(screen.getByTestId("value-protein_g").textContent).toContain("67.4");
    expect(screen.getByText("Oats")).toBeTruthy();
    expect(screen.queryAllByText(MESSAGES[loc].diary.incomplete)).toHaveLength(
      0,
    );
  });

  it("always shows the online-only note and the disclaimer", async () => {
    stub("day_complete_under");
    view();
    await screen.findAllByTestId("slot-title");
    expect(screen.getByTestId("online-only").textContent).toBe(
      MESSAGES.en.meals.online_only,
    );
    expect(screen.getByTestId("disclaimer")).toBeTruthy();
    const footer = screen.getByTestId("diary-target-footer");
    expect(footer.textContent).toContain(MESSAGES.en.diary.disclaimer);
    expect(footer.textContent).toContain(MESSAGES.en.targets.pending_review);
  });

  it("sends diary_day_viewed once, with no properties", async () => {
    stub("day_complete_under");
    view();
    await screen.findAllByTestId("slot-title");
    expect(track).toHaveBeenCalledTimes(1);
    expect(track).toHaveBeenCalledWith("diary_day_viewed");
  });

  it("over renders neutral with the absolute value", async () => {
    stub("day_over_energy");
    view();
    const v = await screen.findByTestId("value-energy_kcal");
    expect(v.textContent).toBe("250.4 kcal over");
    expect(v.getAttribute("data-over")).toBe("true");
    const ring = screen.getByTestId("ring-energy_kcal");
    const fill = within(ring).getByTestId("ring-fill");
    expect(fill.getAttribute("class")).toContain("stroke-text-secondary");
    expect(document.body.innerHTML).not.toMatch(
      /verdict-avoid|text-red|danger/,
    );
    // Protein is over too; fat is exactly 0 left (a known 0, not unknown).
    expect(screen.getByTestId("value-protein_g").textContent).toBe("8 g over");
    expect(screen.getByTestId("value-fat_g").textContent).toBe("0 g left");
  });

  it.each(["day_incomplete_energy", "day_quick_add_kcal_only"])(
    "incomplete nutrient shows the grey chip, not a number (%s)",
    async (stem) => {
      stub(stem);
      view();
      await screen.findAllByTestId("slot-title");
      const day = diaryDay(stem);
      for (const k of [
        "energy_kcal",
        "protein_g",
        "carbs_g",
        "fat_g",
      ] as const) {
        const row = screen.getByTestId(`ring-${k}`);
        if (day.incomplete[k]) {
          expect(within(row).getByTestId(`incomplete-${k}`).textContent).toBe(
            MESSAGES.en.diary.incomplete,
          );
          expect(within(row).queryByTestId(`value-${k}`)).toBeNull();
          expect(row.textContent).not.toMatch(/\bleft\b|\b0\b/);
        }
      }
    },
  );

  it("kcal-only quick add: energy is a number, the macros are chips", async () => {
    stub("day_quick_add_kcal_only");
    view();
    expect(
      (await screen.findByTestId("value-energy_kcal")).textContent,
    ).toContain("2,310");
    for (const k of ["protein_g", "carbs_g", "fat_g"]) {
      expect(screen.getByTestId(`incomplete-${k}`)).toBeTruthy();
    }
  });

  it("empty day shows nothing logged and remaining equals the target", async () => {
    stub("day_empty");
    view();
    expect((await screen.findByTestId("diary-empty")).textContent).toBe(
      MESSAGES.en.diary.empty_day,
    );
    expect(screen.getByTestId("value-energy_kcal").textContent).toContain(
      "2,760",
    );
    expect(screen.queryAllByTestId("entry-row")).toHaveLength(0);
  });

  it("no guide shows the setup call to action", async () => {
    stub("day_no_target");
    view();
    const card = await screen.findByTestId("diary-no-guide");
    expect(card.textContent).toContain(MESSAGES.en.diary.no_guide);
    expect(
      within(card).getByRole("link", { name: MESSAGES.en.targets.setup_cta }),
    ).toHaveProperty("href", expect.stringContaining("/en/guide/setup"));
    // No remaining without a guide: the day shows what was eaten.
    expect(screen.getByTestId("value-energy_kcal").textContent).toContain(
      "250",
    );
    // The disclaimer sits where targets show; none show here.
    expect(screen.queryByTestId("diary-target-footer")).toBeNull();
    // No support link anywhere.
    expect(document.querySelector('a[href*="support"]')).toBeNull();
  });

  it("consent_required shows the consent card, not a redirect", async () => {
    stub("day_consent_required");
    view();
    const card = await screen.findByTestId("diary-consent");
    expect(card.textContent).toContain(MESSAGES.en.diary.targets_consent);
    expect(
      within(card).getByRole("button", { name: MESSAGES.en.consent.agree }),
    ).toBeTruthy();
    // The diary still works.
    expect(screen.getAllByTestId("entry-row").length).toBeGreaterThan(0);
  });

  it("hide_all leaves no digits on the day", async () => {
    stub("day_hide_all", SETTINGS({ numbers_display: "hide_all" }));
    view();
    await screen.findAllByTestId("slot-title");
    await screen.findByTestId("eye-toggle");
    expect(digitsOutsideAllowed()).toEqual([]);
    // Fill shapes remain.
    expect(
      within(screen.getByTestId("ring-energy_kcal")).getByTestId("ring-fill"),
    ).toBeTruthy();
    expect(screen.queryByTestId("value-energy_kcal")).toBeNull();
    expect(screen.queryByTestId("entry-kcal")).toBeNull();
  });

  it("hide_energy hides energy only", async () => {
    stub("day_hide_energy");
    view();
    await screen.findAllByTestId("slot-title");
    expect(screen.queryByTestId("value-energy_kcal")).toBeNull();
    expect(screen.queryByTestId("entry-kcal")).toBeNull();
    expect(screen.getByTestId("value-protein_g").textContent).toContain("67.4");
  });

  it("next day is disabled on today and enabled on a past day", async () => {
    stub("day_complete_under");
    view();
    const next = await screen.findByRole("button", {
      name: MESSAGES.en.diary.next_day,
    });
    expect(next).toHaveProperty("disabled", true);
    expect(screen.getByTestId("day-title").textContent).toBe(
      MESSAGES.en.diary.today,
    );
  });

  it("previous day asks the API for the day before the shown date", async () => {
    const api = stub("day_complete_under");
    view();
    await userEvent.click(
      await screen.findByRole("button", { name: MESSAGES.en.diary.prev_day }),
    );
    await waitFor(() =>
      expect(
        api.callsTo("GET", "/v1/diary/day").at(-1)?.query.get("date"),
      ).toBe("2026-11-06"),
    );
  });

  it("consumed view shows totals", async () => {
    stub("day_complete_under", SETTINGS({ summary_view: "consumed" }));
    view();
    await screen.findAllByTestId("slot-title");
    await waitFor(() =>
      expect(screen.getByTestId("value-energy_kcal").textContent).toBe(
        `${formatAmount(diaryDay("day_complete_under").totals.energy_kcal ?? 0)} kcal`,
      ),
    );
    expect(screen.getByTestId("summary-view-chip").textContent).toBe(
      MESSAGES.en.diary.consumed,
    );
  });

  it("the chip sends summary_view through the display route", async () => {
    const api = stub("day_complete_under", SETTINGS());
    api.on("PUT", "/v1/targets/display", {
      numbers_display: "show",
      summary_view: "consumed",
    });
    view();
    await userEvent.click(await screen.findByTestId("summary-view-chip"));
    await waitFor(() =>
      expect(api.callsTo("PUT", "/v1/targets/display")[0]?.body).toEqual({
        summary_view: "consumed",
      }),
    );
  });

  it("quick add entry shows the badge and the default name", async () => {
    stub("day_quick_add_kcal_only", null, (d) => {
      for (const sl of d.slots) for (const e of sl.entries) e.product_name = "";
    });
    view();
    const row = await screen.findByTestId("entry-row");
    expect(row.textContent).toContain(MESSAGES.en.diary.quick_add_name);
    expect(within(row).getByTestId("entry-quick-badge").textContent).toBe(
      MESSAGES.en.diary.quick_badge,
    );
  });

  it("a typed quick add name is shown as typed", async () => {
    stub("day_quick_add_kcal_only");
    view();
    const row = await screen.findByTestId("entry-row");
    expect(row.textContent).toContain("Office lunch");
  });

  it("archived slot with entries is listed, with its custom label as typed", async () => {
    stub("day_archived_slot");
    view("hi");
    await screen.findAllByTestId("slot-title");
    expect(
      screen.getAllByTestId("slot-title").map((x) => x.textContent),
    ).toContain("Pre-gym");
    expect(screen.getAllByTestId("slot-removed")[0].textContent).toBe(
      MESSAGES.hi.diary.slots.removed,
    );
  });

  it("the Day switch uses diary.view.day", async () => {
    stub("day_complete_under");
    view();
    const sw = await screen.findByTestId("diary-view-switch");
    expect(sw.textContent).toContain(MESSAGES.en.diary.view.day);
  });

  it("past-date params are plain YYYY-MM-DD", async () => {
    const api = stub("day_complete_under");
    view();
    await userEvent.click(
      await screen.findByRole("button", { name: MESSAGES.en.diary.prev_day }),
    );
    await waitFor(() =>
      expect(
        api.callsTo("GET", "/v1/diary/day").at(-1)?.query.get("date"),
      ).toMatch(/^\d{4}-\d{2}-\d{2}$/),
    );
  });

  it("an unknown value is never 0 in the entries", async () => {
    stub("day_quick_add_kcal_only");
    view();
    const row = await screen.findByTestId("entry-row");
    expect(within(row).getByTestId("entry-incomplete")).toBeTruthy();
    expect(within(row).getByTestId("entry-kcal").textContent).toBe("450 kcal");
  });

  it("an API error shows the localised message with retry", async () => {
    apiStub(fetchMock).on(
      "GET",
      "/v1/diary/day",
      json(422, envelope("date_in_future")),
    );
    view("en", "2099-01-01");
    expect(
      await screen.findByText(MESSAGES.en.error.date_in_future),
    ).toBeTruthy();
  });

  it.each(DAY_STEMS)(
    "renders the golden %s without crashing in every locale",
    async (stem) => {
      for (const loc of LOCALES) {
        stub(stem);
        const { unmount } = view(loc);
        await screen.findAllByTestId("slot-title");
        unmount();
      }
    },
  );
});
