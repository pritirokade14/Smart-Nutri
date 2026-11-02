import { createServerClient } from "@supabase/ssr";
import type { NextRequest, NextResponse } from "next/server";

/**
 * Refreshes the Supabase session cookies onto `res` and reports whether the
 * request carries a valid session. Never throws: any failure means signed out.
 */
export async function updateSession(
  req: NextRequest,
  res: NextResponse,
): Promise<{ res: NextResponse; signedIn: boolean }> {
  try {
    const supabase = createServerClient(
      process.env.NEXT_PUBLIC_SUPABASE_URL ?? "",
      process.env.NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY ?? "",
      {
        cookies: {
          getAll: () => req.cookies.getAll(),
          setAll(cookiesToSet, headers) {
            for (const { name, value, options } of cookiesToSet) {
              res.cookies.set(name, value, options);
            }
            for (const [k, v] of Object.entries(headers ?? {})) {
              res.headers.set(k, v);
            }
          },
        },
      },
    );
    const { data } = await supabase.auth.getClaims();
    return { res, signedIn: Boolean(data?.claims) };
  } catch {
    return { res, signedIn: false };
  }
}
