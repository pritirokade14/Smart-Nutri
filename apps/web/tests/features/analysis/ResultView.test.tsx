import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { cleanup, render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { NextIntlClientProvider } from "next-intl";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import {
  analyzeErrorView,
  shouldRetryAnalyze,
} from "@/features/analysis/api/useAnalyzeBarcode";
import { ResultView } from "@/features/analysis/components/ResultView";
import { resultMessages } from "@/i18n/client-messages";
import { ApiError } from "@/lib/api/errors";
import {
  type AnalyzeOut,
  analyzeResponse,
  MESSAGES,
  type TestLocale,
} from "../../support/analyze-fixtures";

// The real getApi() and generated client, over a stubbed fetch.
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

const json = (status: number, body: unknown) =>
  new Response(JSON.stringify(body), {
    status,
    headers: { "content-type": "application/json" },
  });
const envelope = (code: string) => ({
  error: { code, message_key: `error.${code}`, details: {} },
});

function view(barcode = "8901063201089", locale: TestLocale = "en") {
  const client = new QueryClient({
    defaultOptions: { queries: { retry: false } },
  });
  return render(
    <QueryClientProvider client={client}>
      <NextIntlClientProvider
        locale={locale}
        messages={resultMessages(MESSAGES[locale])}
      >
        <ResultView barcode={barcode} />
      </NextIntlClientProvider>
    </QueryClientProvider>,
  );
}

const en = MESSAGES.en;

beforeEach(() => {
  fetchMock.mockReset();
});
afterEach(cleanup);

async function lastBody() {
  const req = fetchMock.mock.calls.at(-1)?.[0] as Request;
  return { url: req.url, method: req.method, body: await req.clone().json() };
}

describe("ResultView success", () => {
  it("posts barcode + language and renders the product, grade, chips, cards and disclaimer", async () => {
    const body = analyzeResponse("sf_biscuit");
    fetchMock.mockResolvedValue(json(200, body));
    const { container } = view("8901063201089", "hi");
    await screen.findAllByTestId("verdict-card");
    expect(await lastBody()).toEqual({
      url: "http://127.0.0.1:8000/v1/analyze",
      method: "POST",
      body: { barcode: "8901063201089", language: "hi" },
    });
    expect(
      screen.getByRole("heading", { level: 1, name: "Sugar Free Biscuit" }),
    ).toBeTruthy();
    expect(
      screen.getByText(MESSAGES.hi.result.grade.replace("{grade}", "D")),
    ).toBeTruthy();
    expect(screen.getByText(MESSAGES.hi.nutriscore.calculated_by)).toBeTruthy();
    expect(screen.getByText(MESSAGES.hi.high_in.sat_fat)).toBeTruthy();
    // One card per verdict, in API order, with the API status.
    const cards = screen.getAllByTestId("verdict-card");
    expect(cards.map((c) => c.getAttribute("data-status"))).toEqual(
      body.verdicts.map((v) => v.status),
    );
    // Once per result view, not per card.
    expect(screen.getAllByText(MESSAGES.hi.common.disclaimer).length).toBe(1);
    expect(screen.queryByText(MESSAGES.hi.attribution.off)).toBeNull();
    const again = screen.getByRole("link", {
      name: MESSAGES.hi.result.scan_another,
    });
    expect(again.getAttribute("href")).toBe("/hi/scan");
    expect(container.querySelector("[style]")).toBeNull();
  });

  it("treats a grade outside A–E as no grade and hides unknown high_in codes", async () => {
    const body = structuredClone(analyzeResponse("sf_biscuit"));
    body.report = {
      ...body.report,
      nutriscore: { grade: "F" },
      high_in: ["salt", "mystery"],
    };
    fetchMock.mockResolvedValue(json(200, body));
    const { container } = view();
    expect(
      await screen.findByText(en.nutriscore.insufficient_data),
    ).toBeTruthy();
    expect(container.textContent).not.toContain("Nutri-Score F");
    expect(screen.getByText(en.high_in.salt)).toBeTruthy();
    expect(container.textContent).not.toContain("mystery");
  });

  it("shows the insufficient-data note when there is no grade", async () => {
    const body = structuredClone(analyzeResponse("oats"));
    body.report = {
      ...body.report,
      nutriscore: { grade: null, reason: "insufficient_data" },
    };
    fetchMock.mockResolvedValue(json(200, body));
    view();
    expect(
      await screen.findByText(en.nutriscore.insufficient_data),
    ).toBeTruthy();
    expect(screen.queryByText(/^Nutri-Score [A-E]$/)).toBeNull();
  });

  it("credits Open Food Facts only for an OFF product", async () => {
    const off: AnalyzeOut = structuredClone(analyzeResponse("sf_biscuit"));
    off.product = {
      ...off.product,
      attribution: "openfoodfacts",
      source: "openfoodfacts",
      barcode: "8901063201089",
      product_id: null,
    };
    fetchMock.mockResolvedValue(json(200, off));
    view();
    const link = await screen.findByRole("link", { name: en.attribution.off });
    expect(link.getAttribute("href")).toBe(
      "https://world.openfoodfacts.org/product/8901063201089",
    );
    expect(link.getAttribute("rel")).toContain("noopener");
    expect(screen.getByText(en.common.disclaimer)).toBeTruthy();
  });
});

describe("ResultView errors", () => {
  it("404 product_not_found → not-found with retry (no API retry)", async () => {
    fetchMock.mockResolvedValue(json(404, envelope("product_not_found")));
    view();
    expect(await screen.findByText(en.scan.not_found)).toBeTruthy();
    expect(fetchMock).toHaveBeenCalledTimes(1);
    expect(screen.getByText(en.common.disclaimer)).toBeTruthy();
    fetchMock.mockResolvedValue(json(200, analyzeResponse("water")));
    await userEvent.click(screen.getByRole("button", { name: en.scan.retry }));
    expect((await screen.findAllByTestId("verdict-card")).length).toBe(9);
  });

  it("503 off_unavailable → retried once, then off-unavailable with retry", async () => {
    fetchMock.mockImplementation(async () =>
      json(503, envelope("off_unavailable")),
    );
    view();
    expect(
      await screen.findByText(en.scan.off_unavailable, undefined, {
        timeout: 4000,
      }),
    ).toBeTruthy();
    expect(fetchMock).toHaveBeenCalledTimes(2);
    expect(screen.getByRole("button", { name: en.scan.retry })).toBeTruthy();
  });

  it("422 invalid_barcode → invalid message and scan-another, no retry button", async () => {
    fetchMock.mockResolvedValue(json(422, envelope("invalid_barcode")));
    view();
    expect(await screen.findByText(en.error.invalid_barcode)).toBeTruthy();
    expect(screen.queryByRole("button", { name: en.scan.retry })).toBeNull();
    expect(
      screen.getByRole("link", { name: en.result.scan_another }),
    ).toBeTruthy();
  });

  it("network failure → error.network", async () => {
    fetchMock.mockImplementation(async () => {
      throw new TypeError("Failed to fetch");
    });
    view();
    expect(await screen.findByText(en.error.network)).toBeTruthy();
  });

  it("an unknown error code → error.internal_error; a known one → error.<code>", async () => {
    fetchMock.mockResolvedValue(json(500, envelope("brand_new_failure")));
    view();
    expect(await screen.findByText(en.error.internal_error)).toBeTruthy();
    cleanup();
    fetchMock.mockResolvedValue(json(429, envelope("rate_limited")));
    view();
    expect(await screen.findByText(en.error.rate_limited)).toBeTruthy();
    expect(fetchMock).toHaveBeenCalledTimes(2);
  });

  it("an invalid barcode in the URL never calls the API", async () => {
    view("abc");
    expect(await screen.findByText(en.error.invalid_barcode)).toBeTruthy();
    expect(fetchMock).not.toHaveBeenCalled();
  });
});

describe("retry and error mapping", () => {
  it("retries only a 503, at most once", () => {
    expect(shouldRetryAnalyze(0, new ApiError("off_unavailable", 503))).toBe(
      true,
    );
    expect(shouldRetryAnalyze(1, new ApiError("off_unavailable", 503))).toBe(
      false,
    );
    for (const s of [400, 401, 404, 422, 429])
      expect(shouldRetryAnalyze(0, new ApiError("x", s))).toBe(false);
    expect(shouldRetryAnalyze(0, new ApiError("network"))).toBe(false);
    expect(shouldRetryAnalyze(0, new ApiError("internal_error", 500))).toBe(
      false,
    );
  });
  it("maps codes to states", () => {
    expect(analyzeErrorView(new ApiError("product_not_found", 404))).toEqual({
      kind: "not_found",
      messageKey: "scan.not_found",
    });
    expect(analyzeErrorView(new ApiError("off_unavailable", 503))).toEqual({
      kind: "unavailable",
      messageKey: "scan.off_unavailable",
    });
    expect(analyzeErrorView(new ApiError("invalid_barcode", 422))).toEqual({
      kind: "invalid",
      messageKey: "error.invalid_barcode",
    });
    expect(analyzeErrorView(new ApiError("network"))).toEqual({
      kind: "error",
      messageKey: "error.network",
    });
    expect(analyzeErrorView(new ApiError("rate_limited", 429))).toEqual({
      kind: "error",
      messageKey: "error.rate_limited",
    });
  });
});

describe("ResultView loading", () => {
  it("shows loading while the request is pending", async () => {
    fetchMock.mockReturnValue(new Promise(() => {}));
    view();
    expect(await screen.findByText(en.common.loading)).toBeTruthy();
    await waitFor(() => expect(fetchMock).toHaveBeenCalled());
  });
});
