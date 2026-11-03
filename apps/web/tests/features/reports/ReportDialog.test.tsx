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
import { ResultView } from "@/features/analysis/components/ResultView";
import { ReportButton } from "@/features/reports/components/ReportDialog";
import { resultMessages } from "@/i18n/client-messages";
import { analyzeResponse, MESSAGES } from "../../support/analyze-fixtures";
import { apiStub, envelope, json } from "../../support/api-stub";

vi.mock("next/navigation", () => ({
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
const track = vi.hoisted(() => vi.fn());
vi.mock("@/lib/analytics", () => ({ track, resetAnalytics: vi.fn() }));
const fetchMock = vi.hoisted(() => {
  const fn = vi.fn();
  globalThis.fetch = fn as unknown as typeof fetch;
  return fn;
});

const en = MESSAGES.en;
const PRODUCT = "62e22ce8-476b-5780-b460-b6230c4c5d6e";
const PATH = `/v1/products/${PRODUCT}/reports`;
let api: ReturnType<typeof apiStub>;
beforeEach(() => {
  fetchMock.mockReset();
  track.mockClear();
  api = apiStub(fetchMock);
});
afterEach(cleanup);

function wrap(ui: React.ReactNode) {
  const client = new QueryClient({
    defaultOptions: { queries: { retry: false } },
  });
  render(
    <QueryClientProvider client={client}>
      <NextIntlClientProvider locale="en" messages={resultMessages(en)}>
        {ui}
      </NextIntlClientProvider>
    </QueryClientProvider>,
  );
}

const reportOut = (reason: string) => ({
  id: "c1d2e3f4-0000-4000-8000-000000000001",
  product_id: PRODUCT,
  reason,
  status: "open",
  created_at: "2026-11-04T10:00:00Z",
});

async function open() {
  await userEvent.click(screen.getByRole("button", { name: en.report.button }));
  return screen.getByRole("dialog");
}

describe("ReportDialog", () => {
  it("ReportDialog posts reason+note and shows report.thanks", async () => {
    api.on("POST", PATH, (c) =>
      json(201, reportOut((c.body as { reason: string }).reason)),
    );
    wrap(<ReportButton productId={PRODUCT} />);
    const dialog = await open();
    expect(within(dialog).getByText(en.report.title)).toBeTruthy();
    const submit = within(dialog).getByRole("button", {
      name: en.report.submit,
    }) as HTMLButtonElement;
    expect(submit.disabled).toBe(true);
    await userEvent.click(
      within(dialog).getByRole("radio", {
        name: en.report.reason.wrong_values,
      }),
    );
    await userEvent.type(
      within(dialog).getByLabelText(en.report.note_label),
      "  Sugar is 5 g on the pack  ",
    );
    expect(within(dialog).getByText(en.report.note_hint)).toBeTruthy();
    await userEvent.click(submit);
    expect(await within(dialog).findByText(en.report.thanks)).toBeTruthy();
    expect(api.callsTo("POST", PATH).map((c) => c.body)).toEqual([
      { reason: "wrong_values", note: "Sugar is 5 g on the pack" },
    ]);
    expect(track).toHaveBeenCalledWith("report_submitted", {
      reason: "wrong_values",
    });
  });

  it("a blank note is not sent, and a duplicate (200) also thanks", async () => {
    api.on("POST", PATH, json(200, reportOut("other")));
    wrap(<ReportButton productId={PRODUCT} />);
    const dialog = await open();
    await userEvent.click(
      within(dialog).getByRole("radio", { name: en.report.reason.other }),
    );
    await userEvent.type(
      within(dialog).getByLabelText(en.report.note_label),
      "   ",
    );
    await userEvent.click(
      within(dialog).getByRole("button", { name: en.report.submit }),
    );
    expect(await within(dialog).findByText(en.report.thanks)).toBeTruthy();
    expect(api.callsTo("POST", PATH).map((c) => c.body)).toEqual([
      { reason: "other" },
    ]);
  });

  it("ReportDialog shows rate_limited on 429", async () => {
    api.on("POST", PATH, json(429, envelope("rate_limited")));
    wrap(<ReportButton productId={PRODUCT} />);
    const dialog = await open();
    await userEvent.click(
      within(dialog).getByRole("radio", {
        name: en.report.reason.wrong_product,
      }),
    );
    await userEvent.click(
      within(dialog).getByRole("button", { name: en.report.submit }),
    );
    expect(await within(dialog).findByText(en.error.rate_limited)).toBeTruthy();
    expect(within(dialog).queryByText(en.report.thanks)).toBeNull();
    expect(track).not.toHaveBeenCalled();
  });

  it("the note is capped at 500 characters, like the API", async () => {
    wrap(<ReportButton productId={PRODUCT} />);
    const dialog = await open();
    expect(
      within(dialog)
        .getByLabelText(en.report.note_label)
        .getAttribute("maxlength"),
    ).toBe("500");
  });

  it("cancel closes without sending", async () => {
    wrap(<ReportButton productId={PRODUCT} />);
    const dialog = await open();
    await userEvent.click(
      within(dialog).getByRole("button", { name: en.common.cancel }),
    );
    expect(screen.queryByRole("dialog")).toBeNull();
    expect(api.calls).toHaveLength(0);
  });
});

describe("Report a problem on the result", () => {
  it("is offered for a product in our catalogue", async () => {
    const body = analyzeResponse("cola");
    api.on("POST", "/v1/analyze", body);
    wrap(<ResultView productId={body.product.product_id as string} />);
    expect(
      await screen.findByRole("button", { name: en.report.button }),
    ).toBeTruthy();
  });

  it("tracks verdicts_shown with only the member count", async () => {
    const body = analyzeResponse("cola");
    api.on("POST", "/v1/analyze", body);
    wrap(<ResultView productId={body.product.product_id as string} />);
    await screen.findByRole("button", { name: en.report.button });
    expect(track).toHaveBeenCalledWith("verdicts_shown", {
      member_count: body.verdicts.length,
    });
  });

  it("is not offered for an Open Food Facts product (nothing to report against)", async () => {
    const body = analyzeResponse("cola");
    api.on("POST", "/v1/analyze", {
      ...body,
      product: { ...body.product, product_id: null, source: "openfoodfacts" },
    });
    wrap(<ResultView barcode="8901063201089" />);
    await waitFor(() =>
      expect(screen.getAllByTestId("verdict-card").length).toBeGreaterThan(0),
    );
    expect(screen.queryByRole("button", { name: en.report.button })).toBeNull();
  });
});
