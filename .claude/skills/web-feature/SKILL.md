---
name: web-feature
description: Use when adding or changing a page, feature, component, route, form or hook in apps/web (the Next.js web app) — logged-in app pages or public SEO pages — including i18n strings, styling with design tokens, and Vitest/Playwright tests.
---

# Adding a Next.js web feature

The stack is Next.js 16 App Router, React 19, TypeScript strict, Tailwind 4 with the generated token variables, shadcn, next-intl, `@supabase/ssr`, TanStack Query, and the **generated client `@smartnutri/api-client`**. See `apps/web/AGENTS.md`. The same feature is built for Android in `apps/app` (full parity), usually in parallel.

## Folder shape

```
src/features/<feature>/
  api/         <feature>.ts: functions and query hooks wrapping @smartnutri/api-client
  components/  <Thing>.tsx (client components only where interactive)
  hooks/
src/app/[locale]/(app)/<route>/page.tsx      # logged-in page (Server Component)
src/app/[locale]/(public)/<route>/page.tsx   # public, indexable page (static/ISR)
tests/features/<feature>/*.test.tsx          # Vitest + Testing Library
e2e/<feature>.spec.ts                        # Playwright, for key flows
```

## Steps

1. **Check that the contract is current.** The endpoint must exist, and `just contract` must have been run. Use `@smartnutri/api-client` types and calls; never write raw `fetch` to the API or hand-written response types.
2. **Data access:**
   - Server Components call the API through `src/lib/api`, with the session from `src/lib/supabase/server.ts`.
   - Interactive client components use TanStack Query hooks in `features/<f>/api`.
   - Map `error.code` to i18n messages.
3. **Page:** a Server Component by default. Add `"use client"` only to the leaf components that need state, the camera, the microphone or forms.
4. **Forms:** react-hook-form with a zod schema that mirrors the API constraints. Show validation messages from i18n.
5. **Strings:** add keys to `packages/i18n/messages/{en,hi,mr}.json` (all three). Use `useTranslations` / `getTranslations`. API reason codes map to `reason.<code>`. No string literals in JSX.
6. **Styling:**
   - Tailwind classes backed by the generated CSS variables from `packages/design-tokens`, plus shadcn components in `components/ui`.
   - No raw hex colours. Use the verdict tokens for statuses.
7. **Tests:**
   - Vitest component tests for the loading, error and data states.
   - For verdict components, use the shared cases in `packages/test-fixtures`.
   - Add or extend a Playwright spec for the main flow.
8. **Check:** `pnpm test && pnpm tsc --noEmit && pnpm biome check . && pnpm build`, then `just e2e` for the affected spec.

## Route groups

- **`(public)`** (landing, how-we-score, `p/[barcode]`):
  - No session needed; static or ISR, with metadata for SEO.
  - **Generic product info only.** Never member names, conditions, verdicts or logs.
  - Show the Open Food Facts attribution when its data is shown.
- **`(app)`:** middleware redirects to sign-in without a session. Personal data is fetched per request; never cache it statically.

## Browser capabilities

- **Barcode:** `BarcodeDetector` where available, falling back to `@zxing/browser`. Always offer manual barcode entry and "scan the label instead".
- **Label photo:** `<input type="file" accept="image/*" capture="environment">`. Compress client-side to under 8 MB before upload.
- **Voice:** `MediaRecorder`, max 30 s. Play the TTS reply with an `<audio>` element.
- Camera and microphone need HTTPS (localhost is fine) and a user gesture.

## Verdict UI rules (health app)

- Show the engine status exactly. `unknown` is never green. An allergy `unknown` says "We couldn't read the ingredients. Check the pack."
- Each verdict shows its reasons, the member's name, and "Information, not medical advice".
- Label extraction always goes through an editable confirm step before saving.
- **Never compute or adjust a verdict in the browser or in server code.**

## Pitfalls

- Putting secrets in `NEXT_PUBLIC_*`, or importing server-only modules into client components (use `import "server-only"`).
- Fetching personal data in a `(public)` page, or statically caching an `(app)` page.
- Editing generated code (`@smartnutri/api-client`, token CSS). Your change will be overwritten.
