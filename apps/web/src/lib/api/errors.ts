import type { ErrorEnvelope } from "@smartnutri/api-client";

export type { ErrorEnvelope };

/**
 * An API failure as a stable code. The UI shows `error.<code>` from packages/i18n
 * (falling back to `error.internal_error`), never server text.
 */
export class ApiError extends Error {
  constructor(
    public readonly code: string,
    public readonly status?: number,
    public readonly details: Record<string, unknown> = {},
  ) {
    super(code);
    this.name = "ApiError";
  }
}

/** True if `body` has the API's `{ error: { code, message_key, details } }` shape. */
export function isErrorEnvelope(body: unknown): body is ErrorEnvelope {
  if (typeof body !== "object" || body === null) return false;
  const error = (body as { error?: unknown }).error;
  if (typeof error !== "object" || error === null) return false;
  const { code, message_key } = error as Record<string, unknown>;
  return typeof code === "string" && typeof message_key === "string";
}

/**
 * Turns an openapi-fetch `error` value (the parsed response body) into an ApiError.
 * Anything that is not the envelope becomes `internal_error`.
 */
export function toApiError(body: unknown, status?: number): ApiError {
  if (!isErrorEnvelope(body)) return new ApiError("internal_error", status);
  const { code, details } = body.error;
  const safeDetails =
    typeof details === "object" && details !== null ? details : {};
  return new ApiError(code, status, safeDetails);
}

/** Thrown for fetch failures (offline, DNS, CORS): no response at all. */
export function networkError(): ApiError {
  return new ApiError("network");
}
