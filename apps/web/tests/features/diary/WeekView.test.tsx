import { cleanup, screen, waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { DiaryView } from "@/features/diary/components/DiaryView";
import { WeekView } from "@/features/diary/components/WeekView";
import { LOCALES, MESSAGES } from "../../support/analyze-fixtures";
import { apiStub, envelope, json } from "../../support/api-stub";
import { diaryDay, diaryWeek } from "../../support/diary-fixtures";
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
vi.mock("@/lib/analytics", () => ({ track: vi.fn() }));

const en = MESSAGES.en;

function stubWeek(stem: string, edit?: Parameters<typeof diaryWeek>[1]) {
  return apiStub(fetchMock)
    .on("GET", "/v1/diary/week", () => json(200, diaryWeek(stem, edit)))
    .on("GET", "/v1/meals/week_counts", {
      start: "2026-11-01",
      end: "2026-11-07",
      scans: 3,
      logged: 6,
    });
}

beforeEach(() => {
  fetchMock.mockReset();
});
afterEach(cleanup);

describe("WeekView", () => {
  it.each(LOCALES)("renders golden week_mixed in %s", async (loc) => {
    stubWeek("week_mixed");
    renderIntl(<WeekView today="2026-11-07" onPickDay={vi.fn()} />, loc);
    const m = MESSAGES[loc].diary;
    const tiles = await screen.findAllByTestId("week-tile");
    expect(tiles.map((x) => x.getAttribute("data-date"))).toEqual([
      "2026-11-01",
      "2026-11-02",
      "2026-11-03",
      "2026-11-04",
      "2026-11-05",
      "2026-11-06",
      "2026-11-07",
    ]);
    // Averages over the 5 averaged days, exactly as the API sent them.
    const avg = screen.getByTestId("week-averages");
    // The averaged-days count comes from the API (5), in the locale's own ICU
    // plural (Latin digits in every locale).
    const avgText = avg.querySelector("[data-allow-digits]")?.textContent ?? "";
    expect(avgText).toContain("5");
    expect(avgText).not.toMatch(/[०-९]/);
    expect(
      screen.getByTestId("week-average-energy_kcal").textContent,
    ).toContain("1,630");
    expect(screen.getByTestId("week-average-protein_g").textContent).toContain(
      "91",
    );
    // 2 of 5 logged days met the protein guide.
    expect(screen.getByTestId("week-protein-days").textContent).toMatch(
      /^(?=.*2)(?=.*5)/,
    );
    // The partly logged day carries the badge; the incomplete day the marker.
    expect(within(tiles[2]).getByTestId("week-partial").textContent).toBe(
      m.partial_badge,
    );
    expect(within(tiles[4]).getByTestId("week-incomplete")).toBeTruthy();
    // Each day with a target has its own line; the day without one has none.
    expect(within(tiles[0]).getByTestId("week-target-line")).toBeTruthy();
    expect(within(tiles[5]).queryByTestId("week-target-line")).toBeNull();
    // The empty day shows no number (never 0).
    expect(within(tiles[3]).queryByTestId("week-kcal")).toBeNull();
  });

  it("averages that are lower bounds read 'at least', in grey", async () => {
    stubWeek("week_mixed");
    renderIntl(<WeekView today="2026-11-07" onPickDay={vi.fn()} />);
    const row = await screen.findByTestId("week-at-least-energy_kcal");
    expect(row.textContent).toBe(
      en.diary.week.at_least.replace("{value}", "1,630 kcal"),
    );
    expect(row.className).toContain("text-text-secondary");
  });

  it("the week average count is a Latin digit in Marathi", async () => {
    stubWeek("week_mixed");
    renderIntl(<WeekView today="2026-11-07" onPickDay={vi.fn()} />, "mr");
    const avg = await screen.findByTestId("week-averages");
    const text = avg.querySelector("[data-allow-digits]")?.textContent ?? "";
    expect(text).toContain("5");
    expect(text).not.toMatch(/[०-९]/);
  });

  it.each(LOCALES)("no rating or streak text in %s", async (loc) => {
    stubWeek("week_mixed");
    renderIntl(<WeekView today="2026-11-07" onPickDay={vi.fn()} />, loc);
    await screen.findAllByTestId("week-tile");
    const text = (document.body.textContent ?? "").toLowerCase();
    expect(text).not.toMatch(
      /streak|\bgood\b|\bbad\b|\bgreat\b|\bpoor\b|well done/,
    );
    const msgs = MESSAGES[loc].diary.week;
    expect(JSON.stringify(msgs).toLowerCase()).not.toMatch(
      /streak|good|bad|great/,
    );
  });

  it("an incomplete day with a raw 0 total shows no kcal number", async () => {
    stubWeek("week_mixed", (w) => {
      w.days[4].totals.energy_kcal = 0;
      w.days[4].incomplete.energy_kcal = true;
      w.days[4].items = Math.max(w.days[4].items, 1);
    });
    renderIntl(<WeekView today="2026-11-07" onPickDay={vi.fn()} />);
    const tiles = await screen.findAllByTestId("week-tile");
    expect(within(tiles[4]).queryByTestId("week-kcal")).toBeNull();
    expect(within(tiles[4]).getByTestId("week-incomplete")).toBeTruthy();
  });

  it("hide_all leaves no digits on the week", async () => {
    stubWeek("week_hide_all");
    renderIntl(<WeekView today="2026-11-07" onPickDay={vi.fn()} />);
    await screen.findAllByTestId("week-tile");
    expect(digitsOutsideAllowed()).toEqual([]);
    expect(screen.queryByTestId("week-kcal")).toBeNull();
    expect(screen.queryByTestId("week-averages")).toBeNull();
    // The API still sends the count; the client shows nothing derived from a hidden target.
    expect(screen.queryByTestId("week-protein-days")).toBeNull();
    // Bar shapes remain.
    expect(screen.getAllByTestId("week-bar").length).toBeGreaterThan(0);
    expect(screen.queryByTestId("week-target-line")).toBeNull();
  });

  it("picking a tile opens that day", async () => {
    stubWeek("week_mixed");
    const onPick = vi.fn();
    renderIntl(<WeekView today="2026-11-07" onPickDay={onPick} />);
    const tiles = await screen.findAllByTestId("week-tile");
    await userEvent.click(within(tiles[1]).getByRole("button"));
    expect(onPick).toHaveBeenCalledWith("2026-11-02");
  });

  it("shows the share action and the disclaimer", async () => {
    stubWeek("week_mixed");
    renderIntl(<WeekView today="2026-11-07" onPickDay={vi.fn()} />);
    expect(
      await screen.findByRole("button", { name: en.diary.share_week }),
    ).toBeTruthy();
    expect(
      screen.queryAllByText(/Information, not medical advice/),
    ).toHaveLength(0);
  });

  it("an API error shows the localised message", async () => {
    apiStub(fetchMock).on(
      "GET",
      "/v1/diary/week",
      json(422, envelope("date_in_future")),
    );
    renderIntl(<WeekView onPickDay={vi.fn()} />);
    expect(await screen.findByText(en.error.date_in_future)).toBeTruthy();
  });
});

describe("Day and week switch, partial day", () => {
  function stubDay() {
    return apiStub(fetchMock)
      .on("GET", "/v1/diary/day", () =>
        json(200, diaryDay("day_complete_under")),
      )
      .on(
        "GET",
        "/v1/targets/settings",
        json(404, envelope("goal_settings_not_found")),
      )
      .on("GET", "/v1/meal-slots", { items: [], suggested_slot_id: "x" })
      .on("GET", "/v1/diary/week", () => json(200, diaryWeek("week_mixed")))
      .on("GET", "/v1/meals/week_counts", {
        start: "a",
        end: "b",
        scans: 0,
        logged: 0,
      });
  }

  it("the Week control shows the week and a tile opens its day", async () => {
    const api = stubDay();
    renderIntl(<DiaryView />);
    await screen.findAllByTestId("slot-title");
    await userEvent.click(
      screen.getByRole("button", { name: en.diary.week.title }),
    );
    const tiles = await screen.findAllByTestId("week-tile");
    await userEvent.click(within(tiles[1]).getByRole("button"));
    await waitFor(() =>
      expect(
        api.callsTo("GET", "/v1/diary/day").at(-1)?.query.get("date"),
      ).toBe("2026-11-02"),
    );
    expect(await screen.findAllByTestId("slot-title")).toHaveLength(4);
  });

  it("mark partial toggles and explains", async () => {
    const api = stubDay().on("PUT", "/v1/diary/days/2026-11-07/status", {
      date: "2026-11-07",
      partial_logged: true,
    });
    renderIntl(<DiaryView />);
    await userEvent.click(
      await screen.findByRole("button", { name: en.nav.more }),
    );
    expect(screen.getByText(en.diary.partial_note)).toBeTruthy();
    await userEvent.click(screen.getByLabelText(en.diary.mark_partial));
    await waitFor(() =>
      expect(
        api.callsTo("PUT", "/v1/diary/days/2026-11-07/status")[0]?.body,
      ).toEqual({
        partial_logged: true,
      }),
    );
  });

  it("a partly logged day shows the badge", async () => {
    apiStub(fetchMock)
      .on("GET", "/v1/diary/day", () =>
        json(
          200,
          diaryDay("day_complete_under", (d) => {
            d.partial_logged = true;
          }),
        ),
      )
      .on(
        "GET",
        "/v1/targets/settings",
        json(404, envelope("goal_settings_not_found")),
      )
      .on("GET", "/v1/meal-slots", { items: [], suggested_slot_id: "x" });
    renderIntl(<DiaryView />);
    expect((await screen.findByTestId("day-partial-badge")).textContent).toBe(
      en.diary.partial_badge,
    );
  });

  it("Add food opens the panel preselecting the tapped slot", async () => {
    const day = diaryDay("day_complete_under");
    apiStub(fetchMock)
      .on("GET", "/v1/diary/day", day)
      .on(
        "GET",
        "/v1/targets/settings",
        json(404, envelope("goal_settings_not_found")),
      )
      .on("GET", "/v1/meal-slots", {
        items: day.slots.map((s) => ({
          id: s.slot_id,
          member_id: day.member_id,
          position: s.position,
          label_key: s.label_key,
          custom_label: s.custom_label,
          default_time_window: null,
          is_default: true,
          archived: false,
        })),
        suggested_slot_id: day.slots[0].slot_id,
      })
      .on("GET", "/v1/diary/recents", { items: [] });
    renderIntl(<DiaryView />);
    await userEvent.click(
      await screen.findByRole("button", {
        name: en.diary.add_to_slot.replace("{slot}", en.diary.slot.snack),
      }),
    );
    const chips = await screen.findByTestId("slot-chips");
    expect(
      within(chips)
        .getByRole("button", { name: en.diary.slot.snack })
        .getAttribute("aria-pressed"),
    ).toBe("true");
  });
});
