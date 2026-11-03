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
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { Alternatives } from "@/features/product/components/Alternatives";
import { resultMessages } from "@/i18n/client-messages";
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
const ME = "a0000000-0000-4000-8000-000000000001";
const DAD = "b0000000-0000-4000-8000-000000000001";
const MEMBERS = [
  { id: ME, name: "", isPrimary: true, relation: "self" },
  { id: DAD, name: "Dad", isPrimary: false, relation: "parent" },
];
const PATH = "/v1/products/barcode/8901063201089/alternatives";

const item = (over: object = {}) => ({
  barcode: "8900000000011",
  product_id: null,
  name: "Oat Biscuit",
  brand: "Brand B",
  image_url: null,
  grade: "B",
  sugars_g: 8,
  high_in: [],
  member_status: "ok",
  attribution: "attribution.off",
  ...over,
});

function view(ref = { barcode: "8901063201089" } as const) {
  return render(
    <QueryClientProvider
      client={
        new QueryClient({ defaultOptions: { queries: { retry: false } } })
      }
    >
      <NextIntlClientProvider locale="en" messages={resultMessages(en)}>
        <Alternatives productRef={ref} members={MEMBERS} />
      </NextIntlClientProvider>
    </QueryClientProvider>,
  );
}

beforeEach(() => {
  fetchMock.mockReset();
});
afterEach(cleanup);

describe("Alternatives", () => {
  it("loading: a status while it loads", () => {
    fetchMock.mockImplementation(() => new Promise(() => {}));
    view();
    expect(screen.getByRole("status").textContent).toBe(en.common.loading);
  });

  it("error: Open Food Facts busy, with a retry", async () => {
    apiStub(fetchMock).on("GET", PATH, json(503, envelope("off_unavailable")));
    view();
    expect(
      await screen.findByText(en.scan.off_unavailable, {}, { timeout: 3000 }),
    ).toBeTruthy();
    expect(screen.getByRole("button", { name: en.common.retry })).toBeTruthy();
  });

  it("data: options with grade, sugars, member status, compare link and OFF credit", async () => {
    const api = apiStub(fetchMock).on("GET", PATH, {
      items: [
        item(),
        item({
          barcode: "8900000000028",
          name: "Rusk",
          grade: "C",
          sugars_g: null,
          member_status: "unknown",
        }),
      ],
      reason: "ok",
    });
    view();
    const rows = await screen.findAllByTestId("alternative");
    expect(rows).toHaveLength(2);
    expect(within(rows[0]).getByText("Oat Biscuit")).toBeTruthy();
    expect(
      within(rows[0]).getByText(en.alternatives.sugars.replace("{value}", "8")),
    ).toBeTruthy();
    // No sugar on the label: no number is invented.
    expect(rows[1].textContent).not.toContain("Sugars:");
    const badges = rows.map((r) =>
      within(r).getByTestId("verdict-badge").getAttribute("data-verdict"),
    );
    expect(badges).toEqual(["ok", "unknown"]);
    expect(
      within(rows[0])
        .getByRole("link", { name: en.alternatives.compare })
        .getAttribute("href"),
    ).toBe("/en/compare?a_barcode=8901063201089&b_barcode=8900000000011");
    expect(
      within(rows[0])
        .getByRole("link", { name: "Oat Biscuit" })
        .getAttribute("href"),
    ).toBe("/en/result/8900000000011");
    expect(screen.getByText(en.attribution.off)).toBeTruthy();
    expect(screen.getByText(en.alternatives.subtitle)).toBeTruthy();
    // For the primary member by default.
    expect(api.callsTo("GET", PATH)[0].query.get("member_id")).toBe(ME);
  });

  it("never lists an option that is avoid for the chosen member (Ruling M1)", async () => {
    apiStub(fetchMock).on("GET", PATH, {
      items: [item({ member_status: "avoid", name: "Choco Bar" }), item()],
      reason: "ok",
    });
    view();
    const rows = await screen.findAllByTestId("alternative");
    expect(rows).toHaveLength(1);
    expect(screen.queryByText("Choco Bar")).toBeNull();
  });

  it("all options avoid for the member: 'no better found', never an avoid product", async () => {
    apiStub(fetchMock).on("GET", PATH, {
      items: [item({ member_status: "avoid" })],
      reason: "ok",
    });
    view();
    expect(
      await screen.findByText(en.alternatives.reason.no_better_found),
    ).toBeTruthy();
    expect(screen.queryAllByTestId("alternative")).toHaveLength(0);
  });

  it.each(["no_category", "no_better_found", "source_ungraded"] as const)(
    "empty with reason %s",
    async (reason) => {
      apiStub(fetchMock).on("GET", PATH, { items: [], reason });
      view();
      expect(
        await screen.findByText(en.alternatives.reason[reason]),
      ).toBeTruthy();
    },
  );

  it("choosing another member asks for that member's statuses", async () => {
    const api = apiStub(fetchMock).on("GET", PATH, {
      items: [item()],
      reason: "ok",
    });
    view();
    await screen.findAllByTestId("alternative");
    await userEvent
      .setup()
      .selectOptions(screen.getByLabelText(en.history.member), DAD);
    await waitFor(() =>
      expect(
        api.callsTo("GET", PATH).some((c) => c.query.get("member_id") === DAD),
      ).toBe(true),
    );
    expect(
      await screen.findByText(
        en.alternatives.for_member.replace("{name}", "Dad"),
      ),
    ).toBeTruthy();
  });

  it("our own product asks by product id", async () => {
    const id = "d0000000-0000-4000-8000-000000000009";
    const api = apiStub(fetchMock).on(
      "GET",
      `/v1/products/${id}/alternatives`,
      { items: [], reason: "no_category" },
    );
    render(
      <QueryClientProvider client={new QueryClient()}>
        <NextIntlClientProvider locale="en" messages={resultMessages(en)}>
          <Alternatives productRef={{ productId: id }} members={MEMBERS} />
        </NextIntlClientProvider>
      </QueryClientProvider>,
    );
    await screen.findByText(en.alternatives.reason.no_category);
    expect(api.callsTo("GET", `/v1/products/${id}/alternatives`)).toHaveLength(
      1,
    );
  });
});
