import { readFileSync } from "node:fs";
import { join } from "node:path";
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
import { DayTotals } from "@/features/history/components/DayTotals";
import { HistoryView } from "@/features/history/components/HistoryView";
import type { Summary } from "@/features/meals/api/meals";
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
const TODAY = "2026-11-03";
const ME = "a0000000-0000-4000-8000-000000000001";
const DAD = "893abc63-23d3-581a-8afe-6488a50f33df";
const member = (id: string, name: string, primary: boolean) => ({
  id,
  name,
  relation: primary ? "self" : "parent",
  birth_year: null,
  sex: null,
  height_cm: null,
  weight_kg: null,
  diet: "non_veg",
  allergens: [],
  conditions: [],
  custom_alerts: [],
  goal: null,
  is_primary: primary,
});
const MEMBERS = [member(ME, "", true), member(DAD, "Dad", false)];

const week = (): Summary =>
  JSON.parse(
    readFileSync(
      join(
        process.cwd(),
        "../../packages/test-fixtures/meals/expected/week_family.dad_diabetic.json",
      ),
      "utf8",
    ),
  );

/** A period=day summary built from one day of the week fixture. */
function daySummary(date: string, edit?: (s: Summary) => void): Summary {
  const w = week();
  const d = w.days.find((x) => x.date === date) ?? w.days[6];
  const s = {
    ...w,
    period: "day",
    start: d.date,
    end: d.date,
    totals: d.totals,
    incomplete: d.incomplete,
    bands: d.bands,
    days: [d],
  } as Summary;
  edit?.(s);
  return s;
}

const meal = (over: object = {}) => ({
  id: "c0000000-0000-4000-8000-000000000001",
  member_id: ME,
  product_id: null,
  barcode: "8901063201089",
  product_name: "Sugar Free Biscuit",
  grade: "D",
  grams: 25,
  eaten_at: "2026-11-03T03:30:00+00:00",
  nutrients: {
    energy_kcal: 120,
    sugars_g: null,
    salt_g: 0.2,
    protein_g: 2,
    fat_g: 5,
    sat_fat_g: 2,
    carbs_g: 17,
  },
  client_id: null,
  attribution: "attribution.off",
  ...over,
});

function stub(day: (date: string) => Summary = (d) => daySummary(d)) {
  return apiStub(fetchMock)
    .on("GET", "/v1/members", MEMBERS)
    .on("GET", "/v1/meals/summary", (c) =>
      json(
        200,
        c.query.get("period") === "week"
          ? week()
          : day(c.query.get("date") ?? ""),
      ),
    )
    .on("GET", "/v1/meals", [meal()]);
}

function view() {
  return render(
    <QueryClientProvider
      client={
        new QueryClient({ defaultOptions: { queries: { retry: false } } })
      }
    >
      <NextIntlClientProvider locale="en" messages={clientMessages(en)}>
        <HistoryView today={TODAY} />
      </NextIntlClientProvider>
    </QueryClientProvider>,
  );
}

beforeEach(() => {
  fetchMock.mockReset();
  track.mockReset();
});
afterEach(cleanup);

describe("HistoryView", () => {
  it("loading: a status while members load", () => {
    fetchMock.mockImplementation(() => new Promise(() => {}));
    view();
    expect(screen.getByRole("status").textContent).toBe(en.common.loading);
    expect(screen.getByTestId("disclaimer")).toBeTruthy();
  });

  it("error: the members error with a retry", async () => {
    apiStub(fetchMock).on(
      "GET",
      "/v1/members",
      json(500, envelope("internal_error")),
    );
    view();
    expect(await screen.findByText(en.error.internal_error)).toBeTruthy();
    expect(screen.getByRole("button", { name: en.common.retry })).toBeTruthy();
  });

  it("data: today's totals, the logged items and the week, for the primary member", async () => {
    const api = stub();
    view();
    expect(await screen.findByTestId("day-totals")).toBeTruthy();
    expect(screen.getByTestId("day-title").textContent).toBe(en.history.today);
    expect(await screen.findByText("Sugar Free Biscuit")).toBeTruthy();
    expect(await screen.findByTestId("weekly-dashboard")).toBeTruthy();
    expect(screen.getByText(en.attribution.off)).toBeTruthy();
    const day = api
      .callsTo("GET", "/v1/meals/summary")
      .find((c) => c.query.get("period") === "day");
    expect(day?.query.get("member_id")).toBe(ME);
    expect(day?.query.get("date")).toBe(TODAY);
    const list = api.callsTo("GET", "/v1/meals")[0];
    expect(list.query.get("from")).toBe("2026-11-03T00:00:00+05:30");
    expect(list.query.get("to")).toBe("2026-11-04T00:00:00+05:30");
    // Today's sugar from the API, against the daily limit.
    expect(
      within(screen.getByTestId("day-sugars_g")).getByTestId("day-value")
        .textContent,
    ).toBe("4.9 g of 25 g");
  });

  it("past days: previous day loads that IST day; next is disabled on today", async () => {
    const api = stub();
    view();
    await screen.findByTestId("day-totals");
    const next = screen.getByRole("button", { name: en.history.next_day });
    expect((next as HTMLButtonElement).disabled).toBe(true);
    await userEvent
      .setup()
      .click(screen.getByRole("button", { name: en.history.previous_day }));
    await waitFor(() =>
      expect(screen.getByTestId("day-title").textContent).not.toBe(
        en.history.today,
      ),
    );
    expect(screen.getByTestId("day-title").textContent).toContain("November");
    await screen.findByTestId("day-totals-empty"); // 2 Nov: nothing logged
    expect(
      api
        .callsTo("GET", "/v1/meals")
        .some((c) => c.query.get("from") === "2026-11-02T00:00:00+05:30"),
    ).toBe(true);
    expect((next as HTMLButtonElement).disabled).toBe(false);
  });

  it("switching member reloads that member's summaries", async () => {
    const api = stub();
    view();
    await screen.findByTestId("day-totals");
    await userEvent
      .setup()
      .selectOptions(screen.getByLabelText(en.history.member), DAD);
    await waitFor(() =>
      expect(
        api
          .callsTo("GET", "/v1/meals/summary")
          .some((c) => c.query.get("member_id") === DAD),
      ).toBe(true),
    );
  });

  it("remove asks first, then deletes the log", async () => {
    const api = stub().on(
      "DELETE",
      "/v1/meals/c0000000-0000-4000-8000-000000000001",
      new Response(null, { status: 204 }),
    );
    view();
    const user = userEvent.setup();
    await user.click(
      await screen.findByRole("button", { name: en.history.remove }),
    );
    const dialog = screen.getByTestId("confirm-dialog");
    expect(within(dialog).getByText(en.history.remove_confirm)).toBeTruthy();
    await user.click(
      within(dialog).getByRole("button", { name: en.history.remove }),
    );
    await waitFor(() =>
      expect(
        api.callsTo("DELETE", "/v1/meals/c0000000-0000-4000-8000-000000000001"),
      ).toHaveLength(1),
    );
    expect(track).toHaveBeenCalledWith("meal_removed");
  });

  it("grades: the 'calculated by SmartNutri' credit shows once per list (F3)", async () => {
    stub().on("GET", "/v1/meals", [
      meal(),
      meal({ id: "c0000000-0000-4000-8000-000000000002", grade: "B" }),
    ]);
    view();
    await screen.findAllByTestId("meal-row");
    expect(screen.getAllByText(en.nutriscore.calculated_by)).toHaveLength(1);
  });

  it("no graded item: no credit line", async () => {
    stub().on("GET", "/v1/meals", [meal({ grade: null })]);
    view();
    await screen.findAllByTestId("meal-row");
    expect(screen.queryByText(en.nutriscore.calculated_by)).toBeNull();
  });

  it("an empty day list says nothing was logged", async () => {
    stub().on("GET", "/v1/meals", []);
    view();
    expect(await screen.findByTestId("day-list-empty")).toBeTruthy();
  });

  it("a summary error shows the error with a retry", async () => {
    stub().on(
      "GET",
      "/v1/meals/summary",
      json(404, envelope("member_not_found")),
    );
    view();
    expect(
      (await screen.findAllByText(en.error.member_not_found)).length,
    ).toBeGreaterThan(0);
  });
});

function totals(s: Summary) {
  return render(
    <NextIntlClientProvider locale="en" messages={clientMessages(en)}>
      <DayTotals summary={s} />
    </NextIntlClientProvider>,
  );
}
const value = (key: string) =>
  within(screen.getByTestId(`day-${key}`)).getByTestId("day-value").textContent;
const badge = (key: string) =>
  within(screen.getByTestId(`day-${key}`)).queryByTestId("band-badge");

describe("DayTotals", () => {
  it("over: the sugar band from the API, against the daily limit", () => {
    totals(daySummary("2026-10-31"));
    expect(value("sugars_g")).toBe("35 g of 25 g");
    expect(badge("sugars_g")?.getAttribute("data-band")).toBe("over");
    expect(badge("sugars_g")?.textContent).toContain(en.summary.band.over);
  });

  it("null totals (Ruling M1): 'Not enough data', never 0, never ok", () => {
    totals(
      daySummary("2026-11-03", (s) => {
        const t = s.totals as unknown as Record<string, number | null>;
        t.sugars_g = null;
        t.protein_g = null;
        t.energy_kcal = null;
        // A stale "ok" next to a null total must not read as fine.
        s.bands.sugar_g = "ok";
      }),
    );
    expect(value("sugars_g")).toBe(en.summary.band.unknown);
    expect(badge("sugars_g")?.getAttribute("data-band")).toBe("unknown");
    expect(value("protein_g")).toBe(en.summary.band.unknown);
    expect(value("energy_kcal")).toBe(en.summary.band.unknown);
    // S3 (Android parity): a null protein or kcal total carries the grey chip.
    for (const k of ["protein_g", "energy_kcal"])
      expect(badge(k)?.getAttribute("data-band")).toBe("unknown");
    expect(screen.getByTestId("day-totals").textContent).not.toMatch(/\b0 g/);
  });

  it("an incomplete 0 total (API before M1) is unknown too, with the note", () => {
    totals(daySummary("2026-11-01"));
    expect(value("sugars_g")).toBe(en.summary.band.unknown);
    expect(badge("sugars_g")?.getAttribute("data-band")).toBe("unknown");
    expect(
      within(screen.getByTestId("day-sugars_g")).getByText(
        en.summary.incomplete,
      ),
    ).toBeTruthy();
  });

  it("protein is progress to a target: no band, never 'Within limit'", () => {
    for (const band of ["ok", "unknown"] as const) {
      cleanup();
      totals(
        daySummary("2026-11-03", (s) => {
          s.bands.protein_g = band;
        }),
      );
      expect(value("protein_g")).toBe("8 g of a 58.1 g target");
      expect(badge("protein_g")).toBeNull();
      expect(screen.getByTestId("day-protein_g").textContent).not.toContain(
        en.summary.band.ok,
      );
    }
  });

  it("no protein target (no weight, or a child): the total and the hint", () => {
    totals(
      daySummary("2026-11-03", (s) => {
        s.limits.protein_target_g = null;
      }),
    );
    expect(value("protein_g")).toBe("8 g");
    expect(screen.getByText(en.summary.no_protein_target)).toBeTruthy();
  });

  it("calories are information only", () => {
    totals(daySummary("2026-11-03"));
    expect(value("energy_kcal")).toBe("225 kcal");
    expect(badge("energy_kcal")).toBeNull();
    expect(screen.getByText(en.summary.kcal_info)).toBeTruthy();
  });

  it("a day with nothing logged says so", () => {
    totals(daySummary("2026-10-30"));
    expect(screen.getByTestId("day-totals-empty").textContent).toBe(
      en.summary.nothing_logged,
    );
  });
});
