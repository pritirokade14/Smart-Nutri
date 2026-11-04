import type { components } from "@smartnutri/api-client";
import { type UseMutationResult, useMutation } from "@tanstack/react-query";
import { getApi } from "@/lib/api/client";
import { type ApiError, networkError, toApiError } from "@/lib/api/errors";

export type ReportCreate = components["schemas"]["ReportCreate"];
export type ReportOut = components["schemas"]["ReportOut"];
export type ReportReason = ReportCreate["reason"];

export const REPORT_REASONS: readonly ReportReason[] = [
  "wrong_values",
  "wrong_ingredients",
  "wrong_product",
  "other",
];

/** The API's note limit (ReportCreate.note ≤ 500). */
export const REPORT_NOTE_MAX = 500;

/**
 * POST /v1/products/{product_id}/reports (F14). 201 for a new report, 200
 * with the existing one for a duplicate open report: both are a success.
 */
export async function createReport(
  productId: string,
  body: ReportCreate,
): Promise<ReportOut> {
  const api = getApi();
  const result = await api
    .POST("/v1/products/{product_id}/reports", {
      params: { path: { product_id: productId } },
      body,
    })
    .catch(() => {
      throw networkError();
    });
  if (result.error !== undefined || !result.data) {
    throw toApiError(result.error, result.response.status);
  }
  return result.data;
}

export function useCreateReport(
  productId: string,
): UseMutationResult<ReportOut, ApiError, ReportCreate> {
  return useMutation<ReportOut, ApiError, ReportCreate>({
    mutationFn: (body) => createReport(productId, body),
    retry: false,
  });
}
