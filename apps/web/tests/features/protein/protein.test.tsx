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
import { GradeChip } from "@/features/analysis/components/GradeChip";
import { ProteinFacts } from "@/features/analysis/components/ProteinFacts";
import { MemberForm } from "@/features/members/components/MemberForm";
import type { CompareOut } from "@/features/product/api/products";
import { Alternatives } from "@/features/product/components/Alternatives";
import { CompareTable } from "@/features/product/components/CompareTable";
import { PublicProduct } from "@/features/product/components/PublicProduct";
import { SearchBox } from "@/features/product/components/SearchBox";
import { ProteinScreen } from "@/features/protein/components/ProteinScreen";
import { pricePerScoop } from "@/features/protein/lib/pricePerScoop";
import {
  clientMessages,
  membersMessages,
  resultMessages,
} from "@/i18n/client-messages";
import { analyzeResponse, MESSAGES } from "../../support/analyze-fixtures";
import { apiStub, consentStates, envelope, json } from "../../support/api-stub";

// Plan 9 Task 14: the same nine cases as Android's Task 11, named
// identically, plus the public page.

const router = vi.hoisted(() => ({ push: vi.fn(), replace: vi.fn() }));
vi.mock("next/navigation", () => ({
  usePathname: () => "/en/protein",
  useRouter: () => router,
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
const track = vi.hoisted(() => vi.fn());
vi.mock("@/lib/analytics", () => ({ track }));
const fetchMock = vi.hoisted(() => {
  const fn = vi.fn();
  globalThis.fetch = fn as unknown as typeof fetch;
  return fn;
});

const en = MESSAGES.en;
const ROOT = join(process.cwd(), "../../packages/test-fixtures");
const PRIMARY = "a0000000-0000-4000-8000-000000000001";
const SOURCE = "c1000000-0000-4000-8000-000000000001";
let api: ReturnType<typeof apiStub>;

beforeEach(() => {
  fetchMock.mockReset();
  track.mockReset();
  router.push.mockReset();
  localStorage.clear();
  sessionStorage.clear();
  api = apiStub(fetchMock);
});
afterEach(cleanup);

function wrap(ui: ReactNode, messages = resultMessages(en)) {
  const client = new QueryClient({
    defaultOptions: { queries: { retry: false } },
  });
  const r = render(
    <QueryClientProvider client={client}>
      <NextIntlClientProvider locale="en" messages={messages}>
        {ui}
      </NextIntlClientProvider>
    </QueryClientProvider>,
  );
  return { client, ...r };
}

const side = (over: Record<string, unknown> = {}) => ({
  attribution: null,
  barcode: null,
  brand: null,
  grade: "B" as const,
  high_in: [],
  member_status: null,
  name: "Bar A",
  per_100g: {
    energy_kcal: 400,
    protein_g: 30,
    sugars_g: 10,
    salt_g: 0.5,
    sat_fat_g: 2,
    fiber_g: 3,
    fat_g: 10,
    carbs_g: 40,
    sodium_mg: 200,
  },
  product_id: SOURCE,
  serving_size_g: 40,
  protein_per_serving_g: 12,
  protein_per_100kcal: 7.5,
  sugars_per_serving_g: 4,
  ...over,
});

const compareData = (): CompareOut => ({
  a: side(),
  b: side({
    name: "Bar B",
    product_id: "c1000000-0000-4000-8000-000000000002",
    serving_size_g: null,
    protein_per_serving_g: null,
    protein_per_100kcal: 9.1,
    sugars_per_serving_g: null,
  }),
  better: {
    grade: "same",
    energy_kcal: "same",
    sugars_g: "same",
    salt_g: "same",
    sat_fat_g: "same",
    protein_g: "same",
    fiber_g: "same",
    protein_per_serving_g: "unknown",
    protein_per_100kcal: "b",
    sugars_per_serving_g: "unknown",
  },
});

describe("protein guide (T14)", () => {
  it("protein facts row shows dash for null", () => {
    wrap(
      <ProteinFacts
        report={{
          protein: {
            per_100g: 10,
            per_serving: null,
            per_100kcal: null,
            serving_size_g: null,
          },
          sweeteners: [],
          caffeine: [],
        }}
      />,
    );
    const facts = screen.getByTestId("protein-facts");
    const row = (k: string) =>
      within(facts).getByTestId(`protein-${k}`).textContent ?? "";
    expect(row("per_100g")).toContain("10 g");
    // Missing is "not on the label" (the web's dash), never 0.
    for (const k of ["per_serving", "per_100kcal"]) {
      expect(row(k)).toContain(en.protein.not_on_label);
      expect(row(k)).not.toMatch(/\b0\b/);
    }
  });

  it("protein facts list sweeteners and caffeine from the report", () => {
    const whey = analyzeResponse("whey_powder");
    wrap(<ProteinFacts report={whey.report} />);
    const facts = screen.getByTestId("protein-facts");
    expect(
      within(facts).getByTestId("protein-per_serving").textContent,
    ).toContain("24 g");
    expect(
      within(facts).getByTestId("protein-per_100kcal").textContent,
    ).toContain("18.4 g");
    expect(within(facts).getByText(en.report.sweeteners)).toBeTruthy();
    expect(within(facts).getByText("sucralose")).toBeTruthy();
    expect(within(facts).queryByText(en.report.caffeine)).toBeNull();
  });

  it("supplement shows not graded label", () => {
    const whey = analyzeResponse("whey_powder");
    const ns = whey.report.nutriscore as { grade: null; reason: string };
    wrap(<GradeChip grade={ns.grade} reason={ns.reason} />);
    expect(screen.getByText(en.nutriscore.not_scored_supplement)).toBeTruthy();
    expect(screen.queryByTestId("grade-tile")).toBeNull();
    expect(screen.queryByText(en.nutriscore.insufficient_data)).toBeNull();
  });

  it("price per scoop matches shared fixture", () => {
    const fx = JSON.parse(
      readFileSync(join(ROOT, "protein/price_per_scoop.json"), "utf8"),
    ) as {
      cases: {
        name: string;
        price: number | null;
        pack_size_g: number | null;
        serving_size_g: number | null;
        expected: number | null;
      }[];
    };
    expect(fx.cases.length).toBeGreaterThan(5);
    for (const c of fx.cases)
      expect(
        pricePerScoop(c.price, c.pack_size_g, c.serving_size_g),
        c.name,
      ).toBe(c.expected);
  });

  it("price is never persisted or sent", async () => {
    const setItem = vi.spyOn(Storage.prototype, "setItem");
    const { unmount } = wrap(<CompareTable data={compareData()} />);
    const priceA = screen.getByTestId("price-a");
    await userEvent.type(
      within(priceA).getByLabelText(en.protein.price_label),
      "2499",
    );
    await userEvent.type(
      within(priceA).getByLabelText(en.protein.pack_size_label),
      "1000",
    );
    // 2499 x 40 / 1000 = 99.96
    expect(within(priceA).getByTestId("price-result").textContent).toContain(
      "99.96",
    );
    expect(within(priceA).getByText(en.protein.price_note)).toBeTruthy();
    // Side B has no serving size: no price per scoop.
    const priceB = screen.getByTestId("price-b");
    await userEvent.type(
      within(priceB).getByLabelText(en.protein.price_label),
      "1500",
    );
    await userEvent.type(
      within(priceB).getByLabelText(en.protein.pack_size_label),
      "500",
    );
    expect(within(priceB).queryByTestId("price-result")).toBeNull();
    // Nothing left the component: no request, no storage, no URL, no event.
    expect(fetchMock).not.toHaveBeenCalled();
    expect(setItem).not.toHaveBeenCalled();
    expect(localStorage.length + sessionStorage.length).toBe(0);
    expect(window.location.href).not.toContain("2499");
    expect(track).not.toHaveBeenCalled();
    unmount();
    // Rebuilt: the price is gone.
    wrap(<CompareTable data={compareData()} />);
    expect(
      (
        within(screen.getByTestId("price-a")).getByLabelText(
          en.protein.price_label,
        ) as HTMLInputElement
      ).value,
    ).toBe("");
    setItem.mockRestore();
  });

  it("higher protein toggle requests sort=protein with member", async () => {
    api.on("GET", `/v1/products/${SOURCE}/alternatives`, (c) =>
      json(
        200,
        c.query.get("sort") === "protein"
          ? {
              items: [
                {
                  ...side({ name: "More protein bar" }),
                  grade: "A",
                  image_url: null,
                  member_status: "ok",
                  protein_g: 35,
                  sugars_g: 5,
                },
              ],
              reason: "ok",
            }
          : { items: [], reason: "no_better_found" },
      ),
    );
    wrap(
      <Alternatives
        productRef={{ productId: SOURCE }}
        members={[
          { id: PRIMARY, name: "Asha", isPrimary: true, relation: "self" },
        ]}
      />,
    );
    await screen.findByTestId("alternatives-empty");
    await userEvent.click(
      screen.getByRole("radio", { name: en.protein.sort_higher }),
    );
    expect(await screen.findByText("More protein bar")).toBeTruthy();
    const calls = api.callsTo("GET", `/v1/products/${SOURCE}/alternatives`);
    expect(calls.at(-1)?.query.get("sort")).toBe("protein");
    expect(calls.at(-1)?.query.get("member_id")).toBe(PRIMARY);
    expect(calls[0]?.query.get("sort")).toBeNull();
    const item = screen.getByTestId("alternative");
    expect(within(item).getByText(en.protein.per_100kcal)).toBeTruthy();
    expect(within(item).getByText("7.5 g")).toBeTruthy();
  });

  it("higher protein: the API's reasons for no options are shown", async () => {
    api.on("GET", `/v1/products/${SOURCE}/alternatives`, (c) =>
      json(200, {
        items: [],
        reason:
          c.query.get("sort") === "protein"
            ? "source_protein_unknown"
            : "source_supplement",
      }),
    );
    wrap(
      <Alternatives
        productRef={{ productId: SOURCE }}
        members={[
          { id: PRIMARY, name: "Asha", isPrimary: true, relation: "self" },
        ]}
      />,
    );
    expect(
      await screen.findByText(en.alternatives.reason.source_supplement),
    ).toBeTruthy();
    await userEvent.click(
      screen.getByRole("radio", { name: en.protein.sort_higher }),
    );
    expect(
      await screen.findByText(en.alternatives.reason.source_protein_unknown),
    ).toBeTruthy();
  });

  it("search protein sort", async () => {
    api.on("GET", "/v1/products/search", (c) =>
      json(200, [
        {
          attribution: null,
          barcode: null,
          brand: null,
          grade: "A",
          member_status: c.query.get("sort") === "protein" ? "caution" : null,
          name: "Paneer",
          off_degraded: false,
          product_id: SOURCE,
          protein_g: 18,
          protein_per_100kcal: 6.2,
          source: "ours",
        },
      ]),
    );
    wrap(<SearchBox debounceMs={0} memberId={PRIMARY} />);
    await userEvent.type(screen.getByRole("searchbox"), "paneer");
    await screen.findByText("Paneer");
    expect(
      api.callsTo("GET", "/v1/products/search")[0]?.query.get("sort"),
    ).toBeNull();
    await userEvent.click(
      screen.getByRole("radio", { name: en.protein.sort_higher }),
    );
    await waitFor(() =>
      expect(
        api.callsTo("GET", "/v1/products/search").at(-1)?.query.get("sort"),
      ).toBe("protein"),
    );
    const last = api.callsTo("GET", "/v1/products/search").at(-1);
    expect(last?.query.get("member_id")).toBe(PRIMARY);
    expect(last?.query.get("q")).toBe("paneer");
    expect(await screen.findByText(en.status.caution)).toBeTruthy();
  });

  it("protein screen lists swaps for logged items", async () => {
    api
      .on("GET", "/v1/members", [
        {
          id: PRIMARY,
          name: "Asha",
          relation: "self",
          birth_year: 1990,
          sex: null,
          height_cm: null,
          weight_kg: 70,
          diet: "non_veg",
          allergens: [],
          conditions: [],
          custom_alerts: [],
          goal: "build_muscle",
          is_primary: true,
        },
      ])
      .on("GET", "/v1/meals/summary", {
        member_id: PRIMARY,
        period: "day",
        start: "2026-11-04",
        end: "2026-11-04",
        totals: { energy_kcal: 400, sugars_g: 10, salt_g: 1, protein_g: 30 },
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
        bands: {
          kcal: "unknown",
          protein_g: "ok",
          salt_g: "ok",
          sugar_g: "ok",
        },
        days: [],
        pending_clinician_review: true,
        protein_left_g: 82,
      })
      .on("GET", "/v1/meals", [
        {
          attribution: null,
          barcode: null,
          client_id: null,
          eaten_at: "2026-11-04T08:00:00+05:30",
          grade: "C",
          grams: 40,
          id: "d0000000-0000-4000-8000-000000000001",
          member_id: PRIMARY,
          nutrients: {},
          product_id: SOURCE,
          product_name: "Oat bar",
        },
      ])
      .on("GET", `/v1/products/${SOURCE}/alternatives`, {
        items: [
          {
            ...side({ name: "Protein oat bar" }),
            grade: "B",
            image_url: null,
            member_status: "ok",
            protein_g: 30,
            sugars_g: 8,
          },
        ],
        reason: "ok",
      });
    wrap(<ProteinScreen />);
    expect(await screen.findByText("Oat bar")).toBeTruthy();
    await userEvent.click(
      screen.getByRole("button", { name: en.protein.swaps_title }),
    );
    expect(await screen.findByText("Protein oat bar")).toBeTruthy();
    const call = api.callsTo("GET", `/v1/products/${SOURCE}/alternatives`)[0];
    expect(call?.query.get("sort")).toBe("protein");
    expect(call?.query.get("member_id")).toBe(PRIMARY);
    expect(screen.getByText(en.protein.kidney_note)).toBeTruthy();
    expect(
      screen.getAllByText(en.common.disclaimer, { exact: false }).length,
    ).toBeGreaterThan(0);
    expect(track).not.toHaveBeenCalled();
  });

  it("compare shows protein rows and markers", () => {
    wrap(<CompareTable data={compareData()} />);
    const row = (k: string) => screen.getByTestId(`row-${k}`);
    expect(
      within(row("protein_per_serving_g")).getByText(
        en.protein.compare.protein_serving,
      ),
    ).toBeTruthy();
    expect(
      within(row("protein_per_serving_g"))
        .getAllByTestId(/^cell-/)
        .map((c) => c.dataset.better),
    ).toEqual(["false", "false"]);
    expect(
      within(row("protein_per_serving_g")).getByText(en.compare.better.unknown),
    ).toBeTruthy();
    expect(
      within(row("protein_per_100kcal"))
        .getAllByTestId(/^cell-/)
        .map((c) => c.dataset.better),
    ).toEqual(["false", "true"]);
    expect(
      within(row("sugars_per_serving_g")).getByText(en.protein.compare.sugar),
    ).toBeTruthy();
    // Missing per-serving values are "not on the label", never 0.
    expect(
      within(
        within(row("sugars_per_serving_g")).getByTestId("cell-b"),
      ).getByText(en.result.not_on_label),
    ).toBeTruthy();
  });

  it("member form offers build muscle to adults only", async () => {
    api
      .on(
        "GET",
        "/v1/consents",
        consentStates({ terms: true, health_data: true }),
      )
      .on(
        "POST",
        "/v1/members",
        json(422, envelope("validation_error", { fields: ["body.goal"] })),
      );
    wrap(<MemberForm />, membersMessages(en));
    const goal = screen.getByLabelText(
      en.members.form.goal,
    ) as HTMLSelectElement;
    const offered = () => [...goal.options].map((o) => o.value);
    // No birth year yet: not offered (adults only, by birth year).
    expect(offered()).not.toContain("build_muscle");
    await userEvent.type(screen.getByLabelText(en.members.form.name), "Ravi");
    await userEvent.selectOptions(
      screen.getByLabelText(en.members.form.relation),
      "child",
    );
    const birthYear = screen.getByLabelText(en.members.form.birth_year);
    // A child is never offered the goal.
    await userEvent.type(birthYear, String(new Date().getFullYear() - 10));
    expect(offered()).not.toContain("build_muscle");
    // An adult is; the API's 422 body.goal is shown on the goal field.
    await userEvent.clear(birthYear);
    await userEvent.type(birthYear, "1990");
    expect(offered()).toContain("build_muscle");
    expect([...goal.options].map((o) => o.textContent)).toContain(
      en.members.goal.build_muscle,
    );
    await userEvent.selectOptions(goal, "build_muscle");
    await userEvent.click(
      screen.getByRole("button", { name: en.members.form.save }),
    );
    await waitFor(() =>
      expect(api.callsTo("POST", "/v1/members")).toHaveLength(1),
    );
    expect(
      (
        api.callsTo("POST", "/v1/members")[0]?.body as
          | { goal?: string }
          | undefined
      )?.goal,
    ).toBe("build_muscle");
    expect(
      await screen.findByText(en.members.goal.build_muscle_adults_only),
    ).toBeTruthy();
    expect(goal.getAttribute("aria-invalid")).toBe("true");
    expect(router.push).not.toHaveBeenCalled();
  });

  it("a chosen build muscle stays visible and is refused for a minor", async () => {
    api.on(
      "GET",
      "/v1/consents",
      consentStates({ terms: true, health_data: true }),
    );
    wrap(<MemberForm />, membersMessages(en));
    const goal = screen.getByLabelText(
      en.members.form.goal,
    ) as HTMLSelectElement;
    await userEvent.type(screen.getByLabelText(en.members.form.name), "Ravi");
    await userEvent.selectOptions(
      screen.getByLabelText(en.members.form.relation),
      "child",
    );
    const birthYear = screen.getByLabelText(en.members.form.birth_year);
    await userEvent.type(birthYear, "1990");
    await userEvent.selectOptions(goal, "build_muscle");
    await userEvent.clear(birthYear);
    await userEvent.type(birthYear, String(new Date().getFullYear() - 10));
    // Kept so it can be changed, but the form refuses it before saving.
    expect([...goal.options].map((o) => o.value)).toContain("build_muscle");
    await userEvent.click(
      screen.getByRole("button", { name: en.members.form.save }),
    );
    expect(
      await screen.findByText(en.members.goal.build_muscle_adults_only),
    ).toBeTruthy();
    expect(api.callsTo("POST", "/v1/members")).toHaveLength(0);
  });

  it("public page shows protein facts without member data", () => {
    const pub = JSON.parse(
      readFileSync(join(ROOT, "responses/public/whey_powder.json"), "utf8"),
    );
    const { container } = wrap(
      <PublicProduct data={pub} barcode="8901234567890" />,
      clientMessages(en),
    );
    const facts = screen.getByTestId("protein-facts");
    expect(
      within(facts).getByTestId("protein-per_serving").textContent,
    ).toContain("24 g");
    expect(screen.getByText(en.nutriscore.not_scored_supplement)).toBeTruthy();
    // Generic facts only: no member, status or verdict anywhere.
    expect(container.querySelector("[data-verdict]")).toBeNull();
    expect(screen.queryByTestId("verdict-card")).toBeNull();
    expect(fetchMock).not.toHaveBeenCalled();
  });
});
