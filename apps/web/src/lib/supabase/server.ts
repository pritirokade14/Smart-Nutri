import { createServerClient } from "@supabase/ssr";
import type { SupabaseClient } from "@supabase/supabase-js";
import { cookies } from "next/headers";
import { supabaseCookieOptions } from "./options";

export async function createSupabaseServerClient(): Promise<SupabaseClient> {
  const store = await cookies();
  return createServerClient(
    process.env.NEXT_PUBLIC_SUPABASE_URL ?? "",
    process.env.NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY ?? "",
    {
      cookieOptions: supabaseCookieOptions(),
      cookies: {
        getAll: () => store.getAll(),
        setAll(cookiesToSet) {
          try {
            for (const { name, value, options } of cookiesToSet) {
              store.set(name, value, options);
            }
          } catch {
            // Called from a Server Component: the proxy refreshes the session.
          }
        },
      },
    },
  );
}
