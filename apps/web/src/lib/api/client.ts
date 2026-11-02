import { createApiClient } from "@smartnutri/api-client";
import { createSupabaseBrowserClient } from "@/lib/supabase/client";

type ApiClient = ReturnType<typeof createApiClient>;
let api: ApiClient | undefined;

/** Browser API client; the bearer token comes from the Supabase session. */
export function getApi(): ApiClient {
  if (!api) {
    const supabase = createSupabaseBrowserClient();
    api = createApiClient(
      process.env.NEXT_PUBLIC_API_BASE_URL ?? "",
      async () =>
        (await supabase.auth.getSession()).data.session?.access_token ?? null,
    );
  }
  return api;
}
