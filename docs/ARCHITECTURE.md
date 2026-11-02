# Architecture

The source of truth for v1 decisions is `docs/superpowers/specs/2026-11-02-smartnutri-v1-design.md`. The reasons behind each choice are in `docs/adr/`. Feature coverage per platform is in `docs/FEATURE_PARITY.md`.

**Platforms (ADR 0008):**
- **Android:** a Flutter app.
- **Web:** a Next.js app.
- Both clients ship **every v1 feature**.
- Neither client holds business logic. All rules, scoring and AI orchestration live in `apps/api`.

## System overview

```
┌──── apps/app (Flutter, Android) ────┐        ┌────────── apps/web (Next.js 16, TypeScript) ──────────┐
│ Riverpod · go_router · dio · drift  │        │ App Router · TanStack Query · Tailwind 4 + shadcn      │
│ mobile_scanner · image_picker ·     │        │ next-intl · BarcodeDetector→@zxing/browser ·           │
│ record · supabase_flutter (session) │        │ MediaRecorder · @supabase/ssr (cookie session)         │
│ generated: smartnutri_api (Dart),   │        │ generated: @smartnutri/api-client (TS),                │
│ ARB l10n, design tokens             │        │ messages from packages/i18n, CSS tokens                │
└───────┬──────────────────┬──────────┘        └──────┬──────────────────┬─────────────────────────────┘
        │ Supabase Auth    │ HTTPS + Bearer JWT        │ Supabase Auth    │ HTTPS + Bearer JWT
        ▼                  ▼                           ▼                  ▼
┌──── Supabase (ap-south-1, Mumbai) ────┐   ┌──── apps/api (FastAPI, Cloud Run asia-south1) ──────────┐
│ Auth: Google OAuth, email OTP,        │   │ core/       config, JWT verify (JWKS), rate limits, logs │
│       phone OTP (Send-SMS hook, later)│◄──┤ features/   members · products · scans · analyze · meals │
│ Postgres + RLS (schema via Alembic)   │   │             voice · consents · reports · methodology · me│
│ Storage: private label-photo bucket   │   │ scoring/    pure rules engine (no I/O)                   │
└───────────────────────────────────────┘   │ integrations/ callmissed · openfoodfacts · storage       │
                                            │ prompts/    versioned prompt files                       │
                                            └───────┬──────────────────────┬──────────────────────────┘
                                                    ▼                      ▼
                                   CallMissed API (api.callmissed.com)   Open Food Facts v3
                                   LLM/vision · STT · TTS · WhatsApp     (cached, ODbL)
```

## Components

| Component | Responsibility | Lives in |
|---|---|---|
| Android app | UI, camera and barcode, offline log (drift), auth session, share sheet | `apps/app/lib/{core,features,shared}` |
| Web app | Public SEO pages (static/ISR) plus the logged-in app (client-rendered), camera/upload, share | `apps/web/src/{app,features,lib}` |
| API contract | `openapi.json` exported from FastAPI, plus generated Dart and TypeScript clients | `packages/api-contract/` |
| i18n | Single source of every UI string (en, hi, mr). Generates Flutter ARB; next-intl reads it directly | `packages/i18n/` |
| Design tokens | Verdict and grade colours, spacing, type. Generates Dart constants and CSS variables for Tailwind 4 `@theme` | `packages/design-tokens/` |
| Test fixtures | Real Indian products with the expected verdict for each member, shared by API, Android and web tests | `packages/test-fixtures/` |
| Supabase Auth | Identity: Google OAuth, email OTP or magic link, phone OTP (later) | `supabase/` (config, hooks, email templates) |
| Postgres | Accounts, members, consents, products, scans, meals, reports. RLS on every table | Alembic in `apps/api/alembic/` (ADR 0009) |
| Storage | Label photos in a private bucket, deleted after 30 days | `supabase/` config |
| FastAPI | Business API, JWT verification, rate limits, orchestration, all secrets | `apps/api/app/` |
| Rules engine | Deterministic verdicts, scores, allergens, diet, claims. No I/O | `apps/api/app/scoring/` |
| CallMissed integration | Vision extraction, explanations, STT, TTS, WhatsApp OTP template (later) | `apps/api/app/integrations/callmissed.py` |
| Open Food Facts integration | Barcode lookup and alternatives, with a `User-Agent` and a cache | `apps/api/app/integrations/openfoodfacts.py` |

## Contract-first pipeline (ADR 0010)

```
FastAPI routes + Pydantic schemas
   └─ just contract → packages/api-contract/openapi.json   (committed; CI fails on drift)
        ├─ swagger_parser 1.45 → packages/api-contract/dart → pub package `smartnutri_api` (used by apps/app)
        └─ openapi-typescript 7.13 → packages/api-contract/ts → `@smartnutri/api-client` with openapi-fetch 0.17 (used by apps/web)

packages/i18n/messages/{en,hi,mr}.json ─┬─ generator → apps/app ARB files (flutter gen-l10n)
                                        └─ next-intl loads directly in apps/web
packages/design-tokens/tokens.json ─ style-dictionary 5 ─┬─ Dart constants (apps/app)
                                                         └─ CSS variables → Tailwind 4 @theme (apps/web)
```

How the contract is enforced:
- The API returns reason **codes**, never prose. Both clients translate codes through the same `packages/i18n` keys, so a reason reads the same on Android and web.
- Changing an endpoint means re-running `just contract` and committing the regenerated clients. CI checks that `openapi.json` matches the running app.

## Request flows

The flows are the same on both clients. Only the device-side step differs.

**Barcode scan**
1. The barcode is decoded on the device:
   - **Android:** `mobile_scanner`.
   - **Web:** the native `BarcodeDetector` API where available (Chrome on Android, desktop Chrome), otherwise `@zxing/browser` on the camera stream. Manual barcode entry is always offered.
2. The client calls `GET /v1/products/barcode/{code}`. The API looks in `products`, then `off_product_cache` (fresh for 7 days), then the OFF v3 API.
3. The client calls `POST /v1/analyze` with `{product_id, member_ids, language}`.
4. The API runs `scoring.analyze()`, then the CallMissed LLM explains the engine's result. The prompt carries no names, and uses an India-processed model with `data_residency: in`. Explanations are cached by `(product_id, profile_hash, language)`.
5. The response is `{report, verdicts[], explanation, tips}`. Each client renders a red, amber, green or grey verdict per member using the shared tokens.
6. On a miss, the client moves to the label flow (F15). There is never a dead end.

**Label photo (including not-found)**
1. The image is uploaded with `POST /v1/scans/label` (multipart, ≤ 8 MB).
   - **Android:** `image_picker` (camera).
   - **Web:** `<input type="file" accept="image/*" capture="environment">`. On desktop, this is a file upload or the webcam.
2. The API hashes the image (sha256). If an extraction for that hash exists, it is reused. Otherwise the photo is stored privately, and a CallMissed vision model is called with a JSON schema.
3. Sanity checks run (plausible ranges; energy ≈ 4P + 4C + 9F). The API returns a **draft**.
4. The user confirms or edits the values, then the client calls `POST /v1/products`. The product is saved with `source = label` and `verification_status = pending`.
5. The flow continues with `POST /v1/analyze`.

**Voice question**
1. Push-to-talk records up to 30 s, sent as `POST /v1/voice/ask`.
   - **Android:** `record`.
   - **Web:** `MediaRecorder` (webm/opus). The API converts the audio format if CallMissed STT needs it; verify the accepted formats in Plan 2.
2. The API runs CallMissed STT (`saaras:v4`), then the LLM. The LLM is given the engine report as context and is told not to change the verdict.
3. CallMissed TTS (`bulbul`) speaks the answer.
4. The response is `{question, answer, audio_url}`.

**Public product page (web only, SEO)**
- `/[locale]/p/[barcode]` is statically generated or ISR from `GET /v1/products/{barcode}/public`.
- It shows only generic facts:
  - the Nutri-Score (labelled "calculated by SmartNutri")
  - "high in" warnings
  - claim checks
  - ingredients
  - Open Food Facts attribution
- It **never shows a personal verdict**. A "Check for my family" button sends the visitor to log in.

## Login (both clients)

| Method | Android (`supabase_flutter` 2.18) | Web (`@supabase/ssr` 0.12 + supabase-js 2.118) |
|---|---|---|
| Google | `signInWithOAuth(google)` with a deep-link redirect, or native Google Sign-In ID token → `signInWithIdToken` | OAuth redirect → `/auth/callback` route exchanges the code for a cookie session |
| Email OTP / magic link | `signInWithOtp(email)` → verify code | Same, with the magic-link callback route |
| Phone OTP (built, off) | Screen behind a feature flag | Same screen behind the same flag |

How the session reaches the API:
- Both clients send the Supabase access token as `Authorization: Bearer` to the API. The API verifies it with Supabase JWKS.
- On the web, server components read the session from cookies and call the API server-side only for public data. Logged-in data is fetched client-side via TanStack Query.

Phone OTP delivery (when switched on):
1. The Supabase Send-SMS hook calls the API's `/internal/auth/send-otp`.
2. The API calls the CallMissed WhatsApp authentication template.
3. The feature is enabled after Meta approves the template.

## Data model (summary)

The tables are:
- `accounts`
- `members`, with `custom_alerts`
- `consents`
- `products`, with `verification_status`
- `off_product_cache`
- `scans`, with `image_sha256`
- `meal_logs`
- `product_reports`

Full columns are in spec §4.

Rules:
- **Alembic owns the whole schema, including RLS policies** (via `op.execute`). `supabase/` never changes tables (ADR 0009).
- OFF data stays in `off_product_cache` for ODbL separation.

## Rate limiting and caching

| Control | Default (configurable) |
|---|---|
| Label extractions | 30 per account per day |
| Voice questions | 20 per account per day, audio ≤ 30 s |
| `/analyze` | 120 per account per hour |
| Public endpoints (`/methodology`, `/products/{barcode}/public`) | Per-IP limits plus CDN/ISR caching |
| Extraction cache | Keyed by image sha256 |
| Product cache | Keyed by barcode (own table, then OFF cache with a 7-day TTL) |
| Explanation cache | Keyed by `(product_id, profile_hash, language)` |

Limits are enforced in `apps/api/app/core` and return `429` with a `retry_after` field. Both clients show a localised message.

## Security and privacy

See [SECURITY.md](../SECURITY.md).

- Secrets stay server-side only. The web app has no CallMissed or service-role keys, and its server components hold only the public Supabase publishable key.
- Every query is scoped by the JWT.
- Consent records are versioned.
- Prompts are stripped of names.
- Health-data calls use India-processed models.
- Photos are deleted after 30 days.
- Errors are generic, and account deletion removes everything.

## Hosting

| Piece | Where | Notes |
|---|---|---|
| API | Cloud Run `asia-south1` (Mumbai) | Container; scale to zero in dev, `min-instances=1` in prod to avoid cold starts |
| Web app | Cloud Run `asia-south1` | Next.js `output: "standalone"` Docker image; public pages cached via ISR (ADR 0012) |
| Android app | Google Play (internal testing → production) | Built with Flutter |
| Database, auth, storage | Supabase Mumbai | Pro plan before real users (backups, no pausing) |
| Secrets | Google Secret Manager | Mounted into the Cloud Run API service only |

Hosting choices not taken:
- **Firebase Hosting:** no longer needed, because the web app is server-rendered.
- **Vercel:** its Hobby plan forbids commercial use.

## Environments

| Env | Android | Web | API | Supabase | CallMissed |
|---|---|---|---|---|---|
| local | `flutter run --dart-define-from-file=env/dev.json` | `pnpm --filter web dev` | `uv run fastapi dev` | Supabase CLI local stack or the dev project | dev key, low limits |
| dev | Internal-testing build | Cloud Run `smartnutri-web-dev` | Cloud Run `smartnutri-api-dev` | `smartnutri-dev` (Mumbai) | dev key |
| prod | Google Play | Cloud Run `smartnutri-web` + custom domain | Cloud Run `smartnutri-api` | `smartnutri-prod` (Mumbai) | prod key, Starter plan or higher |

- `just dev` starts the local Supabase, API and web together. Android runs separately with `just android`.
- Public client config: `apps/app/env/*.json` and `apps/web/.env.local`. Both are git-ignored, apart from the example files.

## CallMissed usage and model selection

- **Endpoints:**
  - Inference: `https://api.callmissed.com/v1`, OpenAI-compatible. Covers `/chat/completions`, `/audio/transcriptions` and `/audio/speech`.
  - Resources: `https://api.callmissed.com/api/v1`. Covers WhatsApp and email.
- **Client:** the `openai` Python SDK with `base_url` overridden, wrapped behind `LLMProvider` and `SpeechProvider` interfaces.
- **Policy:**
  1. Model IDs come from config, never code.
  2. Pick defaults with the label eval set.
  3. Health-data prompts use `processing == "india"` models with `provider.data_residency = "in"`.
  4. Use `response_format: json_schema` for structured output.
  5. Handle `402` (alert ops, show a friendly message) and `429` (back off).
  6. Log each call with model, prompt version, latency, tokens and cost. Never log health data.
- **Plan limits:** the Free plan is for development only. Launch needs Starter or higher. The caches above cut calls.

## Delivery: vertical slices (ADR 0011)

Each milestone ships **API + Android + web** together, and passes the shared fixtures on all three:

| Milestone | Target day | Slice |
|---|---|---|
| M1 | 4–5 | Barcode → OFF → rules engine → verdict, on Android and web |
| M2 | 6–7 | Label photo → draft → confirm → verdict; not-found flow |
| M3 | 8–9 | Family members, per-member verdicts, claim checker, custom alerts, explanations |
| M4 | 10–11 | Scan-to-log, daily and weekly summaries, share, alternatives, compare |
| M5 | 12–13 | Voice Q&A, "How we score", report a problem, public product pages |
| M6 | 14–15 | Hardening, consent and deletion, rate limits, Sentry and PostHog, release |

## Observability and quality

- **Sentry:** `sentry_flutter` on Android, `@sentry/nextjs` 11.10 on web, and `sentry-sdk` on the API, all with PII scrubbing.
- **Logs:** structured JSON, plus an LLM call log.
- **PostHog:** `posthog-js` 1.444 on web, plus the Flutter SDK. No health data in events. Events cover scan started and completed, verdict shown, "I ate this" and report filed.
- **CI (GitHub Actions)** on every push, with path filters:
  - `api.yml`: ruff, pytest, contract drift.
  - `app.yml`: `flutter analyze`, `flutter test`.
  - `web.yml`: Biome, Vitest, Playwright smoke tests, `next build`.
  - `security.yml`: gitleaks.
- **Pre-commit:** gitleaks, ruff, Biome, `dart format`.
- **Mandatory safety review:** CODEOWNERS plus branch protection require it for `apps/api/app/scoring/**`, `apps/api/app/prompts/**`, and the verdict and allergy UI in both clients.

## Monorepo map

```
apps/api/                FastAPI (feature-based) + scoring engine + alembic/
apps/app/                Flutter Android app (android/, ios/ kept for later)
apps/web/                Next.js 16 web app
packages/api-contract/   openapi.json + dart/ (smartnutri_api) + ts/ (@smartnutri/api-client)
packages/i18n/           messages/{en,hi,mr}.json
packages/design-tokens/  tokens.json → Dart + CSS
packages/test-fixtures/  products/*.json + expected verdicts
supabase/                config.toml, auth hooks, email templates (no schema)
docs/                    PRODUCT, ARCHITECTURE, FEATURE_PARITY, adr/, research/, superpowers/
.claude/  .github/       agent skills/subagents; CI workflows, CODEOWNERS, PR template
package.json  pnpm-workspace.yaml  justfile  .pre-commit-config.yaml
```
