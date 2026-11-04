import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { act, cleanup, render, screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { NextIntlClientProvider } from "next-intl";
import { Suspense } from "react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { compareRef } from "@/features/product/lib/compareRefs";
import { clientMessages } from "@/i18n/client-messages";
import { MESSAGES } from "../../support/analyze-fixtures";
import { apiStub, envelope, json } from "../../support/api-stub";

vi.mock("next-intl/server", async () => {
  const { MESSAGES } = await import("../../support/analyze-fixtures");
  const { createTranslator } = await import("next-intl");
  return {
    setRequestLocale: () => {},
    getMessages: async ({ locale }: { locale: "en" | "hi" | "mr" }) =>
      MESSAGES[locale],
    getTranslations: async ({ locale }: { locale: "en" | "hi" | "mr" }) =>
      createTranslator({ locale, messages: MESSAGES[locale] }),
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
const track = vi.hoisted(() => vi.fn());
vi.mock("@/lib/analytics", () => ({ track }));

const en = MESSAGES.en;
const ID = "d0000000-0000-4000-8000-000000000009";
const ME = "a0000000-0000-4000-8000-000000000001";
const member = {
  id: ME,
  name: "",
  relation: "self",
  birth_year: null,
  sex: null,
  height_cm: null,
  weight_kg: null,
  diet: "non_veg",
  allergens: [],
  conditions: [],
  custom_alerts: [],
  goal: null,
  is_primary: true,
};
const per100 = {
  energy_kcal: 400,
  sugars_g: 10,
  salt_g: 1,
  sat_fat_g: 2,
  protein_g: 6,
  fiber_g: 3,
  fat_g: 9,
  carbs_g: 60,
  sodium_mg: null,
};
const side = (name: string, over: object = {}) => ({
  product_id: null,
  barcode: "8901063201089",
  name,
  brand: null,
  grade: "C",
  per_100g: per100,
  high_in: [],
  member_status: "caution",
  attribution: "attribution.off",
  ...over,
});
const COMPARE = {
  a: side("First"),
  b: side("Second", { product_id: ID, barcode: null, attribution: null }),
  better: {
    grade: "same",
    energy_kcal: "same",
    sugars_g: "same",
    salt_g: "same",
    sat_fat_g: "same",
    protein_g: "same",
    fiber_g: "same",
  },
};

async function page(sp: Record<string, string>) {
  const { default: Page } = await import("@/app/[locale]/(app)/compare/page");
  const ui = await Page({
    params: Promise.resolve({ locale: "en" }),
    searchParams: Promise.resolve(sp),
  });
  await act(async () => {
    render(
      <QueryClientProvider
        client={
          new QueryClient({ defaultOptions: { queries: { retry: false } } })
        }
      >
        <NextIntlClientProvider locale="en" messages={clientMessages(en)}>
          <Suspense>{ui}</Suspense>
        </NextIntlClientProvider>
      </QueryClientProvider>,
    );
  });
}

beforeEach(() => {
  fetchMock.mockReset();
  track.mockReset();
});
afterEach(cleanup);

describe("compare refs", () => {
  it("exactly one valid id or barcode per side", () => {
    expect(compareRef({ a: ID.toUpperCase() }, "a")).toEqual({ productId: ID });
    expect(compareRef({ a_barcode: "8901-0632-01089" }, "a")).toEqual({
      barcode: "8901063201089",
    });
    expect(compareRef({ a: ID, a_barcode: "8901063201089" }, "a")).toBeNull();
    expect(compareRef({ a: "dad" }, "a")).toBeNull();
    expect(compareRef({ a_barcode: "12" }, "a")).toBeNull();
    expect(compareRef({ a: ["x", "y"] }, "a")).toBeNull();
    expect(compareRef({}, "b")).toBeNull();
  });
});

describe("compare page", () => {
  it("an invalid reference never reaches the API", async () => {
    await page({ a: "not-a-uuid" });
    expect(screen.getByText(en.error.invalid_product_ref)).toBeTruthy();
    expect(fetchMock).not.toHaveBeenCalled();
  });

  it("two products: the table for the primary member, the disclaimer, an event name", async () => {
    const api = apiStub(fetchMock)
      .on("GET", "/v1/members", [member])
      .on("GET", "/v1/products/compare", COMPARE);
    await page({ a_barcode: "8901063201089", b: ID });
    expect(await screen.findByTestId("compare-table")).toBeTruthy();
    const q = api.callsTo("GET", "/v1/products/compare")[0].query;
    expect(q.get("a_barcode")).toBe("8901063201089");
    expect(q.get("b")).toBe(ID);
    expect(q.get("member_id")).toBe(ME);
    expect(q.has("a")).toBe(false);
    expect(screen.getAllByTestId("verdict-badge")).toHaveLength(2);
    expect(screen.getByTestId("disclaimer")).toBeTruthy();
    expect(track).toHaveBeenCalledWith("compare_viewed");
  });

  it("an API error shows its text with a retry", async () => {
    apiStub(fetchMock)
      .on("GET", "/v1/members", [member])
      .on(
        "GET",
        "/v1/products/compare",
        json(404, envelope("product_not_found")),
      );
    await page({ a_barcode: "8901063201089", b: ID });
    expect(await screen.findByText(en.error.product_not_found)).toBeTruthy();
  });

  it("one product: search for the second, which links back to compare", async () => {
    apiStub(fetchMock)
      .on("GET", "/v1/members", [member])
      .on("GET", "/v1/products/search", [
        {
          product_id: ID,
          barcode: null,
          name: "Masala Oats",
          brand: null,
          grade: "B",
          source: "ours",
          attribution: null,
        },
      ]);
    await page({ a_barcode: "8901063201089" });
    await userEvent
      .setup()
      .type(screen.getByLabelText(en.compare.pick_second), "oats");
    const hit = await screen.findByTestId("search-hit", {}, { timeout: 3000 });
    expect(within(hit).getByRole("link").getAttribute("href")).toBe(
      `/en/compare?a_barcode=8901063201089&b=${ID}`,
    );
  });
});

describe("search page", () => {
  it("title, hint and the search box", async () => {
    const { default: Page } = await import("@/app/[locale]/(app)/search/page");
    await act(async () => {
      render(
        <QueryClientProvider client={new QueryClient()}>
          <NextIntlClientProvider locale="en" messages={clientMessages(en)}>
            <Suspense>
              <Page params={Promise.resolve({ locale: "en" })} />
            </Suspense>
          </NextIntlClientProvider>
        </QueryClientProvider>,
      );
    });
    expect(
      await screen.findByRole("heading", { level: 1, name: en.search.title }),
    ).toBeTruthy();
    expect(screen.getByText(en.search.hint)).toBeTruthy();
    expect(screen.getByLabelText(en.search.placeholder)).toBeTruthy();
  });
});
