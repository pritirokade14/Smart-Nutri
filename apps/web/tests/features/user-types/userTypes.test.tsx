import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import {
  cleanup,
  render,
  screen,
  waitFor,
  within,
} from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { type AbstractIntlMessages, NextIntlClientProvider } from "next-intl";
import type { ReactNode } from "react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { ConsentGate } from "@/features/consent/components/ConsentGate";
import type { UserTypesOut } from "@/features/user-types/api/userTypes";
import { ProfileFocus } from "@/features/user-types/components/ProfileFocus";
import { UserTypesGate } from "@/features/user-types/components/UserTypesGate";
import { WelcomeFlow } from "@/features/user-types/components/WelcomeFlow";
import { clientMessages, membersMessages } from "@/i18n/client-messages";
import { MESSAGES } from "../../support/analyze-fixtures";
import { apiStub, consentStates, envelope, json } from "../../support/api-stub";

// Plan 9 Task 12: the same ten cases as Android's Task 9, named identically.

const nav = vi.hoisted(() => ({
  pathname: "/en/home",
  replace: vi.fn(),
  push: vi.fn(),
}));
vi.mock("next/navigation", () => ({
  usePathname: () => nav.pathname,
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
const track = vi.hoisted(() => vi.fn());
vi.mock("@/lib/analytics", () => ({ track }));
const fetchMock = vi.hoisted(() => {
  const fn = vi.fn();
  globalThis.fetch = fn as unknown as typeof fetch;
  return fn;
});

const en = MESSAGES.en;
const PRIMARY = "a0000000-0000-4000-8000-000000000001";
let api: ReturnType<typeof apiStub>;

beforeEach(() => {
  nav.pathname = "/en/welcome";
  nav.replace.mockReset();
  nav.push.mockReset();
  track.mockReset();
  fetchMock.mockReset();
  api = apiStub(fetchMock);
});
afterEach(cleanup);

const out = (over: Partial<UserTypesOut> = {}): UserTypesOut => ({
  types: [],
  follow_ups: {},
  active_type: "eat_better",
  answered: false,
  answered_at: null,
  prefill: null,
  ...over,
});

const prefill = (
  changes: NonNullable<UserTypesOut["prefill"]>["changes"],
  goal_choice: NonNullable<UserTypesOut["prefill"]>["goal_choice"] = null,
) => ({
  member_id: PRIMARY,
  changes,
  goal_choice,
  needs_health_consent: false,
});

function wrap(
  ui: ReactNode,
  messages: AbstractIntlMessages = membersMessages(en),
) {
  const client = new QueryClient({
    defaultOptions: { queries: { retry: false } },
  });
  render(
    <QueryClientProvider client={client}>
      <NextIntlClientProvider locale="en" messages={messages}>
        {ui}
      </NextIntlClientProvider>
    </QueryClientProvider>,
  );
  return client;
}

const tile = (type: string) => screen.getByTestId(`type-tile-${type}`);
const button = (name: string) => screen.getByRole("button", { name });

describe("user types (T12)", () => {
  it("max three selections", async () => {
    api
      .on("GET", "/v1/me/user-types", out())
      .on("GET", "/v1/consents", consentStates({ terms: true }));
    wrap(<WelcomeFlow edit={false} />);
    await screen.findByRole("heading", { level: 1, name: en.user_types.title });
    for (const t of ["family", "gym", "eat_better"])
      await userEvent.click(tile(t));
    expect(screen.queryByText(en.user_types.max_reached)).toBeNull();
    await userEvent.click(tile("weight_loss"));
    expect(screen.getByText(en.user_types.max_reached)).toBeTruthy();
    expect(tile("weight_loss").getAttribute("aria-pressed")).toBe("false");
    const pressed = screen
      .getAllByRole("button")
      .filter((b) => b.getAttribute("aria-pressed") === "true");
    expect(pressed).toHaveLength(3);
  });

  it("skip stores empty types and lands on home", async () => {
    api
      .on("GET", "/v1/me/user-types", out())
      .on("GET", "/v1/consents", consentStates({ terms: true }))
      .on("PUT", "/v1/me/user-types", out({ answered: true }));
    wrap(<WelcomeFlow edit={false} />);
    await userEvent.click(
      await screen.findByRole("button", { name: en.user_types.skip }),
    );
    await waitFor(() => expect(nav.replace).toHaveBeenCalledWith("/en/home"));
    expect(api.callsTo("PUT", "/v1/me/user-types").map((c) => c.body)).toEqual([
      { types: [], follow_ups: {} },
    ]);
    expect(api.callsTo("PATCH", `/v1/members/${PRIMARY}`)).toHaveLength(0);
  });

  it("terms then picker redirect", async () => {
    nav.pathname = "/en/home";
    api
      .on("GET", "/v1/consents", consentStates({}))
      .on("POST", "/v1/consents", consentStates({ terms: true }))
      .on("GET", "/v1/me/user-types", out());
    wrap(
      <ConsentGate>
        <UserTypesGate>
          <p>{"app page"}</p>
        </UserTypesGate>
      </ConsentGate>,
      clientMessages(en),
    );
    // Terms come first: no picker redirect while the terms step is shown.
    await screen.findByTestId("terms-step");
    expect(nav.replace).not.toHaveBeenCalled();
    await userEvent.click(button(en.consent.agree));
    await waitFor(() =>
      expect(nav.replace).toHaveBeenCalledWith("/en/welcome"),
    );
    expect(screen.queryByText("app page")).toBeNull();
  });

  it("terms then picker redirect: no picker once answered, profile exempt", async () => {
    nav.pathname = "/en/home";
    api
      .on("GET", "/v1/consents", consentStates({ terms: true }))
      .on("GET", "/v1/me/user-types", out({ answered: true }));
    wrap(
      <ConsentGate>
        <UserTypesGate>
          <p>{"app page"}</p>
        </UserTypesGate>
      </ConsentGate>,
      clientMessages(en),
    );
    expect(await screen.findByText("app page")).toBeTruthy();
    expect(nav.replace).not.toHaveBeenCalled();
    cleanup();

    nav.pathname = "/en/profile";
    api.on("GET", "/v1/me/user-types", out());
    wrap(
      <UserTypesGate>
        <p>{"profile page"}</p>
      </UserTypesGate>,
      clientMessages(en),
    );
    expect(await screen.findByText("profile page")).toBeTruthy();
    expect(nav.replace).not.toHaveBeenCalled();
  });

  it("terms then picker redirect: loading and errors never block the page", async () => {
    nav.pathname = "/en/scan";
    api.on("GET", "/v1/me/user-types", json(500, envelope("internal_error")));
    wrap(
      <UserTypesGate>
        <p>{"scan page"}</p>
      </UserTypesGate>,
      clientMessages(en),
    );
    expect(screen.getByText("scan page")).toBeTruthy();
    await waitFor(() =>
      expect(api.callsTo("GET", "/v1/me/user-types")).toHaveLength(1),
    );
    expect(screen.getByText("scan page")).toBeTruthy();
    expect(nav.replace).not.toHaveBeenCalled();
  });

  it("an answered account opening /welcome without edit goes home", async () => {
    api
      .on("GET", "/v1/me/user-types", out({ answered: true }))
      .on("GET", "/v1/consents", consentStates({ terms: true }));
    wrap(<WelcomeFlow edit={false} />);
    await waitFor(() => expect(nav.replace).toHaveBeenCalledWith("/en/home"));
  });

  it("health tile without consent opens consent sheet; declined drops it with note", async () => {
    api
      .on("GET", "/v1/me/user-types", out())
      .on("GET", "/v1/consents", consentStates({ terms: true }))
      .on("PUT", "/v1/me/user-types", (c) =>
        json(
          200,
          out({
            answered: true,
            types: (c.body as { types: UserTypesOut["types"] }).types,
          }),
        ),
      );
    wrap(<WelcomeFlow edit={false} />);
    await screen.findByRole("heading", { level: 1, name: en.user_types.title });
    await userEvent.click(tile("health_condition"));
    await userEvent.click(tile("family"));
    await userEvent.click(button(en.user_types.continue));
    // Follow-ups, in priority order: health first, then family.
    const sections = screen.getAllByTestId(/^follow-up-/);
    expect(sections.map((s) => s.dataset.testid)).toEqual([
      "follow-up-health_condition",
      "follow-up-family",
    ]);
    await userEvent.click(button(en.condition.diabetes));
    await userEvent.click(button(en.user_types.follow_up.family.children));
    await userEvent.click(button(en.user_types.continue));
    const dialog = await screen.findByTestId("consent-dialog");
    expect(api.callsTo("PUT", "/v1/me/user-types")).toHaveLength(0);
    await userEvent.click(
      within(dialog).getByRole("button", { name: en.consent.decline }),
    );
    expect(await screen.findByText(en.user_types.consent_needed)).toBeTruthy();
    expect(api.callsTo("PUT", "/v1/me/user-types").map((c) => c.body)).toEqual([
      { types: ["family"], follow_ups: { family_with: ["children"] } },
    ]);
    expect(api.callsTo("POST", "/v1/consents")).toHaveLength(0);
  });

  it("health tile with consent agreed in place saves everything", async () => {
    api
      .on("GET", "/v1/me/user-types", out())
      .on("GET", "/v1/consents", consentStates({ terms: true }))
      .on(
        "POST",
        "/v1/consents",
        consentStates({ terms: true, health_data: true }),
      )
      .on("PUT", "/v1/me/user-types", out({ answered: true }));
    wrap(<WelcomeFlow edit={false} />);
    await screen.findByRole("heading", { level: 1, name: en.user_types.title });
    await userEvent.click(tile("weight_loss"));
    await userEvent.click(button(en.user_types.continue));
    const dialog = await screen.findByTestId("consent-dialog");
    await waitFor(() =>
      expect(
        (
          within(dialog).getByRole("button", {
            name: en.consent.agree,
          }) as HTMLButtonElement
        ).disabled,
      ).toBe(false),
    );
    await userEvent.click(
      within(dialog).getByRole("button", { name: en.consent.agree }),
    );
    await waitFor(() => expect(nav.replace).toHaveBeenCalledWith("/en/home"));
    expect(api.callsTo("PUT", "/v1/me/user-types").map((c) => c.body)).toEqual([
      { types: ["weight_loss"], follow_ups: {} },
    ]);
  });

  it("defaults are not saved until confirmed", async () => {
    api
      .on("GET", "/v1/me/user-types", out())
      .on(
        "GET",
        "/v1/consents",
        consentStates({ terms: true, health_data: true }),
      )
      .on(
        "PUT",
        "/v1/me/user-types",
        out({
          answered: true,
          types: ["allergy_diet"],
          prefill: prefill([
            {
              field: "allergens",
              current: [],
              value: ["milk"],
              added: ["milk"],
              reason: "allergy_diet",
            },
          ]),
        }),
      );
    wrap(<WelcomeFlow edit={false} />);
    await screen.findByRole("heading", { level: 1, name: en.user_types.title });
    await userEvent.click(tile("allergy_diet"));
    await userEvent.click(button(en.user_types.continue));
    await userEvent.click(button(en.allergen.milk));
    await userEvent.click(button(en.user_types.continue));
    const review = await screen.findByTestId("prefill-review");
    expect(within(review).getByText(en.user_types.prefill.body)).toBeTruthy();
    // The suggestion is shown, ticked (the user's own follow-up), not saved.
    const box = within(review).getByRole("checkbox", {
      name: "Allergies: Milk",
    });
    expect((box as HTMLInputElement).checked).toBe(true);
    expect(api.calls.filter((c) => c.method === "PATCH")).toHaveLength(0);
    // "Not now" sends nothing at all.
    await userEvent.click(button(en.user_types.prefill.not_now));
    await waitFor(() => expect(nav.replace).toHaveBeenCalledWith("/en/home"));
    expect(api.calls.filter((c) => c.method === "PATCH")).toHaveLength(0);
  });

  it("only ticked changes are sent", async () => {
    api
      .on("GET", "/v1/me/user-types", out())
      .on(
        "GET",
        "/v1/consents",
        consentStates({ terms: true, health_data: true }),
      )
      .on(
        "PUT",
        "/v1/me/user-types",
        out({
          answered: true,
          types: ["allergy_diet", "eat_better"],
          prefill: prefill([
            {
              field: "allergens",
              current: ["peanut"],
              value: ["peanut", "milk"],
              added: ["milk"],
              reason: "allergy_diet",
            },
            {
              field: "custom_alerts",
              current: [],
              value: ["palm_oil"],
              added: ["palm_oil"],
              reason: "eat_better",
            },
            {
              field: "goal",
              current: null,
              value: "healthy_eating",
              added: [],
              reason: "eat_better",
            },
          ]),
        }),
      )
      .on("PATCH", `/v1/members/${PRIMARY}`, { id: PRIMARY });
    wrap(<WelcomeFlow edit={false} />);
    await screen.findByRole("heading", { level: 1, name: en.user_types.title });
    await userEvent.click(tile("allergy_diet"));
    await userEvent.click(tile("eat_better"));
    await userEvent.click(button(en.user_types.continue));
    await userEvent.click(button(en.allergen.milk));
    await userEvent.click(button(en.alert.palm_oil));
    await userEvent.click(button(en.user_types.continue));
    const review = await screen.findByTestId("prefill-review");
    const boxes = within(review).getAllByRole("checkbox") as HTMLInputElement[];
    // Follow-up answers start ticked; the goal implied by a type does not.
    expect(boxes.map((b) => b.checked)).toEqual([true, true, false]);
    await userEvent.click(boxes[1] as HTMLInputElement); // untick the alert
    await userEvent.click(button(en.user_types.prefill.apply));
    await waitFor(() => expect(nav.replace).toHaveBeenCalledWith("/en/home"));
    expect(
      api.callsTo("PATCH", `/v1/members/${PRIMARY}`).map((c) => c.body),
    ).toEqual([{ allergens: ["peanut", "milk"] }]);
  });

  it("goal conflict defaults to neither", async () => {
    api
      .on("GET", "/v1/me/user-types", out())
      .on(
        "GET",
        "/v1/consents",
        consentStates({ terms: true, health_data: true }),
      )
      .on(
        "PUT",
        "/v1/me/user-types",
        out({
          answered: true,
          types: ["weight_loss", "gym"],
          prefill: prefill([], ["weight_loss", "build_muscle"]),
        }),
      )
      .on("PATCH", `/v1/members/${PRIMARY}`, { id: PRIMARY });
    wrap(<WelcomeFlow edit={false} />);
    await screen.findByRole("heading", { level: 1, name: en.user_types.title });
    await userEvent.click(tile("weight_loss"));
    await userEvent.click(tile("gym"));
    await userEvent.click(button(en.user_types.continue));
    await userEvent.click(
      screen.getByRole("radio", {
        name: en.user_types.follow_up.gym.build_muscle,
      }),
    );
    await userEvent.click(button(en.user_types.continue));
    const review = await screen.findByTestId("prefill-review");
    expect(
      within(review).getByText(en.user_types.prefill.goal_conflict),
    ).toBeTruthy();
    const neither = within(review).getByRole("radio", {
      name: en.user_types.prefill.goal_neither,
    }) as HTMLInputElement;
    expect(neither.checked).toBe(true);
    // Saving with "neither" changes nothing: no members PATCH.
    await userEvent.click(button(en.user_types.prefill.apply));
    await waitFor(() => expect(nav.replace).toHaveBeenCalledWith("/en/home"));
    expect(api.calls.filter((c) => c.method === "PATCH")).toHaveLength(0);
    expect(api.callsTo("PUT", "/v1/me/user-types").map((c) => c.body)).toEqual([
      {
        types: ["weight_loss", "gym"],
        follow_ups: { gym_goal: "build_muscle" },
      },
    ]);
  });

  it("goal conflict: picking one sends only that goal", async () => {
    api
      .on("GET", "/v1/me/user-types", out())
      .on(
        "GET",
        "/v1/consents",
        consentStates({ terms: true, health_data: true }),
      )
      .on(
        "PUT",
        "/v1/me/user-types",
        out({
          answered: true,
          prefill: prefill([], ["weight_loss", "build_muscle"]),
        }),
      )
      .on("PATCH", `/v1/members/${PRIMARY}`, { id: PRIMARY });
    wrap(<WelcomeFlow edit={false} />);
    await screen.findByRole("heading", { level: 1, name: en.user_types.title });
    await userEvent.click(tile("weight_loss"));
    await userEvent.click(button(en.user_types.continue));
    const review = await screen.findByTestId("prefill-review");
    await userEvent.click(
      within(review).getByRole("radio", { name: en.members.goal.build_muscle }),
    );
    await userEvent.click(button(en.user_types.prefill.apply));
    await waitFor(() => expect(nav.replace).toHaveBeenCalled());
    expect(
      api.callsTo("PATCH", `/v1/members/${PRIMARY}`).map((c) => c.body),
    ).toEqual([{ goal: "build_muscle" }]);
  });

  it("a 403 on the members PATCH goes through the consent dialog, then retries", async () => {
    let patched = 0;
    api
      .on("GET", "/v1/me/user-types", out())
      .on("GET", "/v1/consents", consentStates({ terms: true }))
      .on(
        "POST",
        "/v1/consents",
        consentStates({ terms: true, health_data: true }),
      )
      .on(
        "PUT",
        "/v1/me/user-types",
        out({
          answered: true,
          prefill: prefill([
            {
              field: "custom_alerts",
              current: [],
              value: ["msg"],
              added: ["msg"],
              reason: "eat_better",
            },
          ]),
        }),
      )
      .on("PATCH", `/v1/members/${PRIMARY}`, () => {
        patched += 1;
        return patched === 1
          ? json(403, envelope("consent_required", { purpose: "health_data" }))
          : json(200, { id: PRIMARY });
      });
    wrap(<WelcomeFlow edit={false} />);
    await screen.findByRole("heading", { level: 1, name: en.user_types.title });
    await userEvent.click(tile("eat_better"));
    await userEvent.click(button(en.user_types.continue));
    await userEvent.click(button(en.alert.msg));
    await userEvent.click(button(en.user_types.continue));
    await screen.findByTestId("prefill-review");
    await userEvent.click(button(en.user_types.prefill.apply));
    const dialog = await screen.findByTestId("consent-dialog");
    await userEvent.click(
      within(dialog).getByRole("button", { name: en.consent.agree }),
    );
    await waitFor(() => expect(nav.replace).toHaveBeenCalledWith("/en/home"));
    expect(
      api.callsTo("PATCH", `/v1/members/${PRIMARY}`).map((c) => c.body),
    ).toEqual([{ custom_alerts: ["msg"] }, { custom_alerts: ["msg"] }]);
  });

  it("editing types in profile never sends a members PATCH by itself", async () => {
    nav.pathname = "/en/profile";
    api
      .on(
        "GET",
        "/v1/me/user-types",
        out({
          answered: true,
          types: ["gym"],
          follow_ups: { gym_goal: "stay_fit" },
          active_type: "gym",
        }),
      )
      .on(
        "GET",
        "/v1/consents",
        consentStates({ terms: true, health_data: true }),
      )
      .on(
        "PUT",
        "/v1/me/user-types",
        out({
          answered: true,
          types: ["gym"],
          prefill: prefill([
            {
              field: "goal",
              current: "healthy_eating",
              value: "build_muscle",
              added: [],
              reason: "gym",
            },
          ]),
        }),
      );
    wrap(<ProfileFocus />);
    const link = await screen.findByRole("link", { name: en.user_types.edit });
    expect(link.getAttribute("href")).toBe("/en/welcome?edit=1");
    expect(await screen.findByText(en.modes.name.gym)).toBeTruthy();
    cleanup();

    nav.pathname = "/en/welcome";
    wrap(<WelcomeFlow edit />);
    // The same picker, prefilled from what is stored.
    await waitFor(() =>
      expect(tile("gym").getAttribute("aria-pressed")).toBe("true"),
    );
    await userEvent.click(button(en.user_types.continue));
    expect(
      (
        screen.getByRole("radio", {
          name: en.user_types.follow_up.gym.stay_fit,
        }) as HTMLInputElement
      ).checked,
    ).toBe(true);
    await userEvent.click(
      screen.getByRole("radio", {
        name: en.user_types.follow_up.gym.build_muscle,
      }),
    );
    await userEvent.click(button(en.user_types.continue));
    await screen.findByTestId("prefill-review");
    expect(api.callsTo("PUT", "/v1/me/user-types")).toHaveLength(1);
    expect(api.calls.filter((c) => c.method === "PATCH")).toHaveLength(0);
    await userEvent.click(button(en.user_types.prefill.not_now));
    await waitFor(() =>
      expect(nav.replace).toHaveBeenCalledWith("/en/profile"),
    );
    expect(api.calls.filter((c) => c.method === "PATCH")).toHaveLength(0);
  });

  it("no analytics events", async () => {
    api
      .on("GET", "/v1/me/user-types", out())
      .on(
        "GET",
        "/v1/consents",
        consentStates({ terms: true, health_data: true }),
      )
      .on(
        "PUT",
        "/v1/me/user-types",
        out({
          answered: true,
          prefill: prefill([
            {
              field: "conditions",
              current: [],
              value: ["pcos"],
              added: ["pcos"],
              reason: "health_condition",
            },
          ]),
        }),
      )
      .on("PATCH", `/v1/members/${PRIMARY}`, { id: PRIMARY });
    wrap(<WelcomeFlow edit={false} />);
    await screen.findByRole("heading", { level: 1, name: en.user_types.title });
    await userEvent.click(tile("health_condition"));
    await userEvent.click(button(en.user_types.continue));
    await userEvent.click(button(en.condition.pcos));
    await userEvent.click(button(en.user_types.continue));
    await screen.findByTestId("prefill-review");
    await userEvent.click(button(en.user_types.prefill.apply));
    await waitFor(() => expect(nav.replace).toHaveBeenCalled());
    expect(track).not.toHaveBeenCalled();
  });

  it("all copy from l10n", async () => {
    // Every leaf replaced by its own key: any visible text that is not a key
    // was hard-coded.
    const keyed = (o: unknown, p = ""): unknown =>
      typeof o === "object" && o !== null
        ? Object.fromEntries(
            Object.entries(o).map(([k, v]) => [
              k,
              keyed(v, p ? `${p}.${k}` : k),
            ]),
          )
        : `@${p}`;
    const messages = keyed(membersMessages(en)) as AbstractIntlMessages;
    api
      .on("GET", "/v1/me/user-types", out())
      .on(
        "GET",
        "/v1/consents",
        consentStates({ terms: true, health_data: true }),
      )
      .on(
        "PUT",
        "/v1/me/user-types",
        out({
          answered: true,
          prefill: prefill(
            [
              {
                field: "diet",
                current: "non_veg",
                value: "veg",
                added: [],
                reason: "allergy_diet",
              },
            ],
            ["weight_loss", "build_muscle"],
          ),
        }),
      );
    wrap(<WelcomeFlow edit={false} />, messages);
    const texts = () => {
      const walker = document.createTreeWalker(
        document.body,
        NodeFilter.SHOW_TEXT,
      );
      const out: string[] = [];
      for (let n = walker.nextNode(); n; n = walker.nextNode()) {
        const v = n.textContent?.trim();
        if (v) out.push(v);
      }
      return out;
    };
    const assertKeyed = () => {
      for (const v of texts()) expect(v).toMatch(/^@[a-z0-9_.]+$/);
    };
    await screen.findByRole("heading", { level: 1, name: "@user_types.title" });
    assertKeyed();
    for (const t of ["health_condition", "family", "gym"])
      await userEvent.click(tile(t));
    await userEvent.click(tile("eat_better"));
    assertKeyed();
    await userEvent.click(tile("family"));
    await userEvent.click(tile("allergy_diet"));
    await userEvent.click(button("@user_types.continue"));
    assertKeyed();
    await userEvent.click(button("@user_types.continue"));
    await screen.findByTestId("prefill-review");
    assertKeyed();
  });
});
