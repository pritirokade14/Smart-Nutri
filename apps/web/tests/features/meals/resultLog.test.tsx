import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { cleanup, render, screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { NextIntlClientProvider } from "next-intl";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { ResultView } from "@/features/analysis/components/ResultView";
import { resultMessages } from "@/i18n/client-messages";
import { analyzeResponse, MESSAGES } from "../../support/analyze-fixtures";
import { apiStub, json } from "../../support/api-stub";

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

function view(body = analyzeResponse("sf_biscuit")) {
  const api = apiStub(fetchMock).on("POST", "/v1/analyze", body);
  render(
    <QueryClientProvider
      client={
        new QueryClient({ defaultOptions: { queries: { retry: false } } })
      }
    >
      <NextIntlClientProvider locale="en" messages={resultMessages(en)}>
        <ResultView barcode="8901063201089" />
      </NextIntlClientProvider>
    </QueryClientProvider>,
  );
  return api;
}

beforeEach(() => {
  fetchMock.mockReset();
});
afterEach(cleanup);

describe("result page: I ate this", () => {
  it("one button per member card", async () => {
    const body = analyzeResponse("sf_biscuit");
    view(body);
    const results = await screen.findAllByTestId("member-result");
    expect(results).toHaveLength(body.verdicts.length);
    for (const r of results) {
      expect(within(r).getByTestId("log-meal-cta")).toBeTruthy();
    }
  });

  it("each button has its own accessible name (the member's)", async () => {
    const body = analyzeResponse("sf_biscuit");
    view(body);
    await screen.findAllByTestId("member-result");
    const buttons = screen.getAllByTestId("log-meal-cta");
    const names = buttons.map((b) => b.getAttribute("aria-label"));
    expect(new Set(names).size).toBe(buttons.length);
    for (const n of names) expect(n).toContain(en.meals.log.cta);
    expect(names[0]).toContain(body.verdicts[0].member_name || en.result.you);
  });

  it("opens the dialog for that card's member and logs the product", async () => {
    const body = analyzeResponse("sf_biscuit");
    const target = body.verdicts[1];
    const api = view(body).on("POST", "/v1/meals", (c) =>
      json(201, {
        id: "c0000000-0000-4000-8000-000000000001",
        member_id: (c.body as { member_id: string }).member_id,
        product_id: body.product.product_id,
        barcode: body.product.product_id ? null : body.product.barcode,
        product_name: body.product.name,
        grade: "D",
        grams: 25,
        eaten_at: "2026-11-03T08:00:00+00:00",
        nutrients: {
          energy_kcal: null,
          sugars_g: null,
          salt_g: null,
          protein_g: null,
          fat_g: null,
          sat_fat_g: null,
          carbs_g: null,
        },
        client_id: null,
        attribution: null,
      }),
    );
    const results = await screen.findAllByTestId("member-result");
    const user = userEvent.setup();
    await user.click(within(results[1]).getByTestId("log-meal-cta"));
    const dialog = screen.getByTestId("log-meal-dialog");
    expect(within(dialog).getByText(en.meals.online_only)).toBeTruthy();
    expect(
      (within(dialog).getByLabelText(en.meals.log.member) as HTMLSelectElement)
        .value,
    ).toBe(target.member_id);
    if (body.product.serving_size_g == null) {
      await user.type(
        within(dialog).getByLabelText(en.meals.log.amount_grams),
        "30",
      );
    }
    await user.click(
      within(dialog).getByRole("button", { name: en.meals.log.save }),
    );
    await within(dialog).findByRole("button", { name: en.meals.log.undo });
    const sent = api.callsTo("POST", "/v1/meals")[0].body as Record<
      string,
      unknown
    >;
    expect(sent.member_id).toBe(target.member_id);
    if (body.product.product_id) {
      expect(sent.product_id).toBe(body.product.product_id);
      expect(sent).not.toHaveProperty("barcode");
    } else {
      expect(sent.barcode).toBe(body.product.barcode ?? "8901063201089");
      expect(sent).not.toHaveProperty("product_id");
    }
  });

  it("the result also offers Share and healthier options for the first member", async () => {
    const body = analyzeResponse("sf_biscuit");
    const id = body.product.product_id as string;
    const api = view(body).on("GET", `/v1/products/${id}/alternatives`, {
      items: [],
      reason: "no_category",
    });
    expect(
      await screen.findByText(en.alternatives.reason.no_category),
    ).toBeTruthy();
    expect(screen.getByRole("button", { name: en.share.button })).toBeTruthy();
    expect(
      api
        .callsTo("GET", `/v1/products/${id}/alternatives`)[0]
        .query.get("member_id"),
    ).toBe(body.verdicts[0].member_id);
  });
});
