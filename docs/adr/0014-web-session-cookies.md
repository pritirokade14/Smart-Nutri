# ADR 0014: Web session in JS-readable Supabase cookies

- **Status:** Accepted
- **Date:** 2026-11-03

## Context

The web app signs in with Supabase Auth through `@supabase/ssr`. The browser calls the FastAPI backend directly with the Supabase access token as a bearer token (ADR 0003, ADR 0007). That means client JavaScript must be able to read the session, so the cookie cannot be HTTP-only. A backend-for-frontend (BFF) that keeps the token server-side would allow HTTP-only cookies, but adds a proxy hop and a second API surface.

## Decision

Keep JS-readable Supabase cookies and no BFF in v1. Mitigate XSS (the main risk) and transport risks with:

- A strict per-request nonce CSP with `strict-dynamic`, no `'unsafe-inline'` for scripts, and `frame-ancestors 'none'`.
- `Secure` cookies in production and `SameSite=Lax` (`cookieOptions` on every `createBrowserClient` / `createServerClient` call).
- `Strict-Transport-Security: max-age=63072000; includeSubDomains` in production.
- The proxy and the `(app)` layout both verify the session server-side, so the cookie is never trusted for access control by itself.

## Consequences

- An XSS bug could read the session token; the CSP is the main defence, so CSP regressions are treated as security bugs.
- No BFF to build or run in v1. Revisit if the threat model changes (for example, storing more sensitive data, or third-party scripts).
- The bearer-token model is the same on web and Android.
