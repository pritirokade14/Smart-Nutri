import type { components } from "@smartnutri/api-client";
import {
  type QueryClient,
  type UseQueryResult,
  useQuery,
} from "@tanstack/react-query";
import { normalizeBarcode } from "@/features/scan/lib/barcode";
import { getApi } from "@/lib/api/client";
import { type ApiError, networkError, toApiError } from "@/lib/api/errors";

export type AnalyzeOut = components["schemas"]["AnalyzeOut"];
export type AnalyzeLanguage =
  components["schemas"]["AnalyzeRequest"]["language"];

/** POST /v1/analyze for the account's primary member. Throws ApiError. */
export async function analyzeBarcode(
  barcode: string,
  language: AnalyzeLanguage,
): Promise<AnalyzeOut> {
  const api = getApi(); // a misconfigured base URL is not a network error
  const result = await api
    .POST("/v1/analyze", { body: { barcode, language } })
    .catch(() => {
      throw networkError();
    });
  if (result.error !== undefined || !result.data) {
    throw toApiError(result.error, result.response.status);
  }
  return result.data;
}

/** POST /v1/analyze for a saved product (e.g. a confirmed label scan). */
export async function analyzeProduct(
  productId: string,
  language: AnalyzeLanguage,
): Promise<AnalyzeOut> {
  const api = getApi();
  const result = await api
    .POST("/v1/analyze", { body: { product_id: productId, language } })
    .catch(() => {
      throw networkError();
    });
  if (result.error !== undefined || !result.data) {
    throw toApiError(result.error, result.response.status);
  }
  return result.data;
}

const UUID = /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i;

/** A product id is a UUID; anything else never reaches the API. */
export function normalizeProductId(id: string): string | null {
  return UUID.test(id) ? id.toLowerCase() : null;
}

/** Never retry a 4xx (or anything else); retry a 503 (OFF busy) once. */
export function shouldRetryAnalyze(
  failureCount: number,
  error: ApiError,
): boolean {
  return error.status === 503 && failureCount < 1;
}

export type AnalyzeErrorView = {
  kind: "not_found" | "unavailable" | "invalid" | "error";
  /** i18n key; for "error" the caller falls back to error.internal_error if missing. */
  messageKey: string;
};

export function analyzeErrorView(error: ApiError): AnalyzeErrorView {
  switch (error.code) {
    case "product_not_found":
      return { kind: "not_found", messageKey: "scan.not_found" };
    case "off_unavailable":
      return { kind: "unavailable", messageKey: "scan.off_unavailable" };
    case "invalid_barcode":
      return { kind: "invalid", messageKey: "error.invalid_barcode" };
    default:
      return { kind: "error", messageKey: `error.${error.code}` };
  }
}

/** Drops every cached verdict (health data) on sign-out. */
export function clearAnalyzeCache(client: QueryClient): void {
  client.removeQueries({ queryKey: ["analyze"] });
}

/** What to analyse: a barcode, or a saved product's id. */
export type AnalyzeRef = { barcode: string } | { productId: string };

/**
 * Analyse a product. Each call records a scan on the server, so the result is
 * never refetched in the background (focus, reconnect, remount). An invalid
 * barcode or id never reaches the API.
 */
export function useAnalyze(
  ref: AnalyzeRef,
  language: AnalyzeLanguage,
): UseQueryResult<AnalyzeOut, ApiError> {
  const byId = "productId" in ref;
  const key = byId
    ? normalizeProductId(ref.productId)
    : normalizeBarcode(ref.barcode);
  return useQuery<AnalyzeOut, ApiError>({
    queryKey: byId
      ? ["analyze", "product", key, language]
      : ["analyze", key, language],
    queryFn: () =>
      byId
        ? analyzeProduct(key as string, language)
        : analyzeBarcode(key as string, language),
    enabled: key !== null,
    retry: shouldRetryAnalyze,
    gcTime: 0, // health data: not kept once nobody is looking at it
    staleTime: Number.POSITIVE_INFINITY,
    refetchOnWindowFocus: false,
    refetchOnReconnect: false,
    refetchOnMount: false,
  });
}

/** Analyse a barcode (see useAnalyze). */
export function useAnalyzeBarcode(
  barcode: string,
  language: AnalyzeLanguage,
): UseQueryResult<AnalyzeOut, ApiError> {
  return useAnalyze({ barcode }, language);
}
