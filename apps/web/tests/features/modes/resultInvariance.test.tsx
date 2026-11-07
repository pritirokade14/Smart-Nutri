import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { cleanup, render, screen } from "@testing-library/react";
import { NextIntlClientProvider } from "next-intl";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { AppNav } from "@/components/shell/AppNav";
import { ResultView } from "@/features/analysis/components/ResultView";
import type { UserType } from "@/features/modes/layouts";
import { userTypesKey } from "@/features/user-types/api/userTypes";
import { resultMessages } from "@/i18n/client-messages";
import { analyzeResponse, MESSAGES } from "../../support/analyze-fixtures";
import { apiStub } from "../../support/api-stub";

// Decision 7 / Review Focus 1: scan, verdicts and allergy checks are the
// same in every mode. The result is rendered inside the mode's shell for
// all six modes; the verdict region's accessible tree must be identical.

vi.mock("next/navigation", () => ({
  usePathname: () => "/en/result/0",
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

const MODES: UserType[] = [
  "health_condition",
  "family",
  "weight_loss",
  "gym",
  "allergy_diet",
  "eat_better",
];
const en = MESSAGES.en;
beforeEach(() => {
  fetchMock.mockReset();
});
afterEach(cleanup);

/** Roles, names, states and verdict tones of the region, in document order. */
function tree(el: Element): string[] {
  const out: string[] = [];
  const walk = (n: Element) => {
    const attrs = ["role", "aria-label", "data-verdict", "data-testid"]
      .map((a) => (n.hasAttribute(a) ? `${a}=${n.getAttribute(a)}` : ""))
      .filter(Boolean)
      .join(" ");
    const own = [...n.childNodes]
      .filter((c) => c.nodeType === Node.TEXT_NODE)
      .map((c) => c.textContent?.trim())
      .filter(Boolean)
      .join(" ");
    if (attrs || own) out.push(`${n.tagName.toLowerCase()} ${attrs} ${own}`);
    for (const c of n.children) walk(c);
  };
  walk(el);
  return out;
}

async function verdictRegion(product: string, mode: UserType) {
  const body = analyzeResponse(product);
  apiStub(fetchMock)
    .on("POST", "/v1/analyze", body)
    .on("GET", `/v1/products/${body.product.product_id}/alternatives`, {
      items: [],
      reason: "no_category",
    })
    .on("GET", "/v1/members", []);
  const client = new QueryClient({
    defaultOptions: { queries: { retry: false } },
  });
  client.setQueryData(userTypesKey, {
    types: [mode],
    follow_ups: {},
    active_type: mode,
    answered: true,
    answered_at: null,
    prefill: null,
  });
  render(
    <QueryClientProvider client={client}>
      <NextIntlClientProvider locale="en" messages={resultMessages(en)}>
        <AppNav locale="en" variant="bar" />
        <ResultView productId={body.product.product_id as string} />
      </NextIntlClientProvider>
    </QueryClientProvider>,
  );
  await screen.findAllByTestId("member-result");
  const region = screen
    .getAllByTestId("member-result")[0]
    ?.closest("section") as Element;
  const snapshot = [
    ...tree(region),
    // The disclaimer is part of every verdict view.
    String(screen.getAllByText(en.common.disclaimer, { exact: false }).length),
  ];
  // The shell really is in this mode (else the test proves nothing).
  const tabs = screen.getAllByTestId("nav-tab").map((l) => l.textContent);
  cleanup();
  return { snapshot, tabs };
}

describe("result screen identical in every mode", () => {
  it.each(["cola", "sf_biscuit"])("%s", async (product) => {
    const results = [];
    for (const mode of MODES) results.push(await verdictRegion(product, mode));
    const first = results[0]?.snapshot ?? [];
    expect(first.some((l) => l.includes("data-verdict="))).toBe(true);
    for (const r of results) expect(r.snapshot).toEqual(first);
    // Five different shells around the same verdicts (weight_loss and gym share
    // their tabs since the Diary took Compare's place, Plan 11 spec 7.10).
    expect(new Set(results.map((r) => r.tabs.join("|"))).size).toBe(5);
  });
});
