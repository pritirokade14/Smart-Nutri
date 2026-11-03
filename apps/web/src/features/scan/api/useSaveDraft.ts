import type { components } from "@smartnutri/api-client";
import { type UseMutationResult, useMutation } from "@tanstack/react-query";
import { getApi } from "@/lib/api/client";
import { type ApiError, networkError, toApiError } from "@/lib/api/errors";
import type { ProductCreate } from "../lib/draftSchema";

export type ProductOut = components["schemas"]["ProductOut"];

/** POST /v1/products (a confirmed scan draft or a manual entry). */
export async function saveDraft(body: ProductCreate): Promise<ProductOut> {
  const api = getApi();
  const result = await api.POST("/v1/products", { body }).catch(() => {
    throw networkError();
  });
  if (result.error !== undefined || !result.data) {
    throw toApiError(result.error, result.response.status);
  }
  return result.data;
}

export function useSaveDraft(): UseMutationResult<
  ProductOut,
  ApiError,
  ProductCreate
> {
  return useMutation<ProductOut, ApiError, ProductCreate>({
    mutationFn: saveDraft,
    retry: false,
  });
}
