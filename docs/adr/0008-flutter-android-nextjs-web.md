# ADR 0008: Flutter for Android, Next.js for web, with full feature parity

- **Status:** Accepted. Supersedes ADR 0002.
- **Date:** 2026-11-02

## Context

v1 must ship an Android app (most Indian users) and a web app. The founder wants **every v1 feature on both**. The web app should also bring users in through Google: public product pages and the "How we score" page.

Options considered:

| Option | Codebases | Web quality and SEO | UI effort | Notes |
|---|---|---|---|---|
| A. Flutter for Android + web | 1 (Dart) | Weak: heavy first load, canvas rendering, poor indexing | 1× | Fastest |
| **B. Flutter Android + Next.js web** | 2 (Dart + TS) | **Best:** real HTML, SSR/ISR, indexable | ~1.5–1.8× | Chosen |
| C. React Native (Expo) for both | 1 (TS) | Good, below Next.js for SEO | ~1×, but a full rewrite | Best only for a React-first team |

## Decision

**Option B.**
- **Android:** Flutter, using the existing Flutter skills and strong Android camera and scanner plugins.
- **Web:** Next.js 16 (App Router, TypeScript, Tailwind 4 + shadcn, next-intl, TanStack Query, @supabase/ssr).
- **Flutter web is dropped.**
- **Parity:** both clients implement F1–F17 (`docs/FEATURE_PARITY.md`).

What makes the duplication manageable:
- All logic stays in the API. The clients are thin.
- The clients share a generated API contract, one i18n source, design tokens and test fixtures (ADR 0010).
- Delivery is in vertical slices (ADR 0011).

Web specifics:
- Public pages are statically rendered or ISR.
- Logged-in pages render on the client.
- Barcode scanning uses `BarcodeDetector`, falling back to `@zxing/browser`.
- Label photos use a file input with `capture`.
- Voice uses `MediaRecorder`.

## Consequences

- **UI effort is ~1.5–1.8×.** Full parity within 15 days is tight. Mitigations:
  - contract-first generated clients
  - parallel builders, one per client
  - shared fixtures as the definition of done
  - vertical slices, so both clients integrate from day 4–5
- **Better web:** fast first load, Google-indexable product and methodology pages, and a natural base for the v2 dietitian dashboard.
- **Two UI stacks to maintain:** a change to the verdict or allergy UI must be made and safety-reviewed in both (CODEOWNERS).
- **Platform gaps on web:** camera barcode scanning on iOS Safari depends on the zxing fallback, and voice recording formats differ (webm/opus). Both are covered in FEATURE_PARITY.
- **Hosting:** the web app runs on Cloud Run in Mumbai (ADR 0012), not Firebase Hosting.
