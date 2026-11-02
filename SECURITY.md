# Security & Data Protection

SmartNutri processes **health data** (conditions, allergies, food logs) of Indian users, including children. We design for India's DPDP Act 2023 and DPDP Rules 2025. The core obligations apply from about May 2027, and we build for them now.

## Reporting a vulnerability

Email the maintainers privately. Do not open a public issue. Include steps to reproduce. We aim to acknowledge within 72 hours.

## Rules for contributors

- **Secrets:**
  - Never commit keys. Pre-commit runs **gitleaks** on every commit, and CI runs it again.
  - The API reads secrets from env or Secret Manager.
  - The Android app receives only public values (`SUPABASE_URL`, the publishable key, `API_BASE_URL`) via `--dart-define`.
  - The web app exposes only `NEXT_PUBLIC_SUPABASE_URL`, `NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY`, `NEXT_PUBLIC_API_BASE_URL` and `NEXT_PUBLIC_POSTHOG_KEY`. **Anything named `NEXT_PUBLIC_*` is shipped to every browser**, so never put a secret in one.
- **CallMissed key:** used only by `apps/api`. Never put it in either client, the web bundle, server components, logs or error messages.
- **Auth:**
  - Every `apps/api` endpoint except `/v1/health` and the public methodology and product-info endpoints verifies the Supabase JWT.
  - Every query is scoped to the caller's `account_id`.
  - Row-level security is enabled on all tables. The policies are written in **Alembic migrations** (`op.execute`), not in `supabase/`.
- **Web app specifics:**
  - Sessions use `@supabase/ssr` **HTTP-only, Secure, SameSite=Lax cookies**. No tokens in `localStorage`.
  - A strict **Content Security Policy** (nonce-based scripts; `connect-src` limited to the API, Supabase, Sentry and PostHog), plus `X-Frame-Options: DENY` and `Referrer-Policy: strict-origin-when-cross-origin`.
  - Public pages (`(public)` route group) show **generic product information only**. Never member names, conditions, verdicts or logs.
  - Server components call the API with the user's session; they never use the Supabase service-role key.
- **Rate limits and cost control:**
  - The API rate-limits each account. Examples: 30 label scans a day, and a daily cap on voice questions.
  - Over the limit, it returns `429` with a reason code (`rate_limited_scans`, `rate_limited_voice`).
  - Label extractions are cached by image SHA-256 and products by barcode, so the same input never triggers a second paid call.
- **Consent:**
  - Health data and AI processing need recorded, versioned consent (the `consents` table).
  - Withdrawing consent stops processing.
- **Children:** members are profiles inside an adult's account. The account holder must be 18 or older.
- **Minimise data:**
  - Strip names and IDs from LLM prompts.
  - Use India-processed models (`data_residency: "in"`) whenever health data is included.
  - Analytics (PostHog) receives event names and non-health properties only. No conditions, allergies, verdict reasons or food logs.
- **Retention:**
  - Delete label photos after 30 days.
  - Account deletion removes all member data and logs.
- **Errors:** never return exception text to clients. Log server-side, sending to Sentry with PII scrubbing, on API, Android and web.
- **Uploads:** images up to 8 MB (JPEG, PNG or WebP), audio up to 30 s. Content type is validated server-side by sniffing bytes.
