import { createApiClient } from "@smartnutri/api-client";
import { createSupabaseBrowserClient } from "@/lib/supabase/client";
import { type ConsentPurpose, consentPurposes } from "./consent-required";

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

let onConsentRequired: ((purposes: ConsentPurpose[]) => void) | undefined;

/**
 * Registers what to do when a gated route answers 403 `consent_required`
 * (ADR 0018): the app shows the consent for the missing purposes. Returns an
 * unregister function.
 */
export function setConsentRequiredHandler(
  handler: ((purposes: ConsentPurpose[]) => void) | undefined,
): () => void {
  onConsentRequired = handler;
  return () => {
    if (onConsentRequired === handler) onConsentRequired = undefined;
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
        // Targets handle a missing health_data consent in place (an inline
        // card with a grant button), never by pulling the user away.
        if (
          response.status === 403 &&
          onConsentRequired &&
          !new URL(request.url).pathname.startsWith("/v1/targets")
        ) {
          const purposes = await consentPurposes(response);
          if (purposes) onConsentRequired(purposes);
        }
        return undefined;
      },
    });
    api = client;
  }
  return api;
}
