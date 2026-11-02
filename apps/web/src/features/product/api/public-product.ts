import type { components } from "@smartnutri/api-client";
import { createApiClient } from "@smartnutri/api-client";
import { toApiError } from "@/lib/api/errors";

export type PublicProductOut = components["schemas"]["PublicProductOut"];

export type PublicProductResult =
  | { kind: "ok"; data: PublicProductOut }
  | { kind: "not_found" }
  | { kind: "unavailable" };

/** Server-side cache window for the public endpoint (matches its Cache-Control). */
export const PUBLIC_REVALIDATE_SECONDS = 3600;

/**
 * Fetches the generic public product. No session: the token getter returns
 * null, so no Authorization header is ever sent. Cached in Next's data cache.
 */
export async function loadPublicProduct(
  barcode: string,
): Promise<PublicProductResult> {
  const baseUrl = process.env.NEXT_PUBLIC_API_BASE_URL;
  if (!baseUrl) return { kind: "unavailable" };
  const client = createApiClient(baseUrl, async () => null);
  try {
    const { data, error, response } = await client.GET(
      "/v1/products/{barcode}/public",
      {
        params: { path: { barcode }, query: { language: "en" } },
        fetch: (req) =>
          fetch(req, { next: { revalidate: PUBLIC_REVALIDATE_SECONDS } }),
      },
    );
    if (data) return { kind: "ok", data };
    if (response.status === 404) return { kind: "not_found" };
    // 503 off_unavailable, 429, 5xx, anything else: a retry message, never server text.
    toApiError(error, response.status);
    return { kind: "unavailable" };
  } catch {
    return { kind: "unavailable" };
  }
}
