import type { components } from "@smartnutri/api-client";
import { type UseQueryResult, useQuery } from "@tanstack/react-query";
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

/**
 * Analyse a barcode. Each call records a scan on the server, so the result is
 * never refetched in the background (focus, reconnect, remount).
 */
export function useAnalyzeBarcode(
  barcode: string,
  language: AnalyzeLanguage,
): UseQueryResult<AnalyzeOut, ApiError> {
  const code = normalizeBarcode(barcode);
  return useQuery<AnalyzeOut, ApiError>({
    queryKey: ["analyze", code, language],
    queryFn: () => analyzeBarcode(code as string, language),
    enabled: code !== null,
    retry: shouldRetryAnalyze,
    staleTime: Number.POSITIVE_INFINITY,
    refetchOnWindowFocus: false,
    refetchOnReconnect: false,
    refetchOnMount: false,
  });
}
