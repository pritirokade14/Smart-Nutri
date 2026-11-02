import { getApi } from "@/lib/api/client";

export class ApiError extends Error {
  constructor(public code: string) {
    super(code);
  }
}

export async function fetchMe() {
  const api = getApi(); // a misconfigured base URL is not a network error
  const result = await api.GET("/v1/me").catch(() => {
    throw new ApiError("network");
  });
  if (result.error || !result.data) {
    // The API envelope is { error: { code } }; the generated type only models 422.
    const code = (result.error as { error?: { code?: string } } | undefined)
      ?.error?.code;
    throw new ApiError(code ?? "internal_error");
  }
  return result.data;
}
