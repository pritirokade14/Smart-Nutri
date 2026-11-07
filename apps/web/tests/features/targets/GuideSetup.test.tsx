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
import type { MemberOut } from "@/features/members/api/members";
import { toPatch } from "@/features/members/lib/memberForm";
import type { TargetsOut } from "@/features/targets/api/targets";
import { GuideSetup } from "@/features/targets/components/GuideSetup";
import { membersMessages } from "@/i18n/client-messages";
import { MESSAGES } from "../../support/analyze-fixtures";
import { apiStub, consentStates, envelope, json } from "../../support/api-stub";
import { targetsFixture } from "../../support/targets-fixtures";

const nav = vi.hoisted(() => ({ push: vi.fn(), replace: vi.fn() }));
vi.mock("next/navigation", () => ({
  usePathname: () => "/en/guide/setup",
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
const member = (over: Partial<MemberOut> = {}): MemberOut => ({
  id: PRIMARY,
  name: "Asha",
  relation: "self",
  birth_year: 1990,
  sex: "female",
  height_cm: 165,
  weight_kg: 80,
  body_fat_pct: null,
  diet: "non_veg",
  allergens: [],
  conditions: [],
  custom_alerts: [],
  goal: "weight_loss",
  is_primary: true,
  ...over,
});

let api: ReturnType<typeof apiStub>;
beforeEach(() => {
  fetchMock.mockReset();
  nav.push.mockReset();
  nav.replace.mockReset();
  api = apiStub(fetchMock);
});
afterEach(cleanup);

/** The API with every route the setup needs; `preview` answers each preview. */
function setup(
  opts: {
    member?: MemberOut;
    preview?: TargetsOut | ((body: unknown) => Response);
    consents?: Parameters<typeof consentStates>[0];
  } = {},
) {
  const m = opts.member ?? member();
  const preview = opts.preview ?? targetsFixture("g2_lose_adjusted");
  api
    .on("GET", "/v1/members", [m])
    .on("GET", "/v1/targets/settings", json(200, null))
    .on(
      "GET",
      "/v1/consents",
      consentStates(opts.consents ?? { terms: true, health_data: true }),
    )
    .on("POST", "/v1/targets/preview", (call) =>
      typeof preview === "function" ? preview(call.body) : json(200, preview),
    )
    .on("PATCH", `/v1/members/${PRIMARY}`, { ...m })
    .on("PUT", "/v1/targets/settings", targetsFixture("g2_lose_adjusted"));
  const client = new QueryClient({
    defaultOptions: { queries: { retry: false } },
  });
  render(
    <QueryClientProvider client={client}>
      <NextIntlClientProvider locale="en" messages={membersMessages(en)}>
        <GuideSetup />
      </NextIntlClientProvider>
    </QueryClientProvider>,
  );
}

const step = async (id: "intro" | "about" | "activity" | "goal" | "guide") =>
  userEvent.click(await screen.findByTestId(`step-nav-${id}`));
const lastPreview = () =>
  api.callsTo("POST", "/v1/targets/preview").at(-1)?.body as {
    body: Record<string, unknown>;
    [k: string]: unknown;
  };
const bodyFat = () => screen.getByLabelText(en.targets.body_fat.label);
const text = (id: string) => screen.getByTestId(id).textContent ?? "";

describe("guide setup", () => {
  it("onboarding preselects show numbers", async () => {
    setup();
    const group = await screen.findByTestId("numbers-choice");
    const show = within(group).getByRole("radio", {
      name: en.settings.diary.numbers.show,
    }) as HTMLInputElement;
    expect(show.checked).toBe(true);
    expect(screen.getByText(en.targets.intro.body)).toBeTruthy();
  });

  it("body fat field shows the hint", async () => {
    setup();
    await step("about");
    expect(screen.getByText(en.targets.body_fat.hint)).toBeTruthy();
    expect(bodyFat().getAttribute("aria-describedby")).toContain("hint");
  });

  it("blank body fat is saved as unknown", async () => {
    setup();
    await step("guide");
    await userEvent.click(
      await screen.findByRole("button", { name: en.targets.save }),
    );
    await waitFor(() =>
      expect(api.callsTo("PATCH", `/v1/members/${PRIMARY}`)).toHaveLength(1),
    );
    const patch = api.callsTo("PATCH", `/v1/members/${PRIMARY}`)[0]
      ?.body as Record<string, unknown>;
    expect(patch.body_fat_pct).toBeNull();
    expect(patch.clear_body_fat_pct).toBe(false);
    // The preview sent body fat as unknown too, never 0.
    expect(lastPreview().body.body_fat_pct).toBeNull();
  });

  it("clearing a stored body fat sends clear flag", async () => {
    setup({ member: member({ body_fat_pct: 15 }) });
    await step("about");
    expect((bodyFat() as HTMLInputElement).value).toBe("15");
    await userEvent.clear(bodyFat());
    await step("guide");
    await userEvent.click(
      await screen.findByRole("button", { name: en.targets.save }),
    );
    await waitFor(() =>
      expect(api.callsTo("PATCH", `/v1/members/${PRIMARY}`)).toHaveLength(1),
    );
    const patch = api.callsTo("PATCH", `/v1/members/${PRIMARY}`)[0]
      ?.body as Record<string, unknown>;
    expect(patch.clear_body_fat_pct).toBe(true);
    expect(patch.body_fat_pct).toBeNull();
  });

  it("member save keeps body fat", () => {
    // An unrelated profile save (the member form) never sends the clear flag.
    const stored = member({ body_fat_pct: 15 });
    const patch = toPatch(
      { name: "Asha", relation: "self", birth_year: 1990 } as never,
      true,
      stored,
    );
    expect(patch.clear_body_fat_pct).toBe(false);
    expect(patch.body_fat_pct ?? null).toBeNull();
  });

  it("out-of-range body fat shows the API message", async () => {
    setup({
      preview: () =>
        json(422, envelope("body_fat_out_of_range", { min: 3, max: 70 })),
    });
    await step("about");
    await userEvent.type(bodyFat(), "2");
    await step("goal");
    // The error returns the user to the field, with the API's limits.
    expect(
      await screen.findByText("Please enter a number between 3 and 70."),
    ).toBeTruthy();
    expect(screen.getByTestId("step-about")).toBeTruthy();
  });

  it("guide step renders g2_lose_adjusted", async () => {
    setup();
    await step("guide");
    const rows = await screen.findByTestId("guide-rows");
    expect(rows.textContent).toContain("1,540 kcal");
    expect(rows.textContent).toContain("71 g");
    expect(rows.textContent).toContain("43 g");
    expect(rows.textContent).toContain("217 g");
    const how = screen.getByTestId("targets-explanation");
    expect(how.textContent).toContain(
      "Protein: 1.2 g per kg of an adjusted weight (59.3 kg)",
    );
    expect(screen.getByText(en.diary.disclaimer)).toBeTruthy();
    expect(screen.getByText(en.targets.pending_review)).toBeTruthy();
    expect(screen.getByText(en.protein.kidney_note)).toBeTruthy();
  });

  it("guide step shows lean basis for g11_lean_mass", async () => {
    setup({ preview: targetsFixture("g11_lean_mass") });
    await step("guide");
    const how = await screen.findByTestId("targets-explanation");
    expect(how.textContent).toContain("of lean mass (59.5 kg)");
    expect(how.querySelector('[data-line="protein"]')?.textContent).toBe(
      "Protein: 2 g per kg of lean mass (59.5 kg)",
    );
  });

  it("floor note renders for g4_floor in a neutral style", async () => {
    setup({ preview: targetsFixture("g4_floor") });
    await step("guide");
    const note = await screen.findByTestId("flag-notes");
    expect(note.textContent).toContain("1,200");
    expect(note.innerHTML).not.toMatch(/danger|error|red|warning/);
  });

  it("hidden floor note for g4_hide_all has no digits", async () => {
    setup({ preview: targetsFixture("g4_hide_all") });
    await step("guide");
    const note = await screen.findByTestId("flag-notes");
    expect(note.textContent).toContain(en.targets.flag.floor_applied_hidden);
    expect(note.textContent).not.toMatch(/\d/);
  });

  it("minor shows adults-only message", async () => {
    setup({ preview: targetsFixture("g6_minor") });
    await step("guide");
    expect(await screen.findByText(en.targets.minor)).toBeTruthy();
    expect(
      (
        screen.getByRole("button", {
          name: en.targets.save,
        }) as HTMLButtonElement
      ).disabled,
    ).toBe(true);
  });

  it("pregnancy shows paused message", async () => {
    setup({ preview: targetsFixture("pregnancy") });
    await step("guide");
    expect(await screen.findByText(en.targets.pregnancy.paused)).toBeTruthy();
    expect(screen.queryByTestId("guide-rows")).toBeNull();
  });

  it("prefer not to say on pregnancy is sent as true", async () => {
    setup();
    await step("goal");
    await userEvent.click(
      screen.getByRole("radio", { name: en.targets.pregnancy.prefer_not }),
    );
    await waitFor(() =>
      expect(lastPreview().pregnant_or_breastfeeding).toBe(true),
    );
  });

  it("underweight lose offers maintenance", async () => {
    setup({
      preview: (body) =>
        (body as { direction: string }).direction === "lose"
          ? json(422, envelope("goal_not_allowed_underweight"))
          : json(200, targetsFixture("g3_eat_healthy")),
    });
    await step("goal");
    await userEvent.click(
      screen.getByRole("radio", { name: en.targets.direction.lose }),
    );
    expect(await screen.findByText(en.targets.underweight)).toBeTruthy();
    const maintain = (await screen.findByRole("radio", {
      name: en.targets.direction.maintain,
    })) as HTMLInputElement;
    await waitFor(() => expect(maintain.checked).toBe(true));
  });

  it("needs_height_cm highlights height", async () => {
    setup({ preview: targetsFixture("needs_height_cm") });
    await step("guide");
    expect(await screen.findByText(/Add .*to see a daily guide/)).toBeTruthy();
    await userEvent.click(
      screen.getByRole("button", { name: en.targets.step.about }),
    );
    const height = await screen.findByLabelText(en.members.form.height_cm);
    expect(height.getAttribute("aria-invalid")).toBe("true");
    expect(
      screen
        .getByLabelText(en.members.form.weight_kg)
        .getAttribute("aria-invalid"),
    ).toBeNull();
  });

  it("rate chips show kg from rate_options", async () => {
    const fake = {
      ...targetsFixture("g2_lose_adjusted"),
      rate_options: [
        { kg_per_week: 0.37, pct_bw_per_week: 0.5 },
        { kg_per_week: 0.74, pct_bw_per_week: 1 },
      ],
      rate: { kg_per_week: 0.37, pct_bw_per_week: 0.5 },
    };
    setup({ preview: fake });
    await step("goal");
    const chips = await screen.findAllByTestId("rate-chip");
    expect(chips).toHaveLength(2);
    expect(chips[0]?.textContent).toContain("0.37");
    expect(chips[0]?.getAttribute("aria-pressed")).toBe("true");
    await userEvent.click(chips[1] as HTMLElement);
    await waitFor(() => expect(lastPreview().rate_pct_bw_per_week).toBe(1));
  });

  it("rate chips show the percent only when kg_per_week is null", async () => {
    const fake = {
      ...targetsFixture("g2_lose_adjusted"),
      rate_options: [
        { kg_per_week: null, pct_bw_per_week: 0.5 },
        { kg_per_week: null, pct_bw_per_week: 1 },
      ],
      rate: { kg_per_week: null, pct_bw_per_week: 0.5 },
    };
    setup({ preview: fake });
    await step("goal");
    const chips = await screen.findAllByTestId("rate-chip");
    expect(chips[0]?.textContent).toBe(
      en.targets.rate_option_pct.replace("{pct}", "0.5"),
    );
    expect(chips[0]?.textContent).not.toContain("kg");
  });

  it("missing fields use the neutral targets.field labels", async () => {
    setup({ preview: targetsFixture("needs_height_cm") });
    await step("guide");
    expect(
      await screen.findByText(new RegExp(en.targets.field.height)),
    ).toBeTruthy();
  });

  it("g1_hide_all preview shows no digits for energy and macros", async () => {
    setup({ preview: targetsFixture("g1_hide_all") });
    await step("guide");
    await screen.findByTestId("step-guide");
    expect(screen.queryByTestId("guide-rows")?.textContent ?? "").not.toMatch(
      /\d/,
    );
    expect(text("targets-explanation")).not.toMatch(/\d/);
    expect(screen.getByText(en.diary.hidden_numbers)).toBeTruthy();
  });

  it("missing consent opens the health-data sheet before save", async () => {
    setup({ consents: { terms: true } });
    await step("guide");
    await userEvent.click(
      await screen.findByRole("button", { name: en.targets.save }),
    );
    expect(await screen.findByTestId("consent-dialog")).toBeTruthy();
    expect(api.callsTo("PATCH", `/v1/members/${PRIMARY}`)).toHaveLength(0);
    expect(api.callsTo("PUT", "/v1/targets/settings")).toHaveLength(0);
  });

  it("unusual height asks for confirmation", async () => {
    setup({
      preview: {
        ...targetsFixture("g2_lose_adjusted"),
        unusual_fields: ["height_cm"],
      },
    });
    await step("guide");
    const save = (await screen.findByRole("button", {
      name: en.targets.save,
    })) as HTMLButtonElement;
    expect(save.disabled).toBe(true);
    await userEvent.click(
      screen.getByRole("checkbox", { name: /Please check Height/ }),
    );
    expect(save.disabled).toBe(false);
  });

  it("skip goes home without saving", async () => {
    setup();
    await userEvent.click(
      await screen.findByRole("button", { name: en.targets.skip }),
    );
    expect(nav.push).toHaveBeenCalledWith("/en/home");
    expect(api.callsTo("PUT", "/v1/targets/settings")).toHaveLength(0);
    expect(api.callsTo("PATCH", `/v1/members/${PRIMARY}`)).toHaveLength(0);
  });

  it("save sends the member PATCH then the settings PUT, then goes home", async () => {
    setup();
    await step("guide");
    await userEvent.click(
      await screen.findByRole("button", { name: en.targets.save }),
    );
    await waitFor(() => expect(nav.push).toHaveBeenCalledWith("/en/home"));
    const put = api.callsTo("PUT", "/v1/targets/settings")[0]?.body as Record<
      string,
      unknown
    >;
    expect(put.direction).toBe("lose");
    expect(put.numbers_display).toBe("show");
    expect(put.pregnant_or_breastfeeding).toBe(false);
  });
});
