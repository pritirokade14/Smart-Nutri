import type { components } from "@smartnutri/api-client";
import { createApiClient } from "@smartnutri/api-client";

export type Methodology = components["schemas"]["Methodology"];
export type MethodologyLanguage = components["schemas"]["MethodologyLanguage"];

export type MethodologyResult =
  | { kind: "ok"; data: Methodology }
  | { kind: "unavailable" };

/** Matches the endpoint's Cache-Control (public, max-age=3600). */
export const METHODOLOGY_REVALIDATE_SECONDS = 3600;

/**
 * GET /v1/methodology on the server, for the public "How we score" page. No
 * session: the token getter returns null, so no Authorization header is sent.
 * Cached in Next's data cache for an hour. Any failure is "unavailable"
 * (the page shows a retry, never server text).
 */
export async function getMethodology(
  language: MethodologyLanguage,
): Promise<MethodologyResult> {
  const baseUrl = process.env.NEXT_PUBLIC_API_BASE_URL;
  if (!baseUrl) return { kind: "unavailable" };
  const client = createApiClient(baseUrl, async () => null);
  try {
    const { data } = await client.GET("/v1/methodology", {
      params: { query: { language } },
      fetch: (req) =>
        fetch(req, { next: { revalidate: METHODOLOGY_REVALIDATE_SECONDS } }),
    });
    return data ? { kind: "ok", data } : { kind: "unavailable" };
  } catch {
    return { kind: "unavailable" };
  }
}
