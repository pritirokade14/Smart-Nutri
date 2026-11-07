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
import type { Summary } from "@/features/meals/api/meals";
import type { MemberOut } from "@/features/members/api/members";
import { TodayTargetsCard } from "@/features/targets/components/TodayTargetsCard";
import { membersMessages } from "@/i18n/client-messages";
import { setConsentRequiredHandler } from "@/lib/api/client";
import { MESSAGES } from "../../support/analyze-fixtures";
import { apiStub, consentStates, envelope, json } from "../../support/api-stub";
import { targetsFixture } from "../../support/targets-fixtures";

const nav = vi.hoisted(() => ({ push: vi.fn(), replace: vi.fn() }));
vi.mock("next/navigation", () => ({
  usePathname: () => "/en/home",
  useRouter: () => ({ push: nav.push, replace: nav.replace }),
}));
vi.mock("@/lib/supabase/client", () => ({
  createSupabaseBrowserClient: () => ({
    auth: {
      getSession: async () => ({
        data: { session: { access_token: "token" } },
      }),
    },
  }),
}));
const fetchMock = vi.hoisted(() => {
  const fn = vi.fn();
  globalThis.fetch = fn as unknown as typeof fetch;
  return fn;
});

const en = MESSAGES.en;
const PRIMARY = "a0000000-0000-4000-8000-000000000001";
const member: MemberOut = {
  id: PRIMARY,
  name: "Asha",
  relation: "self",
  birth_year: 1990,
  sex: "female",
  height_cm: 165,
  weight_kg: 70,
  body_fat_pct: null,
  diet: "non_veg",
  allergens: [],
  conditions: [],
  custom_alerts: [],
  goal: "build_muscle",
  is_primary: true,
};

const summary = (over: Partial<Summary> = {}): Summary => ({
  member_id: PRIMARY,
  period: "day",
  start: "2026-11-07",
  end: "2026-11-07",
  totals: { energy_kcal: 800, sugars_g: 20, salt_g: 3, protein_g: 40 },
  incomplete: {
    energy_kcal: false,
    sugars_g: false,
    salt_g: false,
    protein_g: false,
  },
  limits: {
    kcal: null,
    protein_target_g: 112,
    protein_g_per_kg: 1.6,
    salt_g: 5,
    sugar_g: 25,
  },
  bands: { kcal: "unknown", protein_g: "ok", salt_g: "ok", sugar_g: "near" },
  days: [],
  pending_clinician_review: true,
  protein_left_g: 72,
  numbers_hidden: { energy: false, macros: false },
  ...over,
});

let api: ReturnType<typeof apiStub>;
beforeEach(() => {
  fetchMock.mockReset();
  nav.push.mockReset();
  nav.replace.mockReset();
  window.sessionStorage.clear();
  api = apiStub(fetchMock);
});
afterEach(cleanup);

function wrap() {
  const client = new QueryClient({
    defaultOptions: { queries: { retry: false } },
  });
  render(
    <QueryClientProvider client={client}>
      <NextIntlClientProvider locale="en" messages={membersMessages(en)}>
        <TodayTargetsCard primary={member} />
      </NextIntlClientProvider>
    </QueryClientProvider>,
  );
}

const card = () => screen.findByTestId("home-card-today_targets");

describe("TodayTargetsCard", () => {
  it("renders golden g1_build_muscle targets", async () => {
    api
      .on("GET", "/v1/targets", targetsFixture("g1_build_muscle"))
      .on("GET", "/v1/meals/summary", summary());
    wrap();
    const c = await card();
    expect(await within(c).findByText(/of 2,760 kcal/)).toBeTruthy();
    expect(within(c).getByTestId("target-energy").textContent).toContain(
      "800 kcal of 2,760 kcal",
    );
    expect(within(c).getByTestId("target-protein").textContent).toContain(
      "40 g of 112 g",
    );
    // Fat and carbs: the target only.
    expect(within(c).getByTestId("target-fat").textContent).toContain("77 g");
    expect(within(c).getByTestId("target-carbs").textContent).toContain(
      "405 g",
    );
  });

  it("status none shows setup CTA and skip", async () => {
    api.on("GET", "/v1/targets", targetsFixture("none"));
    wrap();
    const c = await card();
    const cta = await within(c).findByRole("link", {
      name: en.targets.setup_cta,
    });
    expect(cta.getAttribute("href")).toBe("/en/guide/setup");
    await userEvent.click(
      within(c).getByRole("button", { name: en.targets.skip }),
    );
    expect(screen.queryByTestId("home-card-today_targets")).toBeNull();
  });

  it("consent_required shows the consent card, not a redirect", async () => {
    const handler = vi.fn();
    const off = setConsentRequiredHandler(handler);
    api
      .on(
        "GET",
        "/v1/targets",
        json(403, envelope("consent_required", { purposes: ["health_data"] })),
      )
      .on("GET", "/v1/consents", consentStates({ terms: true }));
    wrap();
    const c = await card();
    expect(await within(c).findByText(en.diary.targets_consent)).toBeTruthy();
    // The global consent handler (a redirect to the consent screen) is not used.
    expect(handler).not.toHaveBeenCalled();
    expect(nav.push).not.toHaveBeenCalled();
    expect(nav.replace).not.toHaveBeenCalled();
    await userEvent.click(
      within(c).getByRole("button", { name: en.consent.agree }),
    );
    expect(await screen.findByTestId("consent-dialog")).toBeTruthy();
    expect(within(c).getByTestId("eye-toggle")).toBeTruthy();
    off();
  });

  it("consent withdrawn: the eye sends hide_all, then show, tracking its last value", async () => {
    api
      .on(
        "GET",
        "/v1/targets",
        json(403, envelope("consent_required", { purposes: ["health_data"] })),
      )
      .on("GET", "/v1/consents", consentStates({ terms: true }))
      .on("PUT", "/v1/targets/display", { numbers_display: "hide_all" });
    wrap();
    const c = await card();
    const eye = await within(c).findByTestId("eye-toggle");
    await userEvent.click(eye);
    await waitFor(() =>
      expect(api.callsTo("PUT", "/v1/targets/display")).toHaveLength(1),
    );
    await waitFor(() =>
      expect((eye as HTMLButtonElement).disabled).toBe(false),
    );
    await userEvent.click(eye);
    await waitFor(() =>
      expect(api.callsTo("PUT", "/v1/targets/display")).toHaveLength(2),
    );
    const bodies = api
      .callsTo("PUT", "/v1/targets/display")
      .map((x) => (x.body as { numbers_display: string }).numbers_display);
    expect(bodies).toEqual(["hide_all", "show"]);
  });

  it("eye toggle hides every number in one tap", async () => {
    let display = "show";
    api
      .on("GET", "/v1/targets", () =>
        json(
          200,
          targetsFixture(
            display === "show" ? "g1_build_muscle" : "g1_hide_all",
          ),
        ),
      )
      .on("PUT", "/v1/targets/display", (call) => {
        display = (call.body as { numbers_display: string }).numbers_display;
        return json(200, { numbers_display: display });
      })
      .on("GET", "/v1/meals/summary", () =>
        json(
          200,
          display === "show"
            ? summary()
            : summary({
                totals: {
                  energy_kcal: null,
                  sugars_g: null,
                  salt_g: null,
                  protein_g: null,
                },
                numbers_hidden: { energy: true, macros: true },
              }),
        ),
      );
    wrap();
    const c = await card();
    await within(c).findByTestId("target-energy");
    await userEvent.click(within(c).getByTestId("eye-toggle"));
    await waitFor(() =>
      expect(api.callsTo("PUT", "/v1/targets/display")[0]?.body).toEqual({
        numbers_display: "hide_all",
      }),
    );
    await waitFor(() =>
      expect(within(c).queryByTestId("target-energy")).toBeNull(),
    );
    expect(within(c).getByTestId("numbers-hidden-note").textContent).toBe(
      en.diary.hidden_numbers,
    );
    expect(c.textContent ?? "").not.toMatch(/\d/);
    // Tapping again shows the numbers.
    await userEvent.click(within(c).getByTestId("eye-toggle"));
    await waitFor(() =>
      expect(api.callsTo("PUT", "/v1/targets/display")[1]?.body).toEqual({
        numbers_display: "show",
      }),
    );
    await within(c).findByTestId("target-energy");
  });

  it("un-hiding rate limited shows the standard error copy", async () => {
    api
      .on("GET", "/v1/targets", targetsFixture("g1_hide_all"))
      .on("GET", "/v1/meals/summary", summary())
      .on("PUT", "/v1/targets/display", () =>
        json(429, {
          error: { code: "rate_limited", message_key: "error.rate_limited" },
        }),
      );
    wrap();
    const c = await card();
    await userEvent.click(await within(c).findByTestId("eye-toggle"));
    expect((await within(c).findByRole("alert")).textContent).toBe(
      en.error.rate_limited,
    );
  });

  it("toggling refetches targets and settings", async () => {
    let display = "show";
    api
      .on("GET", "/v1/targets", () =>
        json(200, targetsFixture("g1_build_muscle")),
      )
      .on("GET", "/v1/targets/settings", () => json(200, null))
      .on("GET", "/v1/meals/summary", summary())
      .on("PUT", "/v1/targets/display", () => {
        display = "hide_all";
        return json(200, {
          member_id: "m1",
          numbers_display: display,
          summary_view: "remaining",
          updated_at: "2026-11-07T00:00:00Z",
        });
      });
    wrap();
    const c = await card();
    await within(c).findByTestId("target-energy");
    const before = api.callsTo("GET", "/v1/targets").length;
    await userEvent.click(within(c).getByTestId("eye-toggle"));
    await waitFor(() =>
      expect(api.callsTo("GET", "/v1/targets").length).toBeGreaterThan(before),
    );
  });

  it("hide_energy shows macros but no kcal", async () => {
    api.on("GET", "/v1/targets", targetsFixture("g1_hide_energy")).on(
      "GET",
      "/v1/meals/summary",
      summary({
        totals: {
          energy_kcal: null,
          sugars_g: 20,
          salt_g: 3,
          protein_g: 40,
        },
        numbers_hidden: { energy: true, macros: false },
      }),
    );
    wrap();
    const c = await card();
    expect(await within(c).findByTestId("target-protein")).toBeTruthy();
    expect(within(c).getByTestId("target-fat").textContent).toContain("77 g");
    expect(within(c).queryByTestId("target-energy")).toBeNull();
    expect(c.textContent ?? "").not.toContain("kcal");
  });

  it("incomplete energy shows the grey chip", async () => {
    api.on("GET", "/v1/targets", targetsFixture("g1_build_muscle")).on(
      "GET",
      "/v1/meals/summary",
      summary({
        totals: { energy_kcal: 0, sugars_g: 0, salt_g: 0, protein_g: 40 },
        incomplete: {
          energy_kcal: true,
          sugars_g: false,
          salt_g: false,
          protein_g: false,
        },
      }),
    );
    wrap();
    const c = await card();
    const chip = await within(c).findByTestId("target-energy-incomplete");
    expect(chip.textContent).toBe(en.diary.incomplete);
    // An unknown eaten total is never "0 of": only the target shows.
    expect(within(c).getByTestId("target-energy").textContent).not.toContain(
      "0 kcal of",
    );
  });

  it("over target renders the API numbers with no client comparison", async () => {
    api.on("GET", "/v1/targets", targetsFixture("g1_build_muscle")).on(
      "GET",
      "/v1/meals/summary",
      summary({
        totals: {
          energy_kcal: 3000,
          sugars_g: 20,
          salt_g: 3,
          protein_g: 40,
        },
      }),
    );
    wrap();
    const c = await card();
    const row = await within(c).findByTestId("target-energy");
    await waitFor(() => expect(row.textContent).toContain("3,000 kcal of"));
    expect(row.dataset.over).toBeUndefined();
    expect(row.textContent).toContain("3,000 kcal of 2,760 kcal");
    expect(row.textContent).not.toMatch(/over/i);
    expect(row.innerHTML).not.toMatch(/danger|error|red|warning/);
  });

  it("disclaimer and pending review shown", async () => {
    api
      .on("GET", "/v1/targets", targetsFixture("g1_build_muscle"))
      .on("GET", "/v1/meals/summary", summary());
    wrap();
    const c = await card();
    expect(await within(c).findByText(en.diary.disclaimer)).toBeTruthy();
    expect(within(c).getByText(en.targets.pending_review)).toBeTruthy();
  });

  it("other statuses show their message", async () => {
    api.on("GET", "/v1/targets", targetsFixture("g6_minor"));
    wrap();
    const c = await card();
    expect(await within(c).findByText(en.targets.minor)).toBeTruthy();
    expect(within(c).queryByTestId("target-energy")).toBeNull();
  });
});
