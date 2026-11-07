import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { cleanup, render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { NextIntlClientProvider } from "next-intl";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { GuideSettings } from "@/features/targets/components/GuideSettings";
import { membersMessages } from "@/i18n/client-messages";
import { MESSAGES } from "../../support/analyze-fixtures";
import { apiStub, consentStates, json } from "../../support/api-stub";
import { targetsFixture } from "../../support/targets-fixtures";

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
const settings = {
  member_id: PRIMARY,
  direction: "lose",
  activity_level: "light",
  rate_pct_bw_per_week: 0.5,
  target_weight_kg: null,
  sex_reference: null,
  pregnant_or_breastfeeding: false,
  fat_pct_energy: null,
  energy_mode: "formula",
  numbers_display: "show",
  summary_view: "remaining",
  updated_at: "2026-11-07T00:00:00Z",
};

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
    .on("GET", "/v1/targets/settings", settings)
    .on(
      "GET",
      "/v1/consents",
      consentStates({ terms: true, health_data: true }),
    )
    .on("POST", "/v1/targets/preview", targetsFixture("g2_lose_adjusted"))
    .on("PUT", "/v1/targets/display", {
      ...settings,
      numbers_display: "hide_all",
    })
    .on("DELETE", "/v1/targets/settings", json(204));
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
});
afterEach(cleanup);

describe("guide settings", () => {
  it("is prefilled from the stored settings", async () => {
    await screen.findByTestId("guide-settings");
    const lose = screen.getByRole("radio", {
      name: en.targets.direction.lose,
    }) as HTMLInputElement;
    expect(lose.checked).toBe(true);
    expect(await screen.findByTestId("guide-rows")).toBeTruthy();
  });

  it("changing Numbers uses the terms-only display route", async () => {
    await screen.findByTestId("guide-settings");
    await userEvent.click(
      screen.getByRole("radio", { name: en.settings.diary.numbers.hide_all }),
    );
    await waitFor(() =>
      expect(api.callsTo("PUT", "/v1/targets/display")[0]?.body).toEqual({
        numbers_display: "hide_all",
      }),
    );
    expect(api.callsTo("PUT", "/v1/targets/settings")).toHaveLength(0);
  });

  it("reset asks first, then deletes the settings", async () => {
    await screen.findByTestId("guide-settings");
    await userEvent.click(
      screen.getByRole("button", { name: en.settings.diary.reset }),
    );
    expect(
      await screen.findByText(en.settings.diary.reset_confirm),
    ).toBeTruthy();
    expect(api.callsTo("DELETE", "/v1/targets/settings")).toHaveLength(0);
    const dialog = screen.getByTestId("confirm-dialog");
    await userEvent.click(
      dialog.querySelectorAll("button")[1] as HTMLButtonElement,
    );
    await waitFor(() =>
      expect(api.callsTo("DELETE", "/v1/targets/settings")).toHaveLength(1),
    );
    await waitFor(() => expect(nav.push).toHaveBeenCalledWith("/en/profile"));
  });
});
