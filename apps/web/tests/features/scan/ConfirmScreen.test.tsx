import messages from "@smartnutri/i18n/messages/en.json";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { cleanup, render, screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { NextIntlClientProvider } from "next-intl";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { setScanDraft } from "@/features/scan/api/draftCache";
import { ConfirmScreen } from "@/features/scan/components/ConfirmScreen";
import {
  type DraftCase,
  envelope,
  json,
  scanDraft,
} from "../../support/drafts";

const router = vi.hoisted(() => ({ push: vi.fn(), replace: vi.fn() }));
vi.mock("next/navigation", () => ({ useRouter: () => router }));
vi.mock("@/lib/supabase/client", () => ({
  createSupabaseBrowserClient: () => ({
    auth: {
      getSession: async () => ({
        data: { session: { access_token: "tok" } },
      }),
    },
  }),
}));
const track = vi.hoisted(() => vi.fn());
vi.mock("@/lib/analytics", () => ({ track }));
const fetchMock = vi.hoisted(() => {
  const fn = vi.fn();
  globalThis.fetch = fn as unknown as typeof fetch;
  return fn;
});

const c = messages.confirm;
const BARCODE = "8901063201089";
const PRODUCT_ID = "7d1d2f8a-1111-4c3b-9a0e-0123456789ab";

function view(
  name: DraftCase | null,
  opts: { cached?: boolean; barcode?: string | null } = {},
) {
  const client = new QueryClient({
    defaultOptions: { queries: { retry: false } },
  });
  const scan = name ? scanDraft(name) : null;
  if (scan && opts.cached !== false)
    setScanDraft(client, scan, opts.barcode ?? BARCODE);
  render(
    <QueryClientProvider client={client}>
      <NextIntlClientProvider locale="en" messages={messages}>
        <ConfirmScreen
          scanId={scan ? scan.scan_id : null}
          barcode={opts.barcode ?? BARCODE}
        />
      </NextIntlClientProvider>
    </QueryClientProvider>,
  );
  return { client, scan };
}

async function lastRequest() {
  const req = fetchMock.mock.calls.at(-1)?.[0] as Request;
  return { url: req.url, method: req.method, body: await req.clone().json() };
}

const productOut = {
  source: "smartnutri",
  product_id: PRODUCT_ID,
  barcode: BARCODE,
  name: "Masala Oats",
  brand: "Saffola",
  image_url: null,
  category: "general",
  per_100g: {},
  serving_size_g: null,
  ingredients: [],
  claims: [],
  attribution: null,
};

beforeEach(() => {
  fetchMock.mockReset();
  router.push.mockReset();
  router.replace.mockReset();
  track.mockReset();
});
afterEach(cleanup);

describe("ConfirmScreen", () => {
  it("always offers Retake and Enter manually, and the not-medical-advice note", () => {
    view("clean");
    expect(
      screen
        .getByRole("link", { name: messages.label.retake })
        .getAttribute("href"),
    ).toBe(`/en/scan/label?barcode=${BARCODE}`);
    expect(
      screen
        .getByRole("link", { name: messages.label.enter_manually })
        .getAttribute("href"),
    ).toBe(`/en/scan/manual?barcode=${BARCODE}`);
    expect(screen.getByText(c.not_medical_advice)).toBeTruthy();
  });

  it("save → products_create → the result view for the new product", async () => {
    fetchMock.mockResolvedValue(json(201, productOut));
    const { client, scan } = view("clean");
    await userEvent.click(screen.getByRole("button", { name: c.save }));
    await vi.waitFor(() =>
      expect(router.push).toHaveBeenCalledWith(`/en/product/${PRODUCT_ID}`),
    );
    const req = await lastRequest();
    expect(req.url).toBe("http://127.0.0.1:8000/v1/products");
    expect(req.method).toBe("POST");
    expect(req.body.scan_id).toBe(scan?.scan_id);
    expect(req.body.barcode).toBe(BARCODE);
    expect(track.mock.calls).toEqual([
      ["scan_completed", { method: "label", found: true }],
    ]);
    // The draft is dropped once saved.
    expect(
      client.getQueryCache().findAll({ queryKey: ["scan-draft"] }),
    ).toHaveLength(0);
  });

  it("low_confidence offers Retake and still saves as a scan (scan_id kept, never re-posted as manual)", async () => {
    fetchMock.mockResolvedValue(json(201, productOut));
    const { scan } = view("low_confidence");
    const banner = screen.getByTestId("warning-low_confidence");
    expect(banner).toBeTruthy();
    expect(
      screen.getByRole("link", { name: messages.label.retake }),
    ).toBeTruthy();
    await userEvent.click(screen.getByRole("button", { name: c.save }));
    await vi.waitFor(() => expect(fetchMock).toHaveBeenCalled());
    expect((await lastRequest()).body.scan_id).toBe(scan?.scan_id);
  });

  it("product_exists with a product_id offers to open that product", async () => {
    fetchMock.mockResolvedValue(
      json(409, envelope("product_exists", { product_id: PRODUCT_ID })),
    );
    view("clean");
    await userEvent.click(screen.getByRole("button", { name: c.save }));
    expect(await screen.findByText(messages.error.product_exists)).toBeTruthy();
    expect(
      screen.getByRole("link", { name: c.open_existing }).getAttribute("href"),
    ).toBe(`/en/product/${PRODUCT_ID}`);
    expect(router.push).not.toHaveBeenCalled();
  });

  it("product_exists without a product_id shows only the message", async () => {
    fetchMock.mockResolvedValue(json(409, envelope("product_exists")));
    view("clean");
    await userEvent.click(screen.getByRole("button", { name: c.save }));
    expect(await screen.findByText(messages.error.product_exists)).toBeTruthy();
    expect(screen.queryByRole("link", { name: c.open_existing })).toBeNull();
  });

  it("422 implausible_value highlights each field in details.fields, next to the field", async () => {
    fetchMock.mockResolvedValue(
      json(
        422,
        envelope("implausible_value", { fields: ["nutrients.sugars_g"] }),
      ),
    );
    view("clean");
    await userEvent.click(screen.getByRole("button", { name: c.save }));
    const row = await screen.findByTestId("row-sugars_g");
    await vi.waitFor(() =>
      expect(row.getAttribute("data-highlight")).toBe("true"),
    );
    expect(
      within(row).getByText(messages.error.implausible_value),
    ).toBeTruthy();
    expect(within(row).getByRole("textbox").getAttribute("aria-invalid")).toBe(
      "true",
    );
  });

  it("422 validation_error shows next to the named field", async () => {
    fetchMock.mockResolvedValue(
      json(422, envelope("validation_error", { fields: ["body.sodium_unit"] })),
    );
    view("clean");
    await userEvent.click(screen.getByRole("button", { name: c.save }));
    expect(
      await screen.findAllByText(messages.error.validation_error),
    ).not.toHaveLength(0);
  });

  it("a draft that is no longer in memory → scan_not_found with Retake and Enter manually, no form", async () => {
    view("clean", { cached: false });
    expect(await screen.findByText(messages.error.scan_not_found)).toBeTruthy();
    expect(
      screen.getByRole("link", { name: messages.label.retake }),
    ).toBeTruthy();
    expect(
      screen.getByRole("link", { name: messages.label.enter_manually }),
    ).toBeTruthy();
    expect(screen.queryByRole("button", { name: c.save })).toBeNull();
  });

  it("manual entry (no scan) posts without scan_id", async () => {
    fetchMock.mockResolvedValue(json(201, productOut));
    view(null);
    await userEvent.type(screen.getByLabelText(c.name), "Home Chivda");
    await userEvent.click(
      screen.getByRole("radio", { name: c.category_option.general }),
    );
    await userEvent.click(
      screen.getByRole("radio", { name: c.basis_option.per_100g }),
    );
    await userEvent.click(screen.getByRole("button", { name: c.save }));
    await vi.waitFor(() => expect(router.push).toHaveBeenCalled());
    const req = await lastRequest();
    expect("scan_id" in req.body).toBe(false);
    expect(req.body.barcode).toBe(BARCODE);
    expect(track.mock.calls).toEqual([
      ["scan_completed", { method: "manual", found: true }],
    ]);
  });
});
