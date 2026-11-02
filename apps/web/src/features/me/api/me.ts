import { getApi } from "@/lib/api/client";
import { networkError, toApiError } from "@/lib/api/errors";

export async function fetchMe() {
  const api = getApi(); // a misconfigured base URL is not a network error
  const result = await api.GET("/v1/me").catch(() => {
    throw networkError();
  });
  if (result.error !== undefined || !result.data) {
    throw toApiError(result.error, result.response.status);
  }
  return result.data;
}
