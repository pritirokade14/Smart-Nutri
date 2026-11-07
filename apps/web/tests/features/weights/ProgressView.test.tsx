import { cleanup, screen, waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { ProgressView } from "@/features/weights/components/ProgressView";
import { LOCALES, MESSAGES } from "../../support/analyze-fixtures";
import { apiStub, envelope, json } from "../../support/api-stub";
import { digitsOutsideAllowed, renderIntl } from "../../support/diary-render";
import { WEIGHT_STEMS, weightTrend } from "../../support/weight-fixtures";

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
const TARGETS = (flags: string[] = []) => ({
  status: "ready",
  flags,
  numbers_hidden: { energy: false, macros: false },
  explanation: null,
});

function stub(
  stem: string,
  flags: string[] = [],
  edit?: Parameters<typeof weightTrend>[1],
) {
  return apiStub(fetchMock)
    .on("GET", "/v1/weights/trend", () => json(200, weightTrend(stem, edit)))
    .on("GET", "/v1/weights", { items: [], numbers_hidden: false })
    .on("GET", "/v1/targets", () => json(200, TARGETS(flags)));
}
const view = (loc: (typeof LOCALES)[number] = "en") =>
  renderIntl(<ProgressView today="2026-11-07" />, loc);

beforeEach(() => {
  fetchMock.mockReset();
});
afterEach(cleanup);

describe("ProgressView", () => {
  it("renders weights/expected weekly_rate_loss", async () => {
    stub("weekly_rate_loss");
    view();
    expect((await screen.findByTestId("weight-rate")).textContent).toBe(
      en.weight.weekly_rate.replace("{kg}", "-0.87").replace("{pct}", "-1.1"),
    );
    expect(screen.getAllByTestId("weight-dot")).toHaveLength(4);
    expect(screen.getByTestId("weight-trend-line")).toBeTruthy();
    expect(screen.getByText(en.diary.disclaimer)).toBeTruthy();
  });

  it("projection only when ready", async () => {
    stub("projection_ready");
    view();
    expect((await screen.findByTestId("weight-projection")).textContent).toBe(
      en.weight.projection
        .replace("{target}", "75")
        .replace("{date}", "Feb 24, 2026"),
    );
    expect(screen.queryByTestId("weight-no-projection")).toBeNull();
  });

  it.each([
    ["projection_too_few", "too_few_weigh_ins"],
    ["projection_moving_away", "moving_away"],
    ["no_target", "no_target"],
    ["projection_too_far", "too_far"],
    ["projection_reached", "reached"],
  ])("%s shows the %s reason and no projection", async (stem, reason) => {
    stub(stem);
    view();
    const el = await screen.findByTestId("weight-no-projection");
    expect(el.textContent).toBe(
      (en.weight.no_projection as Record<string, string>)[reason],
    );
    expect(screen.queryByTestId("weight-projection")).toBeNull();
  });

  it.each(LOCALES)(
    "rapid loss card is neutral and uses pct in %s",
    async (loc) => {
      stub("rapid_loss_three_weeks");
      view(loc);
      const card = await screen.findByTestId("weight-rapid-loss");
      expect(card.textContent).toBe(
        MESSAGES[loc].weight.rapid_loss.replace("{pct}", "1.5"),
      );
      expect(card.className).not.toMatch(/danger|error|red|warning/);
      expect(card.textContent).not.toMatch(/support|helpline|call/i);
    },
  );

  it("hide_all leaves no digits on progress", async () => {
    apiStub(fetchMock)
      .on("GET", "/v1/weights/trend", () => json(200, weightTrend("hide_all")))
      .on("GET", "/v1/weights", () =>
        json(200, {
          numbers_hidden: true,
          items: [
            {
              date: "2026-01-02",
              weight_kg: null,
              measured_at: "2026-01-02T00:00:00Z",
              source: "manual",
              client_id: null,
              numbers_hidden: true,
            },
          ],
        }),
      )
      .on("GET", "/v1/targets", () =>
        json(200, {
          ...TARGETS(),
          numbers_hidden: { energy: true, macros: true },
        }),
      );
    view();
    await screen.findByTestId("weight-chart");
    await screen.findAllByTestId("weight-row");
    expect(digitsOutsideAllowed()).toEqual([]);
    expect(screen.queryByTestId("weight-rate")).toBeNull();
    expect(screen.queryByTestId("weight-projection")).toBeNull();
    // The shape stays: one dot per point, a trend line.
    expect(screen.getAllByTestId("weight-dot").length).toBe(20);
    const pts = screen.getByTestId("weight-trend-line").getAttribute("points");
    expect(pts?.split(" ").length).toBe(20);
  });

  it("consent card without health_data, and nothing else", async () => {
    apiStub(fetchMock)
      .on("GET", "/v1/weights/trend", () =>
        json(403, envelope("consent_required", { purposes: ["health_data"] })),
      )
      .on("GET", "/v1/consents", []);
    view();
    const card = await screen.findByTestId("weight-consent");
    expect(card.textContent).toContain(en.weight.consent);
    expect(screen.queryByTestId("weight-chart")).toBeNull();
    expect(screen.queryByTestId("weight-list")).toBeNull();
  });

  it("hide_all rapid_loss shows the no-number note, no digits", async () => {
    stub("hide_all_rapid_loss");
    view();
    const note = await screen.findByTestId("weight-rapid-loss");
    expect(note.textContent).toBe(en.weight.rapid_loss_hidden);
    expect(note.textContent).not.toMatch(/\d/);
  });

  it("deletes all weigh-ins from the consent card after confirming", async () => {
    const api = apiStub(fetchMock)
      .on("GET", "/v1/weights/trend", () =>
        json(403, envelope("consent_required", { purposes: ["health_data"] })),
      )
      .on("GET", "/v1/consents", [])
      .on("DELETE", "/v1/weights", { deleted: 3 });
    void api;
    view();
    await userEvent.click(await screen.findByTestId("weight-delete-all"));
    const dlg = await screen.findByTestId("confirm-dialog");
    expect(dlg.textContent).toContain(en.weight.delete_all_confirm);
    await userEvent.click(
      within(dlg).getByRole("button", { name: en.weight.delete_all }),
    );
    expect(
      (await screen.findByTestId("weight-delete-all-done")).textContent,
    ).toBe(en.weight.delete_all_done);
    expect(
      fetchMock.mock.calls.some(
        ([u, i]) =>
          String(u instanceof Request ? u.url : u).endsWith("/v1/weights") &&
          (i?.method ?? (u instanceof Request ? u.method : "")) === "DELETE",
      ),
    ).toBe(true);
  });

  it("chart x spans the requested from..to, not the data", async () => {
    stub("weekly_rate_loss", [], (d) => {
      d.from = "2026-01-01";
      d.to = "2026-01-31";
    });
    view();
    await screen.findByTestId("weight-chart");
    const xs = screen
      .getAllByTestId("weight-dot")
      .map((c) => Number(c.getAttribute("cx")));
    const dates = screen
      .getByTestId("weight-chart-table")
      .querySelectorAll("tbody tr");
    expect(dates.length).toBeGreaterThan(0);
    // Data covers fewer days than the range, so the span of x is under full width.
    expect(Math.max(...xs) - Math.min(...xs)).toBeLessThan(320 - 24 - 1);
    expect(Math.min(...xs)).toBeGreaterThanOrEqual(12);
  });

  it("taper and goal-reached notes come from today's targets", async () => {
    stub("weekly_rate_loss", ["taper_active", "goal_weight_reached"]);
    view();
    expect(
      (await screen.findByTestId("weight-flag-taper_active")).textContent,
    ).toBe(en.targets.flag.taper_active);
    expect(screen.getByTestId("weight-flag-goal_weight_reached")).toBeTruthy();
  });

  it("an empty window says so and offers adding", async () => {
    stub("weekly_rate_loss", [], (d) => {
      d.points = [];
      d.trend = [];
    });
    view();
    expect(await screen.findByTestId("weight-empty-chart")).toBeTruthy();
    expect(screen.getByTestId("weight-add")).toBeTruthy();
  });

  it("range chips ask the API for 30, 90 and 365 days", async () => {
    const api = stub("weekly_rate_loss");
    view();
    await screen.findByTestId("weight-chart");
    await userEvent.click(
      screen.getByRole("button", { name: en.weight.range["365"] }),
    );
    await waitFor(() =>
      expect(
        api.callsTo("GET", "/v1/weights/trend").at(-1)?.query.get("days"),
      ).toBe("365"),
    );
  });

  it.each(LOCALES)("no streak or rating text in %s", async (loc) => {
    stub("weekly_rate_loss");
    view(loc);
    await screen.findByTestId("weight-chart");
    expect((document.body.textContent ?? "").toLowerCase()).not.toMatch(
      /streak|\bgood\b|\bbad\b|\bgreat\b|well done/,
    );
  });

  it.each(WEIGHT_STEMS)("the golden %s renders without error", async (stem) => {
    stub(stem);
    view();
    await screen.findByTestId("weight-chart");
    const table = screen.getByTestId("weight-chart-table");
    expect(within(table).getAllByRole("row").length).toBeGreaterThan(1);
  });

  it("the outlier dot is hollow and labelled", async () => {
    stub("single_outlier");
    view();
    const dot = await screen.findByTestId("weight-dot-outlier");
    expect(dot.getAttribute("class")).toContain("fill-transparent");
    expect(dot.textContent).toBe(en.weight.outlier);
  });

  it("the trend line uses the brand token, never danger", async () => {
    stub("weekly_rate_loss");
    view();
    const line = await screen.findByTestId("weight-trend-line");
    expect(line.getAttribute("class")).toContain("stroke-brand-primary");
    expect(line.getAttribute("class")).not.toMatch(/danger|avoid|caution/);
  });
});
