# Feature Parity: API × Android × Web

**Rule (ADR 0008, ADR 0011):** every v1 feature F1–F17 ships on **both** the Android app (Flutter) and the web app (Next.js). Nothing is removed from either platform.

## Definition of done (per feature)

A feature is done only when all of these hold:
1. The API endpoint is merged, and `packages/api-contract/openapi.json` plus both generated clients are regenerated and committed.
2. The feature works on **Android and web**, using the generated clients. Neither client contains business logic.
3. Shared fixtures (`packages/test-fixtures`) pass in API tests, Flutter widget tests and web component tests.
4. Every string exists in `packages/i18n/messages/{en,hi,mr}.json`, and all colours come from `packages/design-tokens`.
5. If the feature touches verdicts, allergies, prompts or fixtures, the `nutrition-safety-reviewer` has approved it.

Status values: ⬜ not started · 🟡 in progress · ✅ done.

| # | Feature | Milestone | API | Android (Flutter) | Web (Next.js) | Web-specific notes |
|---|---|---|---|---|---|---|
| F1 | Accounts: Google, email OTP; phone OTP behind a flag | Plan 2 / M1 | 🟡 | 🟡 | 🟡 | `@supabase/ssr` cookie session, `/auth/callback` route for OAuth and magic link, Secure + SameSite=Lax cookies, JS-readable by design with strict CSP and HSTS (ADR 0014) |
| F2 | Family members | M3 | ⬜ | ⬜ | ⬜ | react-hook-form + zod forms; same validation messages from i18n |
| F3 | Scan by barcode | M1 | 🟡 | 🟡 | 🟡 | `BarcodeDetector` where supported, else `@zxing/browser` on the camera stream. Manual entry is always available. Desktop uses the webcam or manual entry. | **Status (M1):** built and tested on API, Android and web (shared golden fixtures + identical reason text in en/hi/mr); ✅ after the manual real-pack check on a phone and in a browser.
| F4 | Scan by label photo plus confirm | M2 | ⬜ | ⬜ | ⬜ | `<input type="file" accept="image/*" capture="environment">`. Desktop: file upload or drag and drop. The confirm form is identical. |
| F5 | Rules engine | Plan 1 | ⬜ | n/a (server) | n/a (server) | The clients only render reason codes |
| F6 | Verdict per member | M3 | ⬜ | ⬜ | ⬜ | Rendered from shared tokens; fixtures check each member's colour and reason |
| F7 | AI explanation (en/hi/mr) | M3 | ⬜ | ⬜ | ⬜ | Streamed or awaited text; same disclaimer component |
| F8 | Scan-to-log plus daily and weekly totals | M4 | ⬜ | ⬜ | ⬜ | Android keeps an offline log (drift) and syncs it. Web is online-only in v1 and says so. |
| F9 | Alternatives, search, compare | M4 | ⬜ | ⬜ | ⬜ | Compare is a two-column table on desktop and stacked on mobile web |
| F10 | Voice Q&A | M5 | ⬜ | ⬜ | ⬜ | `MediaRecorder` (webm/opus) upload; the API converts it if needed. Answer audio plays in an `<audio>` element. Needs HTTPS and mic permission. |
| F11 | Trust and compliance (disclaimer, consent, deletion, attribution) | M6 (consent from M1) | 🟡 | 🟡 | 🟡 | Cookie notice (essential cookies only), OFF attribution in the footer on product pages | **Status (M1):** OFF attribution and the disclaimer on every result and public product page; consent/deletion in later milestones.
| F12 | "How we score" page | M5 | ⬜ | ⬜ | ⬜ | **Public, statically rendered/ISR** at `/[locale]/how-we-score` for Google; in-app link on Android |
| F13 | Result at a glance (colour, grade, one-line reason) | M1 (basic) → M3 | 🟡 | 🟡 | 🟡 | Same component contract on both clients; colour from tokens | **Status (M1, basic):** verdict colour from tokens (unknown never green), grade letter tile, allergen/avoid/unknown reasons always visible, profile-not-set-up note.
| F14 | Report a problem | M5 | ⬜ | ⬜ | ⬜ | Dialog with the four reasons plus a note |
| F15 | Product not found leads to a label-photo result | M2 | ⬜ | ⬜ | ⬜ | The web flow switches to the upload step automatically |
| F16 | Custom ingredient alerts | M3 | ⬜ | ⬜ | ⬜ | Toggles in the member form |
| F17 | Share result or weekly summary | M4 | ⬜ | ⬜ | ⬜ | Web Share API on mobile browsers. Desktop fallback: "Copy link" and a WhatsApp link (`wa.me/?text=`). The shared card image is rendered server-side (OG image). |

## Web-only additions (do not break parity)

- **Public product pages** `/[locale]/p/[barcode]`: generic facts only (Nutri-Score "calculated by SmartNutri", "high in", claim checks, ingredients, OFF attribution). **Never personal verdicts.** Served by `GET /v1/products/{barcode}/public`.
- **Landing page** and `sitemap.xml`, `robots.txt` and `hreflang` links for en, hi and mr.

## Android-only additions

- Offline scan-to-log (drift) with background sync.
- Native camera barcode scanning (`mobile_scanner`).
