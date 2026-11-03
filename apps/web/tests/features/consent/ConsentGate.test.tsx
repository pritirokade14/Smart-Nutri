import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import {
  act,
  cleanup,
  render,
  screen,
  waitFor,
  within,
} from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { NextIntlClientProvider } from "next-intl";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { ConsentGate } from "@/features/consent/components/ConsentGate";
import { ConsentSettings } from "@/features/members/components/ConsentSettings";
import { clientMessages } from "@/i18n/client-messages";
import { getApi } from "@/lib/api/client";
import { MESSAGES } from "../../support/analyze-fixtures";
import { apiStub, consentStates, envelope, json } from "../../support/api-stub";

const nav = vi.hoisted(() => ({ pathname: "/en/home" }));
vi.mock("next/navigation", () => ({
  usePathname: () => nav.pathname,
  useRouter: () => ({ push: vi.fn(), replace: vi.fn() }),
}));
const signOut = vi.hoisted(() => vi.fn(async () => ({ error: null })));
vi.mock("@/lib/supabase/client", () => ({
  createSupabaseBrowserClient: () => ({
    auth: {
      getSession: async () => ({
        data: { session: { access_token: "token" } },
      }),
      signOut,
    },
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
  nav.pathname = "/en/home";
  fetchMock.mockReset();
  signOut.mockClear();
  api = apiStub(fetchMock);
});
afterEach(cleanup);

function gate(child = <p>{"app page"}</p>) {
  const client = new QueryClient({
    defaultOptions: { queries: { retry: false } },
  });
  render(
    <QueryClientProvider client={client}>
      <NextIntlClientProvider locale="en" messages={clientMessages(en)}>
        <ConsentGate>{child}</ConsentGate>
      </NextIntlClientProvider>
    </QueryClientProvider>,
  );
  return client;
}

const agree = () =>
  screen.getByRole("button", { name: en.consent.agree }) as HTMLButtonElement;

describe("ConsentGate (terms acceptance, G1)", () => {
  it("shows a loading state, then the page when terms are agreed", async () => {
    api.on("GET", "/v1/consents", consentStates({ terms: true }));
    gate();
    expect(screen.getByText(en.common.loading)).toBeTruthy();
    expect(await screen.findByText("app page")).toBeTruthy();
    expect(screen.queryByTestId("terms-step")).toBeNull();
  });

  it("shows an error with retry when consents can't be loaded", async () => {
    api.on("GET", "/v1/consents", (_c, n) =>
      n === 1
        ? json(500, envelope("internal_error"))
        : json(200, consentStates({ terms: true })),
    );
    gate();
    expect(await screen.findByText(en.error.internal_error)).toBeTruthy();
    expect(screen.queryByText("app page")).toBeNull();
    await userEvent.click(
      screen.getByRole("button", { name: en.common.retry }),
    );
    expect(await screen.findByText("app page")).toBeTruthy();
  });

  it("after first sign-in, asks for terms and records them at the current version", async () => {
    api
      .on("GET", "/v1/consents", consentStates({}))
      .on("POST", "/v1/consents", consentStates({ terms: true }));
    gate();
    const step = await screen.findByTestId("terms-step");
    expect(screen.queryByText("app page")).toBeNull();
    expect(
      within(step).getByRole("heading", { name: en.consent.terms_step.title }),
    ).toBeTruthy();
    expect(
      within(step)
        .getByRole("link", { name: en.consent.terms_step.read_terms })
        .getAttribute("href"),
    ).toBe("/en/terms");
    expect(
      within(step)
        .getByRole("link", { name: en.consent.terms_step.read_privacy })
        .getAttribute("href"),
    ).toBe("/en/privacy");
    expect(within(step).getByText(en.common.disclaimer)).toBeTruthy();
    await userEvent.click(agree());
    expect(await screen.findByText("app page")).toBeTruthy();
    expect(api.callsTo("POST", "/v1/consents").map((c) => c.body)).toEqual([
      { purpose: "terms", version: "2026-11-01", granted: true },
    ]);
  });

  it("records the optional AI consent only when ticked", async () => {
    api
      .on("GET", "/v1/consents", consentStates({}))
      .on("POST", "/v1/consents", (c) =>
        json(
          200,
          consentStates({
            terms: true,
            ai_processing:
              (c.body as { purpose: string }).purpose === "ai_processing",
          }),
        ),
      );
    gate();
    await screen.findByTestId("terms-step");
    await userEvent.click(
      screen.getByRole("checkbox", {
        name: new RegExp(en.consent.ai_processing.title),
      }),
    );
    await userEvent.click(agree());
    await screen.findByText("app page");
    expect(api.callsTo("POST", "/v1/consents").map((c) => c.body)).toEqual([
      { purpose: "terms", version: "2026-11-01", granted: true },
      { purpose: "ai_processing", version: "2026-11-01", granted: true },
    ]);
  });

  it("re-prompts with the updated wording when terms need an update", async () => {
    api.on("GET", "/v1/consents", consentStates({}, ["terms"]));
    gate();
    const step = await screen.findByTestId("terms-step");
    expect(
      within(step).getByRole("heading", {
        name: en.consent.terms_step.updated_title,
      }),
    ).toBeTruthy();
    expect(
      within(step).getByText(en.consent.terms_step.updated_body),
    ).toBeTruthy();
  });

  it("decline signs out", async () => {
    api.on("GET", "/v1/consents", consentStates({}));
    const assign = vi.fn();
    vi.stubGlobal("location", { ...window.location, assign });
    gate();
    await screen.findByTestId("terms-step");
    await userEvent.click(
      screen.getByRole("button", { name: en.auth.signOut }),
    );
    await waitFor(() => expect(signOut).toHaveBeenCalled());
    vi.unstubAllGlobals();
  });

  it("the profile page stays reachable without terms (to withdraw or delete)", async () => {
    nav.pathname = "/en/profile";
    api.on("GET", "/v1/consents", consentStates({}));
    gate();
    expect(await screen.findByText("app page")).toBeTruthy();
    expect(screen.queryByTestId("terms-step")).toBeNull();
  });

  it("consent_required routes to consent screen (terms withdrawn mid-session)", async () => {
    let terms = true;
    api
      .on("GET", "/v1/consents", () => json(200, consentStates({ terms })))
      .on(
        "POST",
        "/v1/analyze",
        json(403, envelope("consent_required", { purposes: ["terms"] })),
      );
    gate();
    await screen.findByText("app page");
    terms = false; // withdrawn on another device
    await act(async () => {
      await getApi().POST("/v1/analyze", {
        body: { barcode: "8901063201089", language: "en" },
      });
    });
    expect(await screen.findByTestId("terms-step")).toBeTruthy();
    expect(screen.queryByText("app page")).toBeNull();
  });

  it("consent_required for ai_processing asks for that consent in a dialog", async () => {
    api
      .on("GET", "/v1/consents", consentStates({ terms: true }))
      .on(
        "POST",
        "/v1/consents",
        consentStates({ terms: true, ai_processing: true }),
      )
      .on(
        "POST",
        "/v1/voice/ask",
        json(
          403,
          envelope("consent_required", { purposes: ["ai_processing"] }),
        ),
      );
    gate();
    await screen.findByText("app page");
    await act(async () => {
      await getApi().POST("/v1/voice/ask", { body: {} as never });
    });
    const dialog = await screen.findByTestId("consent-prompt");
    expect(
      within(dialog).getByText(en.consent.ai_processing.title),
    ).toBeTruthy();
    expect(screen.getByText("app page")).toBeTruthy();
    await userEvent.click(
      within(dialog).getByRole("button", { name: en.consent.agree }),
    );
    await waitFor(() =>
      expect(screen.queryByTestId("consent-prompt")).toBeNull(),
    );
    expect(api.callsTo("POST", "/v1/consents").map((c) => c.body)).toEqual([
      { purpose: "ai_processing", version: "2026-11-01", granted: true },
    ]);
  });

  it("re-prompts for an updated health_data consent, and Not now dismisses it", async () => {
    api.on(
      "GET",
      "/v1/consents",
      consentStates({ terms: true }, ["health_data"]),
    );
    gate();
    const dialog = await screen.findByTestId("consent-prompt");
    expect(within(dialog).getByText(en.consent.health_data.title)).toBeTruthy();
    expect(within(dialog).getByText(en.consent.needs_update)).toBeTruthy();
    await userEvent.click(
      within(dialog).getByRole("button", { name: en.consent.decline }),
    );
    expect(screen.queryByTestId("consent-prompt")).toBeNull();
    expect(screen.getByText("app page")).toBeTruthy();
    expect(api.callsTo("POST", "/v1/consents")).toHaveLength(0);
  });
});

describe("ConsentSettings (profile)", () => {
  function settings() {
    const client = new QueryClient({
      defaultOptions: { queries: { retry: false } },
    });
    render(
      <QueryClientProvider client={client}>
        <NextIntlClientProvider locale="en" messages={clientMessages(en)}>
          <ConsentSettings />
        </NextIntlClientProvider>
      </QueryClientProvider>,
    );
  }

  it("shows every consent, terms first", async () => {
    api.on("GET", "/v1/consents", consentStates({ terms: true }));
    settings();
    await screen.findByTestId("consent-terms");
    expect(
      screen
        .getAllByTestId(/^consent-(terms|health_data|ai_processing)$/)
        .map((e) => e.dataset.testid),
    ).toEqual([
      "consent-terms",
      "consent-health_data",
      "consent-ai_processing",
    ]);
  });

  it("an outdated consent says so and offers Review and agree", async () => {
    api
      .on(
        "GET",
        "/v1/consents",
        consentStates({ terms: true }, ["ai_processing"]),
      )
      .on(
        "POST",
        "/v1/consents",
        consentStates({ terms: true, ai_processing: true }),
      );
    settings();
    const card = await screen.findByTestId("consent-ai_processing");
    expect(within(card).getByText(en.consent.needs_update)).toBeTruthy();
    await userEvent.click(
      within(card).getByRole("button", { name: en.consent.review_agree }),
    );
    await waitFor(() =>
      expect(within(card).getByTestId("consent-state").textContent).toBe(
        en.consent.granted,
      ),
    );
    expect(api.callsTo("POST", "/v1/consents").map((c) => c.body)).toEqual([
      { purpose: "ai_processing", version: "2026-11-01", granted: true },
    ]);
  });

  it("withdraw terms consent asks first, then calls the API (scanning stops)", async () => {
    api
      .on("GET", "/v1/consents", consentStates({ terms: true }))
      .on("POST", "/v1/consents", consentStates({}));
    settings();
    const card = await screen.findByTestId("consent-terms");
    await userEvent.click(
      within(card).getByRole("button", { name: en.consent.withdraw }),
    );
    const confirm = screen.getByTestId("confirm-dialog");
    expect(
      within(confirm).getByText(en.consent.terms.withdraw_confirm),
    ).toBeTruthy();
    expect(api.callsTo("POST", "/v1/consents")).toHaveLength(0);
    await userEvent.click(
      within(confirm).getByRole("button", { name: en.consent.withdraw }),
    );
    await waitFor(() =>
      expect(api.callsTo("POST", "/v1/consents").map((c) => c.body)).toEqual([
        { purpose: "terms", version: "2026-11-01", granted: false },
      ]),
    );
  });

  it("withdraw health consent calls the API without a confirm step", async () => {
    api
      .on(
        "GET",
        "/v1/consents",
        consentStates({ terms: true, health_data: true }),
      )
      .on("POST", "/v1/consents", consentStates({ terms: true }));
    settings();
    const card = await screen.findByTestId("consent-health_data");
    await userEvent.click(
      within(card).getByRole("button", { name: en.consent.withdraw }),
    );
    await waitFor(() =>
      expect(api.callsTo("POST", "/v1/consents").map((c) => c.body)).toEqual([
        { purpose: "health_data", version: "2026-11-01", granted: false },
      ]),
    );
  });
});
