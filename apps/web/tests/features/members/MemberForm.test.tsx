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
import { MemberForm } from "@/features/members/components/MemberForm";
import {
  type MemberBody,
  memberFormSchema,
  memberToForm,
  needsHealthConsent,
  normaliseAllergen,
  toPatch,
} from "@/features/members/lib/memberForm";
import { membersMessages } from "@/i18n/client-messages";
import { MESSAGES, type TestLocale } from "../../support/analyze-fixtures";
import { apiStub, consentStates, envelope, json } from "../../support/api-stub";

const router = vi.hoisted(() => ({ push: vi.fn(), replace: vi.fn() }));
vi.mock("next/navigation", () => ({ useRouter: () => router }));
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

const en = MESSAGES.en;
let api: ReturnType<typeof apiStub>;

beforeEach(() => {
  fetchMock.mockReset();
  router.push.mockReset();
  api = apiStub(fetchMock);
});
afterEach(cleanup);

function renderForm(member?: MemberOut, locale: TestLocale = "en") {
  const client = new QueryClient({
    defaultOptions: { queries: { retry: false } },
  });
  const errors: unknown[] = [];
  render(
    <QueryClientProvider client={client}>
      <NextIntlClientProvider
        locale={locale}
        messages={membersMessages(MESSAGES[locale])}
        onError={(e) => errors.push(e)}
      >
        <MemberForm member={member} />
      </NextIntlClientProvider>
    </QueryClientProvider>,
  );
  return { errors };
}

const MEMBER_ID = "0b6c1f8e-3c1a-4f0e-9a51-1d2e3f4a5b6c";
const saved = (over: Partial<MemberOut> = {}): MemberOut => ({
  id: MEMBER_ID,
  name: "Dad",
  relation: "parent",
  birth_year: 1960,
  sex: null,
  height_cm: null,
  weight_kg: null,
  body_fat_pct: null,
  diet: "veg",
  allergens: [],
  conditions: [],
  custom_alerts: [],
  goal: null,
  is_primary: false,
  ...over,
});

async function fillBasics(user: ReturnType<typeof userEvent.setup>) {
  await user.type(screen.getByLabelText(en.members.form.name), "Dad");
  await user.selectOptions(
    screen.getByLabelText(en.members.form.relation),
    "parent",
  );
  await user.type(screen.getByLabelText(en.members.form.birth_year), "1960");
}

const save = () => screen.getByRole("button", { name: en.members.form.save });

describe("MemberForm", () => {
  it("submits normalised other allergen", async () => {
    api
      .on("GET", "/v1/consents", consentStates({ health_data: true }))
      .on("POST", "/v1/members", (c) => json(201, saved(c.body as object)));
    const user = userEvent.setup();
    renderForm();
    await fillBasics(user);
    await user.type(
      screen.getByLabelText(en.members.form.allergen_other),
      "  Kiwi ",
    );
    await user.click(
      screen.getByRole("button", { name: en.members.form.allergen_add }),
    );
    expect(within(screen.getByTestId("other-allergens")).getByText("Kiwi"));
    await waitFor(() =>
      expect(api.callsTo("GET", "/v1/consents")).toHaveLength(1),
    );
    await user.click(save());
    await waitFor(() => expect(router.push).toHaveBeenCalledWith("/en/family"));
    const [post] = api.callsTo("POST", "/v1/members");
    expect(post?.body).toEqual({
      name: "Dad",
      relation: "parent",
      birth_year: 1960,
      sex: null,
      height_cm: null,
      weight_kg: null,
      diet: "non_veg",
      allergens: ["Kiwi"],
      conditions: [],
      custom_alerts: [],
      goal: null,
    });
  });

  it("opens consent dialog before saving conditions", async () => {
    api
      .on("GET", "/v1/consents", consentStates({}))
      .on("POST", "/v1/consents", (c) =>
        json(200, consentStates({ health_data: true, ...(c.body as object) })),
      )
      .on("POST", "/v1/members", (c) => json(201, saved(c.body as object)));
    const user = userEvent.setup();
    renderForm();
    await fillBasics(user);
    await user.click(screen.getByLabelText(en.condition.diabetes));
    await user.click(save());

    const dialog = await screen.findByTestId("consent-dialog");
    expect(within(dialog).getByText(en.consent.health_data.body)).toBeTruthy();
    expect(api.callsTo("POST", "/v1/members")).toHaveLength(0);

    await user.click(
      within(dialog).getByRole("button", { name: en.consent.agree }),
    );
    await waitFor(() => expect(router.push).toHaveBeenCalledWith("/en/family"));
    // Only health_data: AI explanations stay optional and unticked.
    expect(api.callsTo("POST", "/v1/consents").map((c) => c.body)).toEqual([
      { purpose: "health_data", version: "2026-11-01", granted: true },
    ]);
    const posts = api.callsTo("POST", "/v1/members");
    expect(posts).toHaveLength(1);
    expect(posts[0]?.body).toHaveProperty("conditions", ["diabetes"]);
  });

  it("declining consent saves nothing", async () => {
    api.on("GET", "/v1/consents", consentStates({}));
    const user = userEvent.setup();
    renderForm();
    await fillBasics(user);
    await user.click(screen.getByLabelText(en.condition.diabetes));
    await user.click(save());
    const dialog = await screen.findByTestId("consent-dialog");
    await user.click(
      within(dialog).getByRole("button", { name: en.consent.decline }),
    );
    expect(screen.queryByTestId("consent-dialog")).toBeNull();
    expect(api.callsTo("POST", "/v1/members")).toHaveLength(0);
    expect(api.callsTo("POST", "/v1/consents")).toHaveLength(0);
  });

  it("a member with no health fields saves without asking for consent", async () => {
    api
      .on("GET", "/v1/consents", consentStates({}))
      .on("POST", "/v1/members", (c) => json(201, saved(c.body as object)));
    const user = userEvent.setup();
    renderForm();
    await fillBasics(user);
    await user.click(save());
    await waitFor(() => expect(router.push).toHaveBeenCalled());
    expect(screen.queryByTestId("consent-dialog")).toBeNull();
  });

  it("a 403 consent_required from the API opens the consent dialog, then retries", async () => {
    api
      .on("GET", "/v1/consents", consentStates({ health_data: true }))
      .on("POST", "/v1/consents", consentStates({ health_data: true }))
      .on("POST", "/v1/members", (c, n) =>
        n === 1
          ? json(403, envelope("consent_required", { purpose: "health_data" }))
          : json(201, saved(c.body as object)),
      );
    const user = userEvent.setup();
    renderForm();
    await fillBasics(user);
    await user.click(screen.getByRole("button", { name: en.allergen.peanut }));
    await waitFor(() =>
      expect(api.callsTo("GET", "/v1/consents")).toHaveLength(1),
    );
    await user.click(save());
    const dialog = await screen.findByTestId("consent-dialog");
    expect(screen.queryByText(en.error.consent_required)).toBeNull();
    await user.click(
      within(dialog).getByRole("button", { name: en.consent.agree }),
    );
    await waitFor(() => expect(router.push).toHaveBeenCalledWith("/en/family"));
    const posts = api.callsTo("POST", "/v1/members");
    expect(posts).toHaveLength(2);
    expect(posts[1]?.body).toEqual(posts[0]?.body);
  });

  it("shows member_limit error text from i18n", async () => {
    api
      .on("GET", "/v1/consents", consentStates({ health_data: true }))
      .on(
        "POST",
        "/v1/members",
        json(422, envelope("member_limit", { max: 10 })),
      );
    const user = userEvent.setup();
    renderForm();
    await fillBasics(user);
    await user.click(save());
    expect((await screen.findByRole("alert")).textContent).toBe(
      en.error.member_limit,
    );
    expect(router.push).not.toHaveBeenCalled();
  });

  it("checks the fields before sending (birth year required, ranges)", async () => {
    api.on("GET", "/v1/consents", consentStates({ health_data: true }));
    const user = userEvent.setup();
    renderForm();
    await user.type(screen.getByLabelText(en.members.form.name), "Dad");
    await user.selectOptions(
      screen.getByLabelText(en.members.form.relation),
      "parent",
    );
    await user.type(screen.getByLabelText(en.members.form.height_cm), "500");
    await user.click(save());
    const year = String(new Date().getFullYear());
    expect(
      screen.getByText(
        en.members.form.birth_year_invalid.replace("{year}", year),
      ),
    ).toBeTruthy();
    expect(screen.getByText(en.members.form.height_invalid)).toBeTruthy();
    expect(
      screen
        .getByLabelText(en.members.form.birth_year)
        .getAttribute("aria-invalid"),
    ).toBe("true");
    expect(api.callsTo("POST", "/v1/members")).toHaveLength(0);
  });

  it("asks before removing an allergy; a pure removal needs no consent", async () => {
    api
      .on("GET", "/v1/consents", consentStates({}))
      .on("PATCH", `/v1/members/${MEMBER_ID}`, (c) =>
        json(200, saved(c.body as object)),
      );
    const user = userEvent.setup();
    renderForm(
      saved({ allergens: ["milk", "kiwi"], conditions: ["diabetes"] }),
    );
    // Consent is off but the member has saved health data: say what that means.
    expect(await screen.findByTestId("consent-withdrawn-notice")).toBeTruthy();

    const milk = screen.getByRole("button", { name: en.allergen.milk });
    expect(milk.getAttribute("aria-pressed")).toBe("true");
    await user.click(milk);
    const confirm = screen.getByTestId("confirm-dialog");
    expect(
      within(confirm).getByText(
        en.members.form.remove_allergy_confirm
          .replace("{allergen}", en.allergen.milk)
          .replace("{name}", "Dad"),
      ),
    ).toBeTruthy();
    // Cancel keeps it.
    await user.click(
      within(confirm).getByRole("button", { name: en.members.form.cancel }),
    );
    expect(milk.getAttribute("aria-pressed")).toBe("true");

    // A typed allergy asks too.
    await user.click(
      screen.getByRole("button", {
        name: en.members.form.remove_allergy.replace("{allergen}", "kiwi"),
      }),
    );
    await user.click(
      within(screen.getByTestId("confirm-dialog")).getByRole("button", {
        name: en.members.remove,
      }),
    );
    expect(screen.queryByTestId("other-allergens")).toBeNull();

    await user.click(save());
    await waitFor(() => expect(router.push).toHaveBeenCalledWith("/en/family"));
    expect(screen.queryByTestId("consent-dialog")).toBeNull();
    const [patch] = api.callsTo("PATCH", `/v1/members/${MEMBER_ID}`);
    expect(patch?.body).toMatchObject({
      allergens: ["milk"],
      conditions: ["diabetes"],
      relation: "parent",
    });
  });

  it("the primary member's relation is fixed and never sent", async () => {
    api
      .on("GET", "/v1/consents", consentStates({ health_data: true }))
      .on("PATCH", `/v1/members/${MEMBER_ID}`, (c) =>
        json(200, saved(c.body as object)),
      );
    const user = userEvent.setup();
    renderForm(
      saved({
        name: "Asha",
        relation: "self",
        is_primary: true,
        birth_year: null,
      }),
    );
    const relation = screen.getByLabelText(
      en.members.form.relation,
    ) as HTMLSelectElement;
    expect(relation.disabled).toBe(true);
    expect(relation.value).toBe("self");
    expect(
      screen.queryByRole("button", { name: en.members.remove }),
    ).toBeNull();
    await user.type(screen.getByLabelText(en.members.form.birth_year), "1990");
    await user.click(save());
    await waitFor(() => expect(router.push).toHaveBeenCalled());
    const [patch] = api.callsTo("PATCH", `/v1/members/${MEMBER_ID}`);
    expect(patch?.body).not.toHaveProperty("relation");
    expect(patch?.body).toMatchObject({ name: "Asha", birth_year: 1990 });
  });

  it("removing a member asks first, then deletes", async () => {
    api
      .on("GET", "/v1/consents", consentStates({ health_data: true }))
      .on(
        "DELETE",
        `/v1/members/${MEMBER_ID}`,
        new Response(null, { status: 204 }),
      );
    const user = userEvent.setup();
    renderForm(saved());
    await user.click(screen.getByRole("button", { name: en.members.remove }));
    const confirm = screen.getByTestId("confirm-dialog");
    expect(
      within(confirm).getByText(
        en.members.remove_confirm.replace("{name}", "Dad"),
      ),
    ).toBeTruthy();
    expect(api.callsTo("DELETE", `/v1/members/${MEMBER_ID}`)).toHaveLength(0);
    await user.click(
      within(confirm).getByRole("button", { name: en.members.remove }),
    );
    await waitFor(() => expect(router.push).toHaveBeenCalledWith("/en/family"));
    expect(api.callsTo("DELETE", `/v1/members/${MEMBER_ID}`)).toHaveLength(1);
  });

  it.each(["hi", "mr"] as const)(
    "renders every label from i18n in %s",
    async (locale) => {
      api.on("GET", "/v1/consents", consentStates({ health_data: true }));
      const { errors } = renderForm(undefined, locale);
      const m = MESSAGES[locale];
      expect(screen.getByLabelText(m.members.form.name)).toBeTruthy();
      expect(
        screen.getByRole("button", { name: m.allergen.peanut }),
      ).toBeTruthy();
      expect(screen.getByLabelText(m.condition.diabetes)).toBeTruthy();
      expect(screen.getByText(m.alert.palm_oil)).toBeTruthy();
      expect(errors).toEqual([]);
    },
  );
});

describe("memberFormSchema and helpers", () => {
  it("normalises typed allergens", () => {
    // Free text is kept as typed (trim and NFC only), as the API stores it;
    // a canonical key typed in any case is that key.
    expect(normaliseAllergen("  Kiwi ")).toBe("Kiwi");
    expect(normaliseAllergen("MILK")).toBe("milk");
    expect(normaliseAllergen("Pine   Nut")).toBe("Pine   Nut");
    expect(normaliseAllergen("x")).toBeNull();
    expect(normaliseAllergen("a".repeat(41))).toBeNull();
    // NFC: a decomposed é is the same allergen as the composed one.
    expect(normaliseAllergen("café")).toBe("café");
  });

  it("dedupes typed allergens case-insensitively, keeping the first", () => {
    const parsed = memberFormSchema.safeParse(
      {
        name: "A",
        relation: "child",
        birth_year: "2015",
        sex: "",
        height_cm: "",
        weight_kg: "",
        diet: "veg",
        allergens: ["Kiwi", "kiwi", "KIWI"],
        conditions: [],
        custom_alerts: [],
        goal: "",
      },
      2026,
    );
    expect(parsed.success && parsed.data.allergens).toEqual(["Kiwi"]);
    // A stored "kiwi" re-sent as "Kiwi" is not new health data.
    const body: MemberBody = {
      name: "A",
      relation: "child",
      birth_year: 2015,
      diet: "veg",
      allergens: ["Kiwi"],
      conditions: [],
      custom_alerts: [],
    };
    expect(needsHealthConsent(body, saved({ allergens: ["kiwi"] }))).toBe(
      false,
    );
  });

  it("leaves unknown stored diet, conditions and alerts unchanged", () => {
    // Values a newer API knows but this build doesn't: never drop or coerce.
    const stored = saved({
      diet: "pescatarian" as MemberOut["diet"],
      conditions: ["diabetes", "thyroid"] as MemberOut["conditions"],
      custom_alerts: ["palm_oil", "caffeine"] as MemberOut["custom_alerts"],
    });
    const parsed = memberFormSchema.safeParse(memberToForm(stored), 2026);
    expect(parsed.success).toBe(true);
    if (!parsed.success) return;
    const patch = toPatch(parsed.data, false, stored);
    expect(patch.diet).toBeNull();
    expect(patch.conditions).toBeNull();
    expect(patch.custom_alerts).toBeNull();

    const known = saved({
      diet: "vegan",
      conditions: ["diabetes"],
      custom_alerts: ["palm_oil"],
    });
    const ok = memberFormSchema.safeParse(memberToForm(known), 2026);
    if (!ok.success) throw new Error("known member should parse");
    const full = toPatch(ok.data, false, known);
    expect(full.diet).toBe("vegan");
    expect(full.conditions).toEqual(["diabetes"]);
    expect(full.custom_alerts).toEqual(["palm_oil"]);
  });

  it("caps allergens at 20", () => {
    const base = {
      name: "A",
      relation: "child" as const,
      birth_year: "2015",
      sex: "" as const,
      height_cm: "",
      weight_kg: "",
      diet: "veg" as const,
      conditions: [],
      custom_alerts: [],
      goal: "" as const,
    };
    const many = Array.from({ length: 21 }, (_, i) => `food ${i}`);
    expect(
      memberFormSchema.safeParse({ ...base, allergens: many }, 2026),
    ).toEqual({
      success: false,
      errors: { allergens: "members.form.allergen_limit" },
    });
    expect(
      memberFormSchema.safeParse(
        { ...base, allergens: many.slice(0, 20) },
        2026,
      ).success,
    ).toBe(true);
    expect(
      memberFormSchema.safeParse(
        { ...base, allergens: [], birth_year: "2027" },
        2026,
      ),
    ).toMatchObject({ success: false });
  });

  it("needs consent only for new health data", () => {
    const body: MemberBody = {
      name: "A",
      relation: "child",
      birth_year: 2015,
      diet: "veg",
      allergens: ["milk"],
      conditions: [],
      custom_alerts: [],
    };
    const before = saved({ allergens: ["milk", "egg"] });
    expect(needsHealthConsent(body)).toBe(true);
    expect(needsHealthConsent(body, before)).toBe(false); // pure removal
    expect(needsHealthConsent({ ...body, allergens: ["kiwi"] }, before)).toBe(
      true,
    );
    expect(
      needsHealthConsent({ ...body, allergens: [], height_cm: 120 }, before),
    ).toBe(true);
    expect(
      needsHealthConsent(
        { ...body, allergens: [], height_cm: 120 },
        saved({ height_cm: 120 }),
      ),
    ).toBe(false);
  });
});
