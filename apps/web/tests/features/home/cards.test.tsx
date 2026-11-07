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
import type { ReactNode } from "react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { HomeView } from "@/features/home/components/HomeView";
import type { Summary } from "@/features/meals/api/meals";
import type { MemberOut } from "@/features/members/api/members";
import type { UserType } from "@/features/modes/layouts";
import { ProteinProgress } from "@/features/protein/components/ProteinProgress";
import { membersMessages } from "@/i18n/client-messages";
import { MESSAGES } from "../../support/analyze-fixtures";
import { apiStub, envelope, json } from "../../support/api-stub";
import { targetsFixture } from "../../support/targets-fixtures";

// Plan 9 Task 13: Home cards come from layouts.json, in order.

vi.mock("next/navigation", () => ({
  usePathname: () => "/en/home",
  useRouter: () => ({ push: vi.fn(), replace: vi.fn() }),
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

type Layouts = {
  modes: Record<string, { tabs: string[]; home_cards: string[] }>;
};
const FIXTURE = JSON.parse(
  readFileSync(
    join(process.cwd(), "../../packages/test-fixtures/modes/layouts.json"),
    "utf8",
  ),
) as Layouts;
const MODES = Object.keys(FIXTURE.modes) as UserType[];
const en = MESSAGES.en;
const PRIMARY = "a0000000-0000-4000-8000-000000000001";

const member = (over: Partial<MemberOut> = {}): MemberOut => ({
  id: PRIMARY,
  name: "Asha",
  relation: "self",
  birth_year: 1990,
  sex: null,
  height_cm: null,
  weight_kg: 70,
  body_fat_pct: null,
  diet: "non_veg",
  allergens: [],
  conditions: [],
  custom_alerts: [],
  goal: "build_muscle",
  is_primary: true,
  ...over,
});

const summary = (over: Partial<Summary> = {}): Summary => ({
  member_id: PRIMARY,
  period: "day",
  start: "2026-11-04",
  end: "2026-11-04",
  totals: { energy_kcal: 900, sugars_g: 20, salt_g: 3, protein_g: 40 },
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
  ...over,
});

let api: ReturnType<typeof apiStub>;
beforeEach(() => {
  fetchMock.mockReset();
  api = apiStub(fetchMock);
});
afterEach(cleanup);

function wrap(ui: ReactNode) {
  const client = new QueryClient({
    defaultOptions: { queries: { retry: false } },
  });
  render(
    <QueryClientProvider client={client}>
      <NextIntlClientProvider locale="en" messages={membersMessages(en)}>
        {ui}
      </NextIntlClientProvider>
    </QueryClientProvider>,
  );
}

function home(mode: UserType, members: MemberOut[], types = [mode]) {
  api
    .on("GET", "/v1/me", { display_name: "Asha", email: null })
    .on("GET", "/v1/me/user-types", {
      types,
      follow_ups: {},
      active_type: mode,
      answered: true,
      answered_at: null,
      prefill: null,
    })
    .on("GET", "/v1/members", members)
    .on("GET", "/v1/meals/summary", summary())
    .on("GET", "/v1/meals/week_counts", {
      start: "2026-10-29",
      end: "2026-11-04",
      scans: 3,
      logged: 5,
    })
    .on("GET", "/v1/meals", []);
  wrap(<HomeView />);
}

const cardOrder = () =>
  screen
    .getAllByTestId(/^home-card-/)
    .map((c) => c.dataset.testid?.replace("home-card-", ""));

describe("home cards (T13)", () => {
  it.each(MODES)("home cards follow layout order (%s)", async (mode) => {
    home(mode, [member()]);
    const want = FIXTURE.modes[mode]?.home_cards ?? [];
    await waitFor(() => expect(cardOrder()).toEqual(want));
    // The scan CTAs sit above the cards and are not cards.
    const scan = screen.getByRole("link", { name: new RegExp(en.scan.title) });
    const first = screen.getAllByTestId(/^home-card-/)[0] as HTMLElement;
    expect(
      scan.compareDocumentPosition(first) & Node.DOCUMENT_POSITION_FOLLOWING,
    ).toBeTruthy();
  });

  it.each(MODES)(
    "allergy_check first in every mode when a member has allergens (%s)",
    async (mode) => {
      home(mode, [
        member(),
        member({
          id: "b0000000-0000-4000-8000-000000000002",
          name: "Ravi",
          relation: "child",
          is_primary: false,
          allergens: ["peanut", "milk"],
        }),
      ]);
      const rest = (FIXTURE.modes[mode]?.home_cards ?? []).filter(
        (c) => c !== "allergy_check",
      );
      await waitFor(() =>
        expect(cardOrder()).toEqual(["allergy_check", ...rest]),
      );
      const card = screen.getByTestId("home-card-allergy_check");
      expect(
        await within(card).findByText(
          `Ravi: ${en.allergen.peanut}, ${en.allergen.milk}`,
        ),
      ).toBeTruthy();
      expect(
        within(card).getByText(en.home.cards.allergy_check.unknown_note),
      ).toBeTruthy();
    },
  );

  it("allergy mode with no allergies offers to add them", async () => {
    home("allergy_diet", [member()]);
    const card = await screen.findByTestId("home-card-allergy_check");
    expect(
      await within(card).findByText(en.home.cards.allergy_check.none),
    ).toBeTruthy();
    expect(
      within(card)
        .getByRole("link", { name: en.home.cards.allergy_check.add_cta })
        .getAttribute("href"),
    ).toBe(`/en/members/${PRIMARY}`);
  });

  it("switcher and More sit in the Home header", async () => {
    home("gym", [member()], ["gym", "family"]);
    expect(
      await screen.findByRole("radiogroup", { name: en.modes.switcher_label }),
    ).toBeTruthy();
    await userEvent.click(screen.getByRole("button", { name: en.modes.more }));
    const dialog = screen.getByRole("dialog");
    expect(
      within(dialog)
        .getAllByRole("link")
        .map((l) => l.textContent),
    ).toEqual([
      en.nav.history,
      en.nav.family,
      en.nav.search,
      en.nav.how_we_score,
    ]);
  });

  it("today_targets: weight_loss shows the daily guide card first, from the API", async () => {
    api.on("GET", "/v1/targets", targetsFixture("g2_lose_adjusted"));
    home("weight_loss", [member({ goal: "weight_loss" })]);
    const card = await screen.findByTestId("home-card-today_targets");
    expect(cardOrder()[0]).toBe("today_targets");
    expect(
      await within(card).findByText(/of 1,540 kcal|1,540 kcal/),
    ).toBeTruthy();
  });

  it("today_protein: loading, then the API's progress and protein left", async () => {
    let resolve: (r: Response) => void = () => {};
    home("gym", [member()]);
    api.on(
      "GET",
      "/v1/meals/summary",
      () => new Promise<Response>((r) => (resolve = r)),
    );
    const card = await screen.findByTestId("home-card-today_protein");
    await waitFor(() =>
      expect(api.callsTo("GET", "/v1/meals/summary")).toHaveLength(1),
    );
    expect(within(card).getByRole("status").textContent).toBe(
      en.common.loading,
    );
    resolve(json(200, summary()));
    expect(
      await within(card).findByText(
        en.protein.progress.replace("{total}", "40").replace("{target}", "112"),
      ),
    ).toBeTruthy();
    expect(
      within(card).getByText(en.protein.left_today.replace("{left}", "72")),
    ).toBeTruthy();
    // The guide: the API's target and its g per kg basis, worded as a guide.
    expect(
      within(card).getByText(
        en.protein.guide.replace("{target}", "112").replace("{per_kg}", "1.6"),
      ),
    ).toBeTruthy();
  });

  it("today_protein: the guide basis is the API's g per kg, never derived", async () => {
    // 112 / 80 kg would read 1.4: the client must show the API's 1.6.
    home("gym", [member({ weight_kg: 80 })]);
    api.on("GET", "/v1/meals/summary", summary());
    const card = await screen.findByTestId("home-card-today_protein");
    expect(
      await within(card).findByText(
        en.protein.guide.replace("{target}", "112").replace("{per_kg}", "1.6"),
      ),
    ).toBeTruthy();
  });

  it("today_protein: no g per kg from the API shows no guide line", async () => {
    home("gym", [member()]);
    api.on(
      "GET",
      "/v1/meals/summary",
      summary({
        limits: {
          kcal: null,
          protein_target_g: 112,
          protein_g_per_kg: null,
          salt_g: 5,
          sugar_g: 25,
        },
      }),
    );
    const card = await screen.findByTestId("home-card-today_protein");
    await within(card).findByText(
      en.protein.progress.replace("{total}", "40").replace("{target}", "112"),
    );
    const guideStart = en.protein.guide.split("{target}")[0] ?? "";
    expect(within(card).queryByText(new RegExp(`^${guideStart}`))).toBeNull();
  });

  it("today_protein: an error offers a retry", async () => {
    home("gym", [member()]);
    api.on("GET", "/v1/meals/summary", (_c, n) =>
      n === 1 ? json(500, envelope("internal_error")) : json(200, summary()),
    );
    const card = await screen.findByTestId("home-card-today_protein");
    await userEvent.click(
      await within(card).findByRole("button", { name: en.common.retry }),
    );
    expect(
      await within(card).findByText(
        en.protein.left_today.replace("{left}", "72"),
      ),
    ).toBeTruthy();
  });

  it("today_protein: no target shows the note and a link to the member form", async () => {
    home("gym", [member({ weight_kg: null })]);
    api.on(
      "GET",
      "/v1/meals/summary",
      summary({
        limits: {
          kcal: null,
          protein_target_g: null,
          protein_g_per_kg: null,
          salt_g: 5,
          sugar_g: 25,
        },
        protein_left_g: null,
      }),
    );
    const card = await screen.findByTestId("home-card-today_protein");
    expect(await within(card).findByText(en.protein.no_target)).toBeTruthy();
    expect(
      within(card)
        .getByRole("link", { name: en.members.edit })
        .getAttribute("href"),
    ).toBe(`/en/members/${PRIMARY}`);
    // Calories are shown without a target.
    expect(within(card).getByText(en.summary.kcal_info)).toBeTruthy();
  });

  it("unknown protein band is never green", () => {
    wrap(
      <ProteinProgress
        locale="en"
        member={member()}
        summary={summary({
          totals: {
            energy_kcal: null,
            sugars_g: null,
            salt_g: null,
            protein_g: null,
          },
          incomplete: {
            energy_kcal: true,
            sugars_g: true,
            salt_g: true,
            protein_g: true,
          },
          bands: {
            kcal: "unknown",
            protein_g: "unknown",
            salt_g: "unknown",
            sugar_g: "unknown",
          },
          protein_left_g: null,
        })}
      />,
    );
    const badge = screen.getByTestId("band-badge");
    expect(badge.dataset.band).toBe("unknown");
    expect(document.querySelector('[data-band="ok"]')).toBeNull();
    expect(document.querySelector('[data-verdict="ok"]')).toBeNull();
    expect(screen.queryByTestId("protein-bar")).toBeNull();
    expect(document.body.innerHTML).not.toMatch(/verdict-ok|band-ok/);
  });

  it("today_sugar_salt shows the API bands; unknown is grey", async () => {
    home("health_condition", [member()]);
    api.on(
      "GET",
      "/v1/meals/summary",
      summary({
        bands: {
          kcal: "unknown",
          protein_g: "unknown",
          salt_g: "unknown",
          sugar_g: "near",
        },
        totals: { energy_kcal: 900, sugars_g: 20, salt_g: null, protein_g: 40 },
      }),
    );
    const card = await screen.findByTestId("home-card-today_sugar_salt");
    await waitFor(() =>
      expect(
        within(card)
          .getAllByTestId("band-badge")
          .map((b) => b.dataset.band),
      ).toEqual(["near", "unknown"]),
    );
  });

  it("family cards: members with Add member, and the week's count only", async () => {
    home("family", [
      member(),
      member({ id: "b1", name: "Dadi", relation: "parent", is_primary: false }),
    ]);
    const strip = await screen.findByTestId("home-card-family_strip");
    expect(await within(strip).findByText("Dadi")).toBeTruthy();
    expect(
      within(strip)
        .getByRole("link", { name: en.home.cards.family_strip.add })
        .getAttribute("href"),
    ).toBe("/en/members/new");
    const week = screen.getByTestId("home-card-weekly_family");
    expect(
      await within(week).findByText(
        en.home.cards.weekly_family.body.replace("{count}", "5"),
      ),
    ).toBeTruthy();
  });
});
