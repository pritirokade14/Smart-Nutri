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
import { ConsentDialog } from "@/features/members/components/ConsentDialog";
import { ConsentSettings } from "@/features/members/components/ConsentSettings";
import { MembersList } from "@/features/members/components/MembersList";
import { membersMessages } from "@/i18n/client-messages";
import { MESSAGES } from "../../support/analyze-fixtures";
import { apiStub, consentStates, envelope, json } from "../../support/api-stub";

vi.mock("next/navigation", () => ({
  useRouter: () => ({ push: vi.fn(), replace: vi.fn() }),
}));
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
  api = apiStub(fetchMock);
});
afterEach(cleanup);

function wrap(ui: ReactNode) {
  const client = new QueryClient({
    defaultOptions: { queries: { retry: false } },
  });
  return render(
    <QueryClientProvider client={client}>
      <NextIntlClientProvider locale="en" messages={membersMessages(en)}>
        {ui}
      </NextIntlClientProvider>
    </QueryClientProvider>,
  );
}

function dialog() {
  const onAgreed = vi.fn();
  const onCancel = vi.fn();
  wrap(<ConsentDialog onAgreed={onAgreed} onCancel={onCancel} />);
  return { onAgreed, onCancel };
}

const agreeButton = () =>
  screen.getByRole("button", { name: en.consent.agree }) as HTMLButtonElement;

describe("ConsentDialog", () => {
  it("shows the health data and AI texts, and records health_data at the current version", async () => {
    api
      .on("GET", "/v1/consents", consentStates({}))
      .on("POST", "/v1/consents", consentStates({ health_data: true }));
    const { onAgreed } = dialog();
    const d = screen.getByRole("dialog");
    expect(within(d).getByText(en.consent.health_data.title)).toBeTruthy();
    expect(within(d).getByText(en.consent.health_data.body)).toBeTruthy();
    expect(within(d).getByText(en.consent.ai_processing.body)).toBeTruthy();
    expect(within(d).getByText(en.common.disclaimer, { exact: false }));
    await waitFor(() => expect(agreeButton().disabled).toBe(false));
    await userEvent.click(agreeButton());
    await waitFor(() => expect(onAgreed).toHaveBeenCalledTimes(1));
    expect(api.callsTo("POST", "/v1/consents").map((c) => c.body)).toEqual([
      { purpose: "health_data", version: "2026-11-01", granted: true },
    ]);
  });

  it("records AI explanations too only when ticked", async () => {
    api
      .on("GET", "/v1/consents", consentStates({}))
      .on("POST", "/v1/consents", consentStates({ health_data: true }));
    const { onAgreed } = dialog();
    await waitFor(() => expect(agreeButton().disabled).toBe(false));
    await userEvent.click(
      screen.getByRole("checkbox", {
        name: new RegExp(en.consent.ai_processing.title),
      }),
    );
    await userEvent.click(agreeButton());
    await waitFor(() => expect(onAgreed).toHaveBeenCalledTimes(1));
    expect(api.callsTo("POST", "/v1/consents").map((c) => c.body)).toEqual([
      { purpose: "health_data", version: "2026-11-01", granted: true },
      { purpose: "ai_processing", version: "2026-11-01", granted: true },
    ]);
  });

  it("a failed AI grant never blocks saving", async () => {
    api
      .on("GET", "/v1/consents", consentStates({}))
      .on("POST", "/v1/consents", (c) =>
        (c.body as { purpose: string }).purpose === "ai_processing"
          ? json(500, envelope("internal_error"))
          : json(200, consentStates({ health_data: true })),
      );
    const { onAgreed } = dialog();
    await waitFor(() => expect(agreeButton().disabled).toBe(false));
    await userEvent.click(screen.getByRole("checkbox"));
    await userEvent.click(agreeButton());
    await waitFor(() => expect(onAgreed).toHaveBeenCalledTimes(1));
  });

  it("decline records nothing", async () => {
    api.on("GET", "/v1/consents", consentStates({}));
    const { onAgreed, onCancel } = dialog();
    await userEvent.click(
      screen.getByRole("button", { name: en.consent.decline }),
    );
    expect(onCancel).toHaveBeenCalledTimes(1);
    expect(onAgreed).not.toHaveBeenCalled();
    expect(api.callsTo("POST", "/v1/consents")).toHaveLength(0);
  });

  it("a changed consent text shows the i18n error and reloads the version", async () => {
    api
      .on("GET", "/v1/consents", consentStates({}))
      .on(
        "POST",
        "/v1/consents",
        json(422, envelope("consent_version_mismatch")),
      );
    const { onAgreed } = dialog();
    await waitFor(() => expect(agreeButton().disabled).toBe(false));
    await userEvent.click(agreeButton());
    expect((await screen.findByRole("alert")).textContent).toBe(
      en.error.consent_version_mismatch,
    );
    expect(onAgreed).not.toHaveBeenCalled();
    await waitFor(() =>
      expect(api.callsTo("GET", "/v1/consents")).toHaveLength(2),
    );
  });

  it("hides the AI tick when AI explanations are already on", async () => {
    api.on("GET", "/v1/consents", consentStates({ ai_processing: true }));
    dialog();
    await waitFor(() => expect(agreeButton().disabled).toBe(false));
    expect(screen.queryByRole("checkbox")).toBeNull();
  });
});

describe("ConsentSettings (profile)", () => {
  it("shows each state and withdraws", async () => {
    api
      .on("GET", "/v1/consents", consentStates({ health_data: true }))
      .on("POST", "/v1/consents", consentStates({}));
    wrap(<ConsentSettings />);
    const health = await screen.findByTestId("consent-health_data");
    const ai = screen.getByTestId("consent-ai_processing");
    expect(within(health).getByTestId("consent-state").textContent).toBe(
      en.consent.granted,
    );
    expect(within(ai).getByTestId("consent-state").textContent).toBe(
      en.consent.not_granted,
    );
    await userEvent.click(
      within(health).getByRole("button", { name: en.consent.withdraw }),
    );
    await waitFor(() =>
      expect(within(health).getByTestId("consent-state").textContent).toBe(
        en.consent.not_granted,
      ),
    );
    expect(api.callsTo("POST", "/v1/consents").map((c) => c.body)).toEqual([
      { purpose: "health_data", version: "2026-11-01", granted: false },
    ]);
    // Withdrawal keeps saved data in use; the notice says so.
    expect(
      within(health).getByText(en.members.consent_withdrawn_notice),
    ).toBeTruthy();
  });

  it("shows an error state with retry", async () => {
    api.on("GET", "/v1/consents", json(500, envelope("internal_error")));
    wrap(<ConsentSettings />);
    expect(await screen.findByText(en.error.internal_error)).toBeTruthy();
    expect(screen.getByRole("button", { name: en.common.retry })).toBeTruthy();
  });
});

const member = (i: number, over: object = {}) => ({
  id: `00000000-0000-4000-8000-${String(i).padStart(12, "0")}`,
  name: `M${i}`,
  relation: "child",
  birth_year: 2015,
  sex: null,
  height_cm: null,
  weight_kg: null,
  diet: "veg",
  allergens: [],
  conditions: [],
  custom_alerts: [],
  goal: null,
  is_primary: false,
  ...over,
});

describe("MembersList", () => {
  it("lists members in API order with edit links and the add button", async () => {
    api.on("GET", "/v1/members", [
      member(1, {
        name: "Asha",
        relation: "self",
        is_primary: true,
        birth_year: null,
      }),
      member(2, { name: "Dad", relation: "parent", birth_year: 1960 }),
    ]);
    wrap(<MembersList />);
    const rows = await screen.findAllByTestId("member-row");
    expect(rows.map((r) => r.textContent)).toEqual([
      expect.stringContaining("Asha"),
      expect.stringContaining("Dad"),
    ]);
    expect(within(rows[0] as HTMLElement).getByText(en.members.you_badge));
    expect(
      within(rows[1] as HTMLElement).getByText(
        `${en.members.relation.parent} · ${en.members.born.replace("{year}", "1960")}`,
      ),
    ).toBeTruthy();
    expect(
      within(rows[1] as HTMLElement)
        .getByRole("link", { name: en.members.edit })
        .getAttribute("href"),
    ).toBe("/en/members/00000000-0000-4000-8000-000000000002");
    expect(
      screen.getByRole("link", { name: en.members.add }).getAttribute("href"),
    ).toBe("/en/members/new");
  });

  it("hides add at 10 members", async () => {
    api.on(
      "GET",
      "/v1/members",
      Array.from({ length: 10 }, (_, i) => member(i)),
    );
    wrap(<MembersList />);
    expect(await screen.findByText(en.members.limit_reached)).toBeTruthy();
    expect(screen.queryByRole("link", { name: en.members.add })).toBeNull();
  });

  it("shows loading, then an error with retry", async () => {
    api.on("GET", "/v1/members", json(500, envelope("internal_error")));
    wrap(<MembersList />);
    expect(screen.getByRole("status").textContent).toBe(en.common.loading);
    expect(await screen.findByText(en.error.internal_error)).toBeTruthy();
  });
});
