import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { cleanup, render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { NextIntlClientProvider } from "next-intl";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { GuideSettings } from "@/features/targets/components/GuideSettings";
import { membersMessages } from "@/i18n/client-messages";
import { MESSAGES } from "../../support/analyze-fixtures";
import { apiStub, consentStates, envelope, json } from "../../support/api-stub";

const nav = vi.hoisted(() => ({ push: vi.fn(), replace: vi.fn() }));
vi.mock("next/navigation", () => ({
  usePathname: () => "/en/profile/guide",
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

let api: ReturnType<typeof apiStub>;
beforeEach(() => {
  fetchMock.mockReset();
  nav.push.mockReset();
  api = apiStub(fetchMock)
    .on("GET", "/v1/members", [
      {
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
      },
    ])
    .on(
      "GET",
      "/v1/targets/settings",
      json(403, envelope("consent_required", { purposes: ["health_data"] })),
    )
    .on("GET", "/v1/consents", consentStates({ terms: true }))
    .on("DELETE", "/v1/targets/settings", json(204));
});
afterEach(cleanup);

function wrap() {
  const client = new QueryClient({
    defaultOptions: { queries: { retry: false } },
  });
  render(
    <QueryClientProvider client={client}>
      <NextIntlClientProvider locale="en" messages={membersMessages(en)}>
        <GuideSettings />
      </NextIntlClientProvider>
    </QueryClientProvider>,
  );
}

describe("guide settings after health_data is withdrawn", () => {
  it("still sends the Numbers choice to the display route", async () => {
    api.on("PUT", "/v1/targets/display", { numbers_display: "hide_all" });
    wrap();
    await screen.findByTestId("guide-settings");
    await userEvent.click(
      screen.getByRole("radio", { name: en.settings.diary.numbers.hide_all }),
    );
    await waitFor(() =>
      expect(api.callsTo("PUT", "/v1/targets/display")[0]?.body).toEqual({
        numbers_display: "hide_all",
      }),
    );
  });

  it("a 404 from display shows neutral copy", async () => {
    api.on(
      "PUT",
      "/v1/targets/display",
      json(404, envelope("goal_settings_not_found")),
    );
    wrap();
    await screen.findByTestId("guide-settings");
    await userEvent.click(
      screen.getByRole("radio", { name: en.settings.diary.numbers.hide_all }),
    );
    expect(
      await screen.findByText(en.error.goal_settings_not_found),
    ).toBeTruthy();
  });

  it("reset stays reachable", async () => {
    wrap();
    await screen.findByTestId("guide-settings");
    expect(
      (
        screen.getByRole("button", {
          name: en.settings.diary.reset,
        }) as HTMLButtonElement
      ).disabled,
    ).toBe(false);
  });
});
