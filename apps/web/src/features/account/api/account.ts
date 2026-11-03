import { type UseMutationResult, useMutation } from "@tanstack/react-query";
import { getApi } from "@/lib/api/client";
import { type ApiError, networkError, toApiError } from "@/lib/api/errors";

/**
 * DELETE /v1/me: erases the account (F11). 204 on success, also on a repeat
 * call; 503 `deletion_incomplete` means retry (completed steps are skipped).
 */
export async function deleteAccount(): Promise<void> {
  const api = getApi();
  const result = await api.DELETE("/v1/me").catch(() => {
    throw networkError();
  });
  if (result.error !== undefined || !result.response.ok) {
    throw toApiError(result.error, result.response.status);
  }
}

/** Retry only what the API says to retry: 503 (and a dropped connection). */
export function shouldRetryDelete(failureCount: number, error: ApiError) {
  return failureCount < 2 && (error.status === 503 || error.code === "network");
}

export function useDeleteAccount(opts: {
  retryDelayMs: number;
  onDeleted: () => Promise<void> | void;
}): UseMutationResult<void, ApiError, void> {
  return useMutation<void, ApiError, void>({
    mutationFn: deleteAccount,
    retry: shouldRetryDelete,
    retryDelay: (attempt) => opts.retryDelayMs * 2 ** attempt,
    onSuccess: opts.onDeleted,
  });
}
