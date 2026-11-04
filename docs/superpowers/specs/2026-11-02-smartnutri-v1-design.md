# SmartNutri AI v1: Design Spec

**Date:** 2026-11-02 · **Branch:** `v1-rebuild` · **Target:** usable v1 in 10–15 days

## 1. Product

SmartNutri AI tells an Indian family whether a packaged food is right for each of them, and tracks what they actually eat.

**Primary users (v1)**
1. **Blood-sugar group:** diabetes, prediabetes, PCOS.
2. **Family health manager:** parents shopping for children, and adults looking after elderly parents.
3. **Weight loss**, including GLP-1 users.

**Platforms (ADR 0008):**
- An **Android app built with Flutter**.
- A **web app built with Next.js 16**.
- **Every v1 feature ships on both** (full parity, see `docs/FEATURE_PARITY.md`). Nothing is removed from either platform.
- The web app also serves public, Google-indexable pages: the landing page, "How we score" and generic product pages.

## 2. v1 Scope

| # | Feature | Notes |
|---|---|---|
| F1 | Accounts | Google OAuth and email OTP / magic link via Supabase Auth. Phone OTP code is written but switched off: delivery through a WhatsApp OTP template sent by CallMissed via the Supabase Send-SMS hook, enabled once the template is approved. |
| F2 | Family members | One account holds many members. Each member has: name, relation, birth year, sex, height, weight, diet, allergens, conditions and goal. |
| F3 | Scan by barcode | Android: on-device `mobile_scanner`. Web: `BarcodeDetector`, falling back to `@zxing/browser`, plus manual entry. Lookup order: our `products` table, then the Open Food Facts v3 API. |
| F4 | Scan by label photo | A CallMissed vision LLM with a JSON schema reads nutrition per 100 g, per-serving values, ingredients, the "contains" and "may contain" lines, front-of-pack claims and the veg mark. **The user confirms or edits the values before they are saved.** No invented values are allowed. |
| F5 | Rules engine | Deterministic. Covers: Nutri-Score 2023, "high in" warnings, the allergen synonym engine, diet checks (veg, eggetarian, vegan, Jain), hidden sugars and sodium additives, the claim checker, and condition and goal rules. **The LLM never decides a verdict.** |
| F6 | Verdict per member | Each member gets one of `ok`, `caution`, `avoid` or `unknown`, with coded reasons. |
| F7 | AI explanation | CallMissed LLM explains the engine's result in the user's language (en/hi/mr), with 3 tips. Uses an India-processed model when health data is in the prompt. |
| F8 | Scan-to-log | "I ate this" plus a portion. Shows real daily and weekly totals per member (sugar, salt, protein, kcal). |
| F9 | Alternatives, search, compare | Uses Open Food Facts v3 and our products table. |
| F10 | Voice Q&A | Push-to-talk (Android `record`; web `MediaRecorder`). Speech goes to CallMissed STT (`saaras:v4`), then the LLM, then CallMissed TTS (`bulbul`), in the member's language. |
| F11 | Trust and compliance | Medical disclaimer, consent records, account deletion, Open Food Facts attribution, and "calculated by SmartNutri" labels. |
| F12 | "How we score" page | A public methodology page, in-app and on the web. It covers each rule, its thresholds and its source (ICMR-NIN 2024, FSSAI Claims Regs 2018, WHO, UK FSA, Nutri-Score 2023), plus the "pending clinician review" note. It is generated from `thresholds.yaml` so it never drifts from the code. *(Idea from Yuka and TruthIn.)* |
| F13 | Result screen at a glance | One red/amber/green colour per member (`avoid` is red, `caution` amber, `ok` green, `unknown` grey with "label unclear"). The A–E grade sits alongside, plus a one-line "why for this person" built from the top reason code (e.g. "Sugar-free claim is false: contains maltodextrin"). *(Ideas from Fig, TruthIn and Xume.)* |
| F14 | Report a problem | A button on every product and result screen with reasons `wrong_values`, `wrong_ingredients`, `wrong_product`, `other` plus an optional note. Reports are stored for review. *(Idea from TruthIn.)* |
| F15 | Product not found | If a barcode misses both our table and Open Food Facts, the app goes straight to F4 (label photo). It gives a result immediately, and saves the product with `verification_status = 'pending'` for review. There is never a dead end. *(Ideas from OFF and Yuka.)* |
| F16 | Custom ingredient alerts | Each member can switch on alerts for `palm_oil`, `maida` (refined wheat flour), `added_sugar`, `artificial_sweetener` and `msg`. A matching product gets a `custom_alert` reason with severity `caution`. *(Idea from Yuka Premium.)* |
| F17 | Share | Share a result card, or the weekly family summary. Android uses the OS share sheet. Web uses the Web Share API, with a copy-link and `wa.me` fallback on desktop. WhatsApp is the expected target. No WhatsApp API is needed in v1. |

**Out of v1 (v2 backlog):**
- Dietitian web dashboard
- Real-time voice agent through the CallMissed voice WebSocket
- WhatsApp bot (send a label photo, get a verdict)
- WhatsApp alerts to caregivers
- Meal photos of home food (needs an INDB/IFCT licence)
- Kidney and pregnancy modes (need a regulatory opinion first)
- Health Connect
- Quick-commerce links
- Contributing data back to Open Food Facts
- Paid family plan
- Competitor-inspired ideas that don't fit the 15-day window:
  - Rewards and streaks for contributing missing products (TruthIn)
  - Alternatives ranked by score and price (Xume)
  - Cart-level insights across several scanned items (TruthIn)
  - An offline bundle of the top Indian products (OpenLabel)
  - Micro-lessons attached to verdicts, e.g. "what is maltodextrin" (Noom, Fooducate)
  - CGM and diabetes-programme partners (Sugar.fit, Fitterfly)
  - A WhatsApp logging/scan bot (Nutrimate)

## 3. Architecture

The full design is in `docs/ARCHITECTURE.md`.

```
apps/app  Flutter (Android): Riverpod · go_router · dio · drift · mobile_scanner · supabase_flutter
apps/web  Next.js 16 (App Router, TS): TanStack Query · Tailwind 4 + shadcn · next-intl · @supabase/ssr
   │  both use generated clients from packages/api-contract, strings from packages/i18n,
   │  colours from packages/design-tokens, and test against packages/test-fixtures
   └─ HTTPS + Supabase JWT ─► apps/api FastAPI (Cloud Run, asia-south1), feature-based
        ├─ core/: config, JWT verify (JWKS), per-account rate limits, logging
        ├─ features/: members · products · scans · analyze · meals · voice · consents · reports · methodology · me
        ├─ db/ + alembic/: Postgres on Supabase ap-south-1. Alembic owns schema and RLS (ADR 0009)
        ├─ Storage: Supabase private bucket; label photos deleted after 30 days
        ├─ scoring/: pure-Python rules engine (no I/O)
        ├─ integrations/callmissed.py: OpenAI-compatible client
        │     · vision extraction  (/v1/chat/completions, json_schema)
        │     · explanation/coach  (/v1/chat/completions, India-processed model)
        │     · STT /v1/audio/transcriptions · TTS /v1/audio/speech
        ├─ integrations/openfoodfacts.py (v3, User-Agent, cache table)
        └─ Sentry + structured logs (each LLM call logged with prompt version)
apps/web is also hosted on Cloud Run asia-south1 (Next standalone); Android ships via Google Play.
```

**CallMissed rules:**
- The API key (`cm_...`) lives only on the backend.
- Model IDs come from config, never hard-coded. Defaults are chosen after the evaluation set runs (Plan 2).
- Calls that include a member's health data use `provider: {"data_residency": "in"}` and a model whose `processing` is `india`.
- Every provider call sits behind an interface (`LLMProvider`, `SpeechProvider`) so the vendor can be swapped.

**Initial model candidates (to be confirmed against the evaluation set):**
- Extraction: `gpt-6-luna` (vision, india_preferred), `glm-5.3-flash` (vision, india), `gemma-4-31b` (vision, india), `gemini-3.5-flash-lite` (vision, outside India).
- Explanation: `sarvam-105b` (india).
- STT: `saaras:v4` (india, 30 s per request).
- TTS: `bulbul:v3` or `bulbul:v4-flash` (india).

## 4. Data Model (Postgres)

| Table | Key columns |
|---|---|
| `accounts` | `id uuid PK = auth.users.id`, `display_name`, `language` (`en`/`hi`/`mr`), `created_at`, `deleted_at` |
| `members` | `id uuid`, `account_id → accounts`, `name`, `relation` (`self`/`child`/`parent`/`spouse`/`other`), `birth_year`, `sex`, `height_cm`, `weight_kg`, `diet` (`veg`/`eggetarian`/`vegan`/`jain`/`non_veg`), `allergens text[]`, `conditions text[]`, `custom_alerts text[]`, `goal`, `is_primary` |
| `consents` | `id`, `account_id`, `purpose` (`terms`/`health_data`/`ai_processing`), `version`, `granted_at`, `withdrawn_at` |
| `products` | `id uuid`, `barcode` (unique, nullable), `name`, `brand`, `category` (`general`/`beverage`/`water`/`cheese`/`fat`), `per_100g jsonb`, `serving_size_g`, `ingredients_text`, `allergen_statement`, `may_contain_statement`, `claims text[]`, `veg_mark`, `source` (`label`/`user`), `extraction_confidence`, `verification_status` (`pending`/`verified`/`rejected`), `created_by`, `created_at` |
| `product_reports` | `id`, `product_id → products`, `account_id`, `reason` (`wrong_values`/`wrong_ingredients`/`wrong_product`/`other`), `note`, `status` (`open`/`resolved`), `created_at` |
| `off_product_cache` | `barcode PK`, `payload jsonb`, `fetched_at`. Kept separate from `products` for ODbL. |
| `scans` | `id`, `account_id`, `product_id`, `image_path`, `image_sha256` (extraction cache key), `analysis jsonb`, `created_at` |
| `meal_logs` | `id`, `member_id`, `product_id`, `grams`, `eaten_at`, `nutrients jsonb` (a snapshot) |

Row-level security applies on every table, keyed by `account_id`. The API also checks ownership on every request. **Alembic owns all schema and RLS changes** (ADR 0009).

## 5. API (`/v1`, Supabase JWT required except `/v1/health`, `/v1/methodology` and `/v1/products/{barcode}/public`)

- `GET /health`
- `GET` / `PATCH` / `DELETE /me`
- `GET` / `POST /members`, and `PATCH` / `DELETE /members/{id}`
- `POST /consents`
- `GET /products/barcode/{code}`, then `POST /scans/label` (multipart image, returns an extraction draft), then `POST /products` (the user-confirmed draft)
- `POST /analyze` with body `{product_id, member_ids?, language}`, returning `{report, verdicts[], explanation, tips}`
- `GET /products/{id}/alternatives`
- `POST /products/{id}/reports` with body `{reason, note?}`
- `GET /methodology?language=` (public, no JWT) returns the rules, thresholds and sources behind F12
- `GET /products/{barcode}/public?language=` (public, no JWT, cached) returns **generic** product facts for the web SEO pages:
  - Nutri-Score, "high in" warnings, claim checks and ingredients
  - OFF attribution
  - **never** member data or a personal verdict
- **Rate limits** (configurable): 30 label extractions per account per day, 20 voice questions per account per day, and 120 `/analyze` calls per account per hour. Public endpoints are limited per IP. Over the limit, the API returns `429` with `{code: "rate_limited_scans" | "rate_limited_voice" | "rate_limited", retry_after}`.
- **Contract:** FastAPI exports `openapi.json` to `packages/api-contract/`. Both clients are generated from it, and CI fails on drift (ADR 0010).
- `POST /meals`, `GET /meals?member_id&from&to`, `GET /meals/summary?member_id&period=day|week`
- `POST /voice/ask` (multipart audio plus `product_id`, `member_id`, `language`), returning `{question, answer, audio_url}` (superseded 2026-11-04 by ADR 0020: the mp3 comes inline as `audio_base64` and is never stored)

## 6. Rules Engine Requirements

- **Input:** nutrition per 100 g. Salt is derived from sodium as `salt_g = sodium_mg × 2.5 / 1000`, and energy as `kJ = kcal × 4.184`.
- **Nutri-Score 2023:** the general, beverage and water categories. Cheese and fat categories use the general table and set `approximated=true`.
  - If energy, sugars, saturated fat or salt is missing, return `grade=None` with reason `insufficient_data`.
  - Missing fibre, protein or fruit/vegetable/legume % counts as 0 and sets `partial=true`.
  - Always labelled "calculated by SmartNutri".
- **"High in" warnings:**
  - Configurable thresholds per 100 g.
  - Default to the UK FSA "high" values until FSSAI notifies its own:
    - Food: sugar > 22.5, fat > 17.5, saturated fat > 5, salt > 1.5.
    - Drinks: half those values.
- **Allergens:**
  - Synonym and derivative map, including INS codes and Hindi/regional names.
  - Each allergen gets one of three states: `contains`, `may_contain`, `unknown`.
  - If ingredients are missing or extraction confidence is below 0.7, every allergen of an allergic member is `unknown`.
  - **Never `ok` for an allergic member when ingredients are unknown.**
- **Diet:** checked against ingredients for veg, eggetarian, vegan and Jain. A product marked veg that has a non-veg ingredient raises a `veg_mark_mismatch` flag.
- **Hidden sugars and sodium additives:** detected from ingredient lists.
- **Claim checker:** compares `sugar free`, `low sugar`, `no added sugar`, `low fat`, `low sodium`, `high protein` and `source of protein` against FSSAI (Advertising & Claims) 2018 thresholds, kept in config. Each claim is `supported`, `contradicted` or `unverifiable`.
- **Conditions and goals:**
  - Covered: `diabetes`, `prediabetes`, `pcos`, `hypertension`, `weight_loss`, plus a child rule (age < 13) and an infant rule (age < 2).
  - Thresholds live in `thresholds.yaml`, marked *pending clinician review*.
- **Combining results:** the most severe status wins, ranked `avoid` > `unknown` > `caution` > `ok`.
- **Output:** reasons carry `code`, `severity` and `params`, never prose. Text is localised later, by the UI or the LLM.

## 7. Non-Functional Requirements

- Python 3.13, FastAPI (current), Pydantic 2, SQLAlchemy 2, Alembic, `uv`.
- **Android:** Flutter stable (3.44.2 locally; upgrade to the latest stable before app work), Dart ≥ 3.9, `supabase_flutter` 2.18, generated client via swagger_parser 1.45.
- **Web:**
  - Node 24 (≥ 20.9), pnpm 12.
  - Next.js 16.4, React 19.3, Tailwind 4.3 + shadcn, next-intl 4.14, TanStack Query 5, zod 4, `@supabase/ssr` 0.12.
  - Biome 2.6 (lint and format), Vitest 5 + Testing Library, Playwright 1.64.
  - TypeScript: the version `create-next-app@16` scaffolds. npm latest is 7.0.2; verify compatibility before bumping.
- **Shared:** openapi-typescript 7.13 + openapi-fetch 0.17, style-dictionary 5.7, a pnpm workspace, a `justfile`, pre-commit (gitleaks, ruff, Biome, `dart format`).
- **Secrets:**
  - Backend secrets come only from env or Secret Manager.
  - Flutter uses `--dart-define`.
  - Web exposes only `NEXT_PUBLIC_*` public values.
  - Neither client holds secrets.
- **CORS:** an allow-list (the web app's origins).
- **Hosting:** API and web on Cloud Run `asia-south1`, with `min-instances=1` in prod (ADR 0012).
- **Observability:** Sentry (API, Flutter, Next.js) and PostHog (no health data).
- **CI:** GitHub Actions on every push, with path filters. CODEOWNERS plus branch protection make the safety review mandatory for scoring, prompts and verdict UI on both clients.
- Upload limits: images up to 8 MB (JPEG, PNG or WebP), audio up to 30 s.
- Error responses never expose exception text.
- **Tests:**
  - unit tests for the engine
  - API tests with a test database
  - an evaluation set of 50+ real Indian label photos
  - Flutter widget tests
  - web component tests (Vitest) and Playwright smoke tests
  - **shared fixtures** (`packages/test-fixtures`) run on all three

## 8. Implementation Plans (in order)

Delivery uses **vertical slices** (ADR 0011). After the two foundation plans, each milestone ships **API + Android + web** together. A milestone is done only when the shared fixtures pass on all three (`docs/FEATURE_PARITY.md`).

1. **Plan 1: Rules engine.** `apps/api/app/scoring`: pure Python, fully unit-tested. Covers the verdicts behind F5, F6 and F13. *(Written.)*
   - **Follow-up (Plan 1b, small):** custom ingredient alerts (F16).
     - Add `custom_alerts: tuple[str, ...]` to `Member`.
     - Add a `custom_alerts` term map to `data/ingredients.yaml`: `palm_oil`, `maida`, `artificial_sweetener`, `msg`. `added_sugar` reuses `added_sugars` ∪ `hidden_sugars`.
     - Add `custom_alert_reasons()`, merged in `evaluate_member`.
     - Add a `methodology()` export for F12.
2. **Plan 2: Foundation.**
   - Root tooling: the pnpm workspace, `justfile`, pre-commit, and CI workflows (`api`, `app`, `web`, `security`). CODEOWNERS and the PR template.
   - The API skeleton (feature-based) with config, Supabase JWT auth, rate-limit middleware, Alembic baseline including RLS, `/health`, and the `openapi.json` export.
   - The `packages/api-contract` generators (Dart and TS), the `packages/i18n` pipeline (JSON → ARB), the `packages/design-tokens` pipeline (Dart + CSS), and `packages/test-fixtures` seeded from the Plan 1 golden products.
   - The **Flutter Android shell:** remove the desktop folders and set Android permissions (INTERNET, CAMERA, RECORD_AUDIO). Add Riverpod, go_router, the generated client, l10n, tokens, and Supabase login (Google and email OTP; phone OTP behind a flag).
   - The **Next.js shell:** App Router with `[locale]`, `(public)` and `(app)` route groups. Add `@supabase/ssr` login, the generated client, next-intl, tokens via Tailwind `@theme`, security headers and CSP.
3. **M1 (day 4–5):** barcode → products/OFF → `analyze` → verdict, on Android and web.
4. **M2 (day 6–7):** label photo → CallMissed extraction (eval harness, image-hash cache) → confirm → verdict; the not-found flow (F15).
5. **M3 (day 8–9):** family members, per-member verdicts (F6, F13), claim checker, custom alerts (Plan 1b), explanations (F7).
6. **M4 (day 10–11):** scan-to-log and daily/weekly summaries (F8; Android offline log), alternatives, search, compare (F9), share (F17).
7. **M5 (day 12–13):** voice Q&A (F10), "How we score" (F12; public page on web), report a problem (F14), public product pages and SEO.
8. **M6 (day 14–15):** hardening and launch:
   - consent, disclaimers and account deletion (F11)
   - rate-limit tuning, Sentry and PostHog
   - Supabase production setup and the Send-SMS hook for WhatsApp OTP (enabled when the template is approved)
   - Cloud Run prod deploys for API and web
   - a Play Store internal-testing release

**Risk note (honest):** full feature parity on two clients in 15 days is **tight**. The UI effort is about 1.5–1.8× that of a single client.

Mitigations:
- **Contract-first generated clients:** no hand-written API code in either client.
- **One builder per client, working in parallel** (`flutter-builder`, `web-builder`) after `api-builder` freezes each slice's contract.
- **Shared i18n, tokens and fixtures:** the clients cannot diverge.
- **Vertical slices:** both platforms integrate from day 4–5.

If a slice slips, the **date** moves, not the scope or a platform. Flag it at the end of each milestone.
