import { networkError, toApiError } from "./errors";

type Result<T> = {
  data?: T;
  error?: unknown;
  response: Response;
};

/**
 * Awaits an openapi-fetch call. A fetch failure (offline, DNS, CORS) becomes
 * a network ApiError; an error body becomes the envelope's stable code.
 */
export async function call<T>(p: Promise<Result<T>>): Promise<T> {
  const result = await p.catch(() => {
    throw networkError();
  });
  if (result.error !== undefined) {
    throw toApiError(result.error, result.response.status);
  }
  return result.data as T;
}
