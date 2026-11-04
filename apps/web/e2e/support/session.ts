import type { APIRequestContext, BrowserContext } from "@playwright/test";

// A signed-in session for e2e runs against the stub (e2e/stub-api.mjs), which
// also stands in for Supabase Auth: a session cookie with an HS256 token is
// accepted by getClaims() through GET /auth/v1/user.

export const STUB = `http://127.0.0.1:${process.env.STUB_API_PORT ?? 18000}`;
export const USER_ID = "5f0c3a52-6f1e-4c9b-9d1a-2b7e8c4d1a01";
export const SESSION_COOKIE = "sb-127-auth-token";

const b64url = (v: unknown) =>
  Buffer.from(typeof v === "string" ? v : JSON.stringify(v)).toString(
    "base64url",
  );

export function sessionCookie(): string {
  const exp = Math.floor(Date.now() / 1000) + 3600;
  const user = {
    id: USER_ID,
    aud: "authenticated",
    role: "authenticated",
    email: "e2e@example.test",
    app_metadata: { provider: "email" },
    user_metadata: {},
    created_at: "2026-01-01T00:00:00Z",
  };
  const token = [
    b64url({ alg: "HS256", typ: "JWT" }),
    b64url({ sub: USER_ID, aud: "authenticated", role: "authenticated", exp }),
    b64url("e2e-signature"),
  ].join(".");
  return `base64-${b64url({
    access_token: token,
    token_type: "bearer",
    expires_in: 3600,
    expires_at: exp,
    refresh_token: "e2e-refresh",
    user,
  })}`;
}

export async function signIn(context: BrowserContext): Promise<void> {
  await context.addCookies([
    {
      name: SESSION_COOKIE,
      value: sessionCookie(),
      domain: "localhost",
      path: "/",
      sameSite: "Lax",
    },
  ]);
}

/** Resets the stub with the terms agreed (ruling G1) and signs the browser in. */
export async function signedIn(
  context: BrowserContext,
  request: APIRequestContext,
): Promise<void> {
  await request.post(`${STUB}/__reset?terms=current`);
  await signIn(context);
}

/** Adds a family member straight through the stub API (no health fields). */
export async function addMember(
  request: APIRequestContext,
  body: { name: string; relation: string; birth_year?: number },
): Promise<{ id: string }> {
  const res = await request.post(`${STUB}/v1/members`, {
    headers: { authorization: "Bearer e2e" },
    data: body,
  });
  return (await res.json()) as { id: string };
}
