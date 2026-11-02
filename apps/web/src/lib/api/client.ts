import { createApiClient } from "@smartnutri/api-client";
import { createSupabaseBrowserClient } from "@/lib/supabase/client";

type ApiClient = ReturnType<typeof createApiClient>;
let api: ApiClient | undefined;

/** Browser API client; the bearer token comes from the Supabase session. */
export function getApi(): ApiClient {
  if (!api) {
    const baseUrl = process.env.NEXT_PUBLIC_API_BASE_URL;
    if (!baseUrl) throw new Error("NEXT_PUBLIC_API_BASE_URL is not set");
    const supabase = createSupabaseBrowserClient();
    api = createApiClient(
      baseUrl,
      async () =>
        (await supabase.auth.getSession()).data.session?.access_token ?? null,
    );
  }
  return api;
}
