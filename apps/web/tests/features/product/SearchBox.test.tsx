import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { cleanup, render, screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { NextIntlClientProvider } from "next-intl";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import type { SearchHit } from "@/features/product/api/products";
import { SearchBox } from "@/features/product/components/SearchBox";
import { clientMessages } from "@/i18n/client-messages";
import { MESSAGES } from "../../support/analyze-fixtures";
import { apiStub, envelope, json } from "../../support/api-stub";

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
const HITS: SearchHit[] = [
  {
    product_id: "d0000000-0000-4000-8000-000000000009",
    barcode: null,
    name: "Masala Oats",
    brand: "Ours",
    grade: "B",
    source: "ours",
    attribution: null,
  },
  {
    product_id: null,
    barcode: "8901063201089",
    name: "Parle-G",
    brand: "Parle",
    grade: null,
    source: "off",
    attribution: "attribution.off",
  },
];

function view(props: Partial<Parameters<typeof SearchBox>[0]> = {}) {
  return render(
    <QueryClientProvider
      client={
        new QueryClient({ defaultOptions: { queries: { retry: false } } })
      }
    >
      <NextIntlClientProvider locale="en" messages={clientMessages(en)}>
        <SearchBox debounceMs={0} {...props} />
      </NextIntlClientProvider>
    </QueryClientProvider>,
  );
}

beforeEach(() => {
  fetchMock.mockReset();
});
afterEach(cleanup);

describe("SearchBox", () => {
  it("under 2 letters: a hint and no request", async () => {
    const api = apiStub(fetchMock).on("GET", "/v1/products/search", HITS);
    view();
    await userEvent.setup().type(screen.getByLabelText(en.search.title), "p");
    expect(await screen.findByText(en.search.too_short)).toBeTruthy();
    expect(api.callsTo("GET", "/v1/products/search")).toHaveLength(0);
  });

  it("results: name, brand, grade, source, links, and the OFF credit", async () => {
    const api = apiStub(fetchMock).on("GET", "/v1/products/search", HITS);
    view();
    await userEvent
      .setup()
      .type(screen.getByLabelText(en.search.title), "  pa ");
    const rows = await screen.findAllByTestId("search-hit");
    expect(rows).toHaveLength(2);
    expect(
      api.callsTo("GET", "/v1/products/search").at(-1)?.query.get("q"),
    ).toBe("pa");
    expect(
      within(rows[0])
        .getByRole("link", { name: /Masala Oats/ })
        .getAttribute("href"),
    ).toBe("/en/product/d0000000-0000-4000-8000-000000000009");
    expect(
      within(rows[1])
        .getByRole("link", { name: /Parle-G/ })
        .getAttribute("href"),
    ).toBe("/en/result/8901063201089");
    expect(within(rows[0]).getByText(en.search.source.ours)).toBeTruthy();
    expect(within(rows[1]).getByText(en.search.source.off)).toBeTruthy();
    expect(
      within(rows[0]).getByText(en.result.grade.replace("{grade}", "B")),
    ).toBeTruthy();
    // No grade: never a made-up one.
    expect(rows[1].textContent).not.toMatch(/Nutri-Score [A-E]/);
    expect(screen.getByText(en.attribution.off)).toBeTruthy();
  });

  it("compare mode: each hit links where the caller says", async () => {
    apiStub(fetchMock).on("GET", "/v1/products/search", HITS);
    view({ hrefFor: (h) => `/en/compare?b_barcode=${h.barcode ?? "x"}` });
    await userEvent.setup().type(screen.getByLabelText(en.search.title), "pa");
    const rows = await screen.findAllByTestId("search-hit");
    expect(within(rows[1]).getByRole("link").getAttribute("href")).toBe(
      "/en/compare?b_barcode=8901063201089",
    );
  });

  it("no results", async () => {
    apiStub(fetchMock).on("GET", "/v1/products/search", []);
    view();
    await userEvent.setup().type(screen.getByLabelText(en.search.title), "zzz");
    expect(await screen.findByText(en.search.no_results)).toBeTruthy();
  });

  it("error: the API code as text", async () => {
    apiStub(fetchMock).on(
      "GET",
      "/v1/products/search",
      json(429, envelope("rate_limited")),
    );
    view();
    await userEvent.setup().type(screen.getByLabelText(en.search.title), "pa");
    expect(await screen.findByText(en.error.rate_limited)).toBeTruthy();
  });
});
