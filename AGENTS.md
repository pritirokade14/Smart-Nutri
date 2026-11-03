# AGENTS.md

> **Start with [CONTEXT.md](CONTEXT.md).** It's the one-page snapshot: what we're building, the decisions, account IDs, current status and open items.

Shared instructions for AI coding agents working in this repository (Claude Code, Codex, Cursor and others). `CLAUDE.md` imports this file. Keep it short; put detail in `docs/`.

## What we are building

SmartNutri AI tells an Indian family whether a packaged food is right for **each member**, and tracks what they actually eat.
- **Primary users:** people managing blood sugar (diabetes, prediabetes, PCOS), family health managers (kids and elderly parents), and people losing weight.
- **Platforms:** an **Android app (Flutter)** and a **web app (Next.js)**, with **every v1 feature on both** (full parity).
- **Product scope:** `docs/PRODUCT.md`.
- **v1 design:** `docs/superpowers/specs/2026-11-02-smartnutri-v1-design.md`.
- **Architecture:** `docs/ARCHITECTURE.md`.

## Repository map

```
apps/api/                FastAPI, feature-based (app/features/<f>/), rules engine (app/scoring), Alembic (owns ALL tables + RLS)
apps/app/                Flutter ANDROID app (lib/features/<f>/{data,domain,presentation})
apps/web/                Next.js 16 web app (src/app/[locale]/(public|app), src/features/<f>/)
packages/api-contract/   openapi.json (exported from the API) + generated Dart and TypeScript clients
packages/i18n/           messages/{en,hi,mr}.json: the ONLY place user-facing strings live
packages/design-tokens/  tokens.json → generated Dart theme + CSS variables
packages/test-fixtures/  real products + expected per-member verdicts, shared by API, Android and web tests
supabase/                Supabase config, auth hooks, email templates (no tables, no RLS)
docs/                    PRODUCT, ARCHITECTURE, ADRs, research, specs and plans
.claude/                 Claude Code skills and subagents
```

Each app and package has its own `AGENTS.md` or `README.md` with stack-specific rules. Read it before editing there.

## Non-negotiable rules (health app)

1. **The rules engine decides; the LLM only explains.**
   - Verdicts (`ok` / `caution` / `unknown` / `avoid`) come only from `apps/api/app/scoring`.
   - Never let model output change a verdict, an allergen state or a score.
   - Clients (Android and web) never compute verdicts. They render what the API returns.
2. **Never invent nutrition data.**
   - No mock or fallback numbers shown as real. A missing value is `None` and leads to `unknown`.
   - Label extractions must be confirmed by the user before they are saved, on both clients.
3. **Unknown is not safe.**
   - An allergic member never gets `ok` when ingredients are missing or extraction confidence is below 0.7.
   - `unknown` is never shown in green on any client.
4. **Thresholds live in data, not code.**
   - Use `apps/api/app/scoring/data/*.yaml`. Changing one needs a test, updated `packages/test-fixtures` expectations, and a note in the PR.
   - Health thresholds stay marked `PENDING CLINICIAN REVIEW` until a clinician signs off.
5. **Secrets stay server-side.**
   - CallMissed (`cm_...`), the Supabase service-role key and other keys live only in `apps/api` env or Secret Manager.
   - The Android app gets only public config via `--dart-define`.
   - The web app exposes only `NEXT_PUBLIC_SUPABASE_URL`, `NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY`, `NEXT_PUBLIC_API_BASE_URL` and `NEXT_PUBLIC_POSTHOG_KEY`, plus the non-secret `NEXT_PUBLIC_SENTRY_DSN`, `NEXT_PUBLIC_SITE_URL` and the `NEXT_PUBLIC_FEATURE_PHONE_OTP` and `NEXT_PUBLIC_FEATURE_EMAIL_OTP` flags. Nothing secret is ever named `NEXT_PUBLIC_*`.
6. **Health data residency.**
   - LLM calls that include member health data use an India-processed model with `provider.data_residency = "in"`.
   - Strip names and IDs from prompts. No health data in analytics events.
7. **No medical claims.**
   - Copy says "information, not medical advice". Never say the app treats, manages or cures a disease.
   - Nutri-Score is labelled "calculated by SmartNutri", never "FSSAI rating".
8. **Open Food Facts data is ODbL.**
   - Keep it in `off_product_cache` (separate from `products`).
   - Credit it wherever it is shown, including public web product pages, and send a `User-Agent` on every call.
9. **Strings live only in `packages/i18n`** (en, hi, mr). The API returns reason codes, not prose. No hard-coded user-facing text in either client.
10. **Never hand-edit generated code:** the contract clients (`packages/api-contract/dart`, `packages/api-contract/ts`), the generated Flutter ARB files and the generated design tokens. Change the source and regenerate (`just contract`, `just i18n`, `just tokens`).
11. **Feature parity.** A feature is done only when the API, the Android app and the web app all ship it, and the shared fixtures in `packages/test-fixtures` pass on all three.

## Working conventions

- **Branches:** `main` is protected. Feature work goes on short-lived branches off `v1-rebuild` (until v1 ships), then `main`.
- **Build in vertical slices:** one feature end to end (API, then contract, then Android and web in parallel), not one layer at a time.
- **Contract first:** after any API schema change, run `just contract` and commit `openapi.json` and both generated clients in the same PR. CI fails on drift.
- **Commits:** Conventional Commits with a scope, e.g. `feat(scoring): …`, `fix(app): …`, `feat(web): …`, `chore(contract): …`, `docs: …`.
- **Tests first (TDD)** for anything in `scoring/`, API endpoints, providers, and client data layers. Run the tests before claiming work is done.
- **Plans:** implementation plans live in `docs/superpowers/plans/`. Follow the active plan task by task; don't skip its tests.
- **Decisions:** record significant ones as an ADR in `docs/adr/` (copy `0000-template.md`).
- **Reviews:** CODEOWNERS requires a review for `apps/api/app/scoring/`, `apps/api/app/prompts/`, verdict and allergy UI, and `packages/test-fixtures/`. Run the `nutrition-safety-reviewer` agent first.

## Commands (from the repo root)

| What | Command |
|---|---|
| First-time setup (deps, hooks) | `just setup` |
| Run everything locally (Supabase + API + web) | `just dev` |
| API only / web only / Android | `just api` · `just web` · `just android` |
| All tests | `just test` (= `test-api`, `test-app`, `test-web`) |
| Lint everything | `just lint` |
| Regenerate API contract and clients | `just contract` |
| Regenerate strings / design tokens | `just i18n` · `just tokens` |
| Apply database migrations | `just db-migrate` |
| End-to-end web tests | `just e2e` |

Per-app commands are in each app's `AGENTS.md`. Recipes that depend on later plans (for example `just dev` before Supabase is set up) may not work yet. Don't invent replacements; check the active plan.
