/** Cookie attributes for the Supabase session cookie (see ADR 0014). */
export function supabaseCookieOptions() {
  return {
    secure: process.env.NODE_ENV === "production",
    sameSite: "lax" as const,
  };
}
