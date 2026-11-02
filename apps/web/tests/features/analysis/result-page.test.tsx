import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { cleanup, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";
import { clientMessages, resultMessages } from "@/i18n/client-messages";
import { analyzeResponse, MESSAGES } from "../../support/analyze-fixtures";

vi.mock("next-intl/server", async () => {
  const { MESSAGES } = await import("../../support/analyze-fixtures");
  return {
    setRequestLocale: () => {},
    getMessages: async ({ locale }: { locale: "en" | "hi" | "mr" }) =>
      MESSAGES[locale],
  };
});
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

afterEach(cleanup);

const VERDICT_NAMESPACES = [
  "verdict",
  "status",
  "reason",
  "reason_variant",
  "nutrient",
  "allergen",
  "diet",
];

describe("result messages", () => {
  it("the root client catalogue strips the verdict namespaces", () => {
    const m = clientMessages(MESSAGES.en);
    for (const ns of VERDICT_NAMESPACES) expect(m).not.toHaveProperty(ns);
  });
  it("the result catalogue adds back exactly what the verdict UI needs", () => {
    const m = resultMessages(MESSAGES.en);
    for (const ns of VERDICT_NAMESPACES) expect(m).toHaveProperty(ns);
    for (const ns of ["claim_verdict", "claim_reason", "condition"])
      expect(m).not.toHaveProperty(ns);
    // Everything the root client provider has is still there.
    for (const ns of Object.keys(clientMessages(MESSAGES.en)))
      expect(m).toHaveProperty(ns);
  });
});

describe("result page", () => {
  it("wraps the result view in a provider that has the verdict namespaces", async () => {
    fetchMock.mockResolvedValue(
      new Response(JSON.stringify(analyzeResponse("sf_biscuit")), {
        status: 200,
        headers: { "content-type": "application/json" },
      }),
    );
    const { default: Page } = await import(
      "@/app/[locale]/(app)/result/[barcode]/page"
    );
    const ui = await Page({
      params: Promise.resolve({ locale: "mr", barcode: "8901063201089" }),
    });
    // No outer NextIntlClientProvider: the page must bring its own.
    render(
      <QueryClientProvider client={new QueryClient()}>
        {ui}
      </QueryClientProvider>,
    );
    const cards = await screen.findAllByTestId("verdict-card");
    expect(cards.length).toBe(9);
    expect(
      screen.getAllByText(MESSAGES.mr.status.avoid).length,
    ).toBeGreaterThan(0);
    expect(document.body.textContent).not.toMatch(/reason\.|status\./);
  });
});
