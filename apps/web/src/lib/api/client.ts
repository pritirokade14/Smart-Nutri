import { createApiClient } from "@smartnutri/api-client";
import { createSupabaseBrowserClient } from "@/lib/supabase/client";

type ApiClient = ReturnType<typeof createApiClient>;
let api: ApiClient | undefined;
let onUnauthorized: (() => void | Promise<void>) | undefined;

/**
 * Registers what to do when an authenticated API call returns 401
 * (sign out and route to sign-in). Returns an unregister function.
 */
export function setUnauthorizedHandler(
  handler: (() => void | Promise<void>) | undefined,
): () => void {
  onUnauthorized = handler;
  return () => {
    if (onUnauthorized === handler) onUnauthorized = undefined;
  };
}

/** Browser API client; the bearer token comes from the Supabase session. */
export function getApi(): ApiClient {
  if (!api) {
    const baseUrl = process.env.NEXT_PUBLIC_API_BASE_URL;
    if (!baseUrl) throw new Error("NEXT_PUBLIC_API_BASE_URL is not set");
    const supabase = createSupabaseBrowserClient();
    const client = createApiClient(
      baseUrl,
      async () =>
        (await supabase.auth.getSession()).data.session?.access_token ?? null,
    );
    // 401 policy (same as Android): a rejected bearer token ends the session.
    // Only 401 triggers it; network errors and 5xx never do.
    client.use({
      async onResponse({ request, response }) {
        if (
          response.status === 401 &&
          request.headers.get("Authorization")?.startsWith("Bearer ")
        ) {
          await onUnauthorized?.();
        }
        return undefined;
      },
    });
    api = client;
  }
  return api;
}
