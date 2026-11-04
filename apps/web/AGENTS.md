# apps/web: agent guide

This is the **web app** for SmartNutri AI, built with Next.js. It ships **every v1 feature** that the Android app (`apps/app`) ships (full parity), plus **public pages that Google can index**. Root rules in `../../AGENTS.md` apply first.

> **Current state:** all v1 features built and merged to `main` (1,298 unit and 47 e2e tests). `robots.txt` and the sitemap exist; `og:image` share cards are not built (TODO). The long manual-entry form on mobile is a known minor UX issue.
>
> **CI gotcha:** `NEXT_PUBLIC_*` is inlined at build time, so the web CI build must set `NEXT_PUBLIC_SUPABASE_URL` to the e2e fake auth stub (`http://127.0.0.1:54321`).
>
> Design system and shell: `src/components/ui` holds hand-built, dependency-free primitives (Button, Card, SectionHeader, EmptyState, ErrorState, Skeleton/LoadingState, DisclaimerFooter, VerdictBadge, ReasonList, NutriScoreChip, icons); `src/components/shell` holds the header, language switcher, tab bar/sidebar and footer. shadcn is not initialised. Verdict tone comes only from `data-verdict` CSS in `globals.css` (default: unknown grey). Fonts: Noto Sans + Noto Sans Devanagari via next/font (self-hosted). Dark mode follows `prefers-color-scheme` via the `color.dark.*` tokens.

## Stack (versions checked 2026-11-02)

- Node 24 · pnpm 12 (workspace member) · **Next.js 16.4** (App Router) · React 19.3
- TypeScript, strict. Pin the version `create-next-app` 16.4 installs. npm `latest` is 7.0.2; confirm `next build` type-checks before upgrading.
- Tailwind CSS 4.3 (theme from **generated** CSS variables in `packages/design-tokens`) + shadcn 4.23 components
- next-intl 4.14 (messages read directly from `packages/i18n/messages/{en,hi,mr}.json`)
- `@supabase/ssr` 0.12 + `@supabase/supabase-js` 2.118: cookie sessions, Google OAuth, email OTP
- **`@smartnutri/api-client`**: the generated client in `packages/api-contract/ts` (openapi-typescript 7.13 + openapi-fetch 0.17). Use it for every API call.
- `@tanstack/react-query` 5.105 (client-side server state), zod 4.6 + react-hook-form 7.91 (forms)
- Barcode: native `BarcodeDetector`, falling back to `@zxing/browser` 0.2.1. Voice: `MediaRecorder`.
- Tests: Vitest 5.1 + `@testing-library/react` 16.3 · Playwright 1.64 (e2e)
- Biome 2.6 (lint and format) · `@sentry/nextjs` 11.10 · `posthog-js` 1.444 (no health data in events)
- Hosting: Cloud Run asia-south1 (Next.js `output: "standalone"` container), next to the API.

## Target layout

```
apps/web/
  package.json  next.config.ts  biome.json  vitest.config.ts  playwright.config.ts  Dockerfile
  src/
    app/
      [locale]/                       # en | hi | mr (next-intl)
        (public)/                     # NO login, indexable, static or ISR
          page.tsx                    # landing
          how-we-score/page.tsx       # methodology, from GET /v1/methodology
          p/[barcode]/page.tsx        # public product page: generic info only, OFF attribution
        (app)/                        # login required (middleware redirect)
          scan/  members/  history/  meals/  product/[id]/  settings/ ...
      api/                            # only thin route handlers if unavoidable (e.g. auth callback)
    features/<feature>/
      api/          # hooks/functions wrapping @smartnutri/api-client (no raw fetch)
      components/   # feature UI
      hooks/
    lib/
      supabase/     # server.ts, client.ts, middleware.ts (@supabase/ssr)
      api/          # configured openapi-fetch client (base URL + session token)
      i18n/         # next-intl config, request.ts
    components/ui/  # shadcn components
  tests/            # Vitest unit and component tests (use packages/test-fixtures)
  e2e/              # Playwright: login, scan by photo, verdict, log
```

## Rules for this app

- **Server Components by default.** Add `"use client"` only for interactivity (camera, recorder, forms, React Query). Keep client bundles small.
- **Route groups:**
  - `(public)` pages must never show member names, conditions, verdicts or logs. Generic product info and the Nutri-Score are fine.
  - `(app)` pages require a session; middleware redirects to sign-in.
- **Route segments are opaque.** Dynamic segments may hold only UUIDs or barcodes, never names, conditions or slugs: URL paths are sent to analytics.
- **Never compute a verdict in the browser or on the web server.** Render exactly what the API returns.
- **Generated client only.**
  - All API calls go through `@smartnutri/api-client`. No hand-written `fetch` to the API, and no hand-written response types.
  - If the client looks out of date, run `just contract`. Never edit the generated files.
- **Strings:**
  - All user-facing text comes from `packages/i18n` via next-intl. No string literals in JSX.
  - Reason codes map to `reason.<code>` keys.
- **Styling:** Tailwind with the generated token variables only. No raw hex colours. Verdict colours come from the shared tokens, and `unknown` is never green.
- **Verdict UI:** show the engine status exactly, the member's name, the reasons, and "Information, not medical advice". Label extraction always goes through an editable confirm step before saving.
- **Secrets:** only `NEXT_PUBLIC_SUPABASE_URL`, `NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY`, `NEXT_PUBLIC_API_BASE_URL` and `NEXT_PUBLIC_POSTHOG_KEY`, plus the non-secret `NEXT_PUBLIC_SENTRY_DSN`, `NEXT_PUBLIC_SITE_URL`, `NEXT_PUBLIC_FEATURE_PHONE_OTP`, `NEXT_PUBLIC_FEATURE_EMAIL_OTP` and `NEXT_PUBLIC_FEATURE_VOICE`. No CallMissed key, no service-role key, not even in server code.
- **Security headers:** a strict CSP (nonce-based), `X-Frame-Options: DENY`, a Supabase cookie session (Secure in production, SameSite=Lax; readable by JS by design, ADR 0014) and HSTS.
- **Credit Open Food Facts** wherever its data is shown, including public product pages.
- **Parity:** each feature has an Android counterpart. Component tests use the shared cases in `packages/test-fixtures`.

## Environment variables

| Name | Purpose |
|---|---|
| `NEXT_PUBLIC_SUPABASE_URL` | Supabase project URL |
| `NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY` | Supabase anon (public) key |
| `NEXT_PUBLIC_API_BASE_URL` | FastAPI base URL |
| `NEXT_PUBLIC_POSTHOG_KEY` | PostHog project key (optional in dev) |
| `NEXT_PUBLIC_SENTRY_DSN` | Sentry DSN for the browser (optional in dev); not secret, a DSN can only send events |
| `NEXT_PUBLIC_SITE_URL` | Public site origin (canonical URLs, OAuth redirect); not secret |
| `NEXT_PUBLIC_FEATURE_PHONE_OTP` | Feature flag, `false` until WhatsApp OTP is enabled; not secret |
| `NEXT_PUBLIC_FEATURE_EMAIL_OTP` | Feature flag, `false` until custom SMTP sends 6-digit email codes; not secret |
| `NEXT_PUBLIC_FEATURE_VOICE` | Feature flag, code default `false`; on in dev via the GitHub repo variable (push-to-talk, F10; needs API `VOICE_ENABLED=true`); not secret |
| `SENTRY_DSN` / `SENTRY_AUTH_TOKEN` | Error reporting; the auth token is used only at build time in CI |

`.env.local` is git-ignored. `.env.example` documents the keys.

## Commands

From the repo root: `just web`, `just test-web`, `just e2e`, `just lint`.

From `apps/web` (once scaffolded):

| What | Command |
|---|---|
| Install | `pnpm install` (run at the repo root) |
| Dev server | `pnpm dev` |
| Unit and component tests | `pnpm test` |
| E2E | `pnpm e2e` |
| Lint and format | `pnpm biome check .` |
| Type-check | `pnpm tsc --noEmit` |
| Build | `pnpm build` |

Commit scope: `web`, e.g. `feat(web): scan by photo page`.

<!-- BEGIN:nextjs-agent-rules -->

## This is NOT the Next.js you know

This version has breaking changes — APIs, conventions, and file structure may all differ from your training data. Read the relevant guide in `node_modules/next/dist/docs/` (resolved from this file's directory; in monorepos the `next` package may not be visible from the repo root) before writing any code. Heed deprecation notices.

This block is written and re-added by `next dev` — verify at `node_modules/next/dist/server/lib/generate-agent-files.js`. Removing it from a diff only re-creates the uncommitted change; committing it with your work keeps the tree clean.

<!-- END:nextjs-agent-rules -->
