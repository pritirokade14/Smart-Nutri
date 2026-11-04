# Feature Parity: API × Android × Web

**Rule (ADR 0008, ADR 0011):** every v1 feature F1–F20 (F18–F20 added by Plan 9) ships on **both** the Android app (Flutter) and the web app (Next.js). Nothing is removed from either platform.

## Definition of done (per feature)

A feature is done only when all of these hold:
1. The API endpoint is merged, and `packages/api-contract/openapi.json` plus both generated clients are regenerated and committed.
2. The feature works on **Android and web**, using the generated clients. Neither client contains business logic.
3. Shared fixtures (`packages/test-fixtures`) pass in API tests, Flutter widget tests and web component tests.
4. Every string exists in `packages/i18n/messages/{en,hi,mr}.json`, and all colours come from `packages/design-tokens`.
5. If the feature touches verdicts, allergies, prompts or fixtures, the `nutrition-safety-reviewer` has approved it.

Status values: ⬜ not started · 🟡 code complete, waiting on a USER gate (manual check, review, deploy or eval) · ✅ done.

**Honest state (2026-11-04):** F1–F20 are code complete on API, Android and web on `v1-rebuild` (API 2811, Flutter 1192, web 1083 tests). None is ✅ yet: each waits on at least one USER step (merge and deploy to dev, manual real-pack parity checks on a phone and in a browser, label eval, clinician and native-language review). Plan 4 and Plan 9 (F18–F20, PR #3) are merged to `main`.

| # | Feature | Milestone | API | Android (Flutter) | Web (Next.js) | Web-specific notes |
|---|---|---|---|---|---|---|
| F1 | Accounts: Google, email OTP; phone OTP behind a flag | Plan 2 / M1 | 🟡 | 🟡 | 🟡 | `@supabase/ssr` cookie session, `/auth/callback` route for OAuth and magic link, Secure + SameSite=Lax cookies, JS-readable by design with strict CSP and HSTS (ADR 0014) **Status:** Google login works on dev web; email OTP is hidden by flag until a domain and SMTP exist; phone OTP is OFF until Meta approves the template. Manual login check on web and Android after the deploy is USER. |
| F2 | Family members | M3 | 🟡 | 🟡 | 🟡 | react-hook-form + zod forms; same validation messages from i18n **Status:** code complete on all three (Plan 5). Not merged to `main`; manual check USER. |
| F3 | Scan by barcode | M1 | 🟡 | 🟡 | 🟡 | `BarcodeDetector` where supported, else `@zxing/browser` on the camera stream. Manual entry is always available. Desktop uses the webcam or manual entry. | **Status (M1):** built and tested on API, Android and web (shared golden fixtures + identical reason text in en/hi/mr); ✅ after the manual real-pack check on a phone and in a browser. |
| F4 | Scan by label photo plus confirm | M2 | 🟡 | 🟡 | 🟡 | `<input type="file" accept="image/*" capture="environment">`. Desktop: file upload or drag and drop. The confirm form is identical. | **Status (M2):** code done on API, Android and web (ADR 0016). 🟡 until the label eval (plan 4, Task 6 Step 6) has run and the manual real-pack check passes. Known differences: after a reload, web loses the draft and shows "scan not found" with Retake / Enter manually; Android opening the confirm route with no draft shows an empty manual form. |
| F5 | Rules engine | Plan 1 | 🟡 | n/a (server) | n/a (server) | The clients only render reason codes **Status:** engine complete; thresholds PENDING CLINICIAN REVIEW (USER). |
| F6 | Verdict per member | M3 | 🟡 | 🟡 | 🟡 | Rendered from shared tokens; fixtures check each member's colour and reason **Status:** code complete; shared fixtures pass on all three; nutrition-safety review approved with changes (fixed in the final batch). |
| F7 | AI explanation (en/hi/mr) | M3 | 🟡 | 🟡 | 🟡 | Streamed or awaited text; same disclaimer component **Status:** code complete. Always an object with `source` llm or unavailable; the card is hidden when unavailable. Needs `ai_processing` consent. hi/mr strings await native review (USER). |
| F8 | Scan-to-log plus daily and weekly totals | M4 | 🟡 | 🟡 | 🟡 | Android keeps an offline log (drift) and syncs it. Web is online-only in v1 and says so. **Status:** code complete (Plan 6). Android queues offline and syncs; web is online-only and says so. |
| F9 | Alternatives, search, compare | M4 | 🟡 | 🟡 | 🟡 | Compare is a two-column table on desktop and stacked on mobile web **Status:** code complete (Plan 6): alternatives (never suggests `avoid`), search, compare. |
| F10 | Voice Q&A | M5 | 🟡 | 🟡 | 🟡 | `MediaRecorder` upload on web; recorder on Android; answer audio comes inline (base64 mp3) and is never stored (ADR 0020); text only when it would be over about 1 MB. Needs HTTPS and mic permission. **Status:** code complete (Plan 7) but **OFF**: `VOICE_ENABLED=false`, `NEXT_PUBLIC_FEATURE_VOICE=false`, `FEATURE_VOICE` off on Android. Turning it on needs the paid STT/TTS probe (USER). No voice bucket or voice retention is needed. |
| F11 | Trust and compliance (disclaimer, consent, deletion, attribution) | M6 (consent from M1) | 🟡 | 🟡 | 🟡 | Cookie notice (essential cookies only), OFF attribution in the footer on product pages | **Status (M1):** OFF attribution and the disclaimer on every result and public product page; consent/deletion in later milestones. **Status:** consent, withdrawal, account deletion, retention job and policy pages are code complete (Plan 8, ADR 0018). Privacy policy and terms are drafts awaiting a lawyer (USER). |
| F12 | "How we score" page | M5 | 🟡 | 🟡 | 🟡 | **Public, statically rendered/ISR** at `/[locale]/how-we-score` for Google; in-app link on Android **Status:** code complete. Source URLs are not yet verified (`url_verified` false). |
| F13 | Result at a glance (colour, grade, one-line reason) | M1 (basic) → M3 | 🟡 | 🟡 | 🟡 | Same component contract on both clients; colour from tokens | **Status (M1, basic):** verdict colour from tokens (unknown never green), grade letter tile, allergen/avoid/unknown reasons always visible, profile-not-set-up note. **Status:** full result (per-member rows, grade tile, reasons, disclaimer) shipped with Plan 5; manual real-pack check is USER. |
| F14 | Report a problem | M5 | 🟡 | 🟡 | 🟡 | Dialog with the four reasons plus a note **Status:** code complete (Plan 7). |
| F15 | Product not found leads to a label-photo result | M2 | 🟡 | 🟡 | 🟡 | The web flow switches to the upload step automatically | **Status (M2):** code done; 🟡 pending the label eval (plan 4, Task 6 Step 6) and the manual real-pack check. Same reload difference as F4. |
| F16 | Custom ingredient alerts | M3 | 🟡 | 🟡 | 🟡 | Toggles in the member form **Status:** code complete (Plan 5). |
| F17 | Share result or weekly summary | M4 | 🟡 | 🟡 | 🟡 | Web Share API on mobile browsers; desktop fallback "Copy link" and a WhatsApp link (`wa.me/?text=`). Default share is product name plus Nutri-Score; member statuses are opt-in per share. The link appears only when the site URL is configured. **Status:** code complete (Plan 6). **No OG share-card image yet: TODO** (not promised for v1). |
| F18 | User types: picker after Terms (up to 3 of 6, one follow-up each, skippable), confirm-only pre-fill of the account holder's profile, edit in Profile | Plan 9 | 🟡 | 🟡 | 🟡 | `/[locale]/welcome` after the terms step (`UserTypesGate`); same consent dialog for health types. **Status:** built and merged (PR #3; Plan 9 Tasks 1, 2, 9, 12); waits on the same USER gates as F1–F17. Never sent to analytics; never changes a verdict (ADR 0019). Migration 0005. |
| F19 | Focused modes: per-type Home cards and 5-tab bar, More menu, mode switcher; scan and verdicts identical in every mode | Plan 9 | 🟡 | 🟡 | 🟡 | Mobile bottom bar shows the mode's 5 tabs; the desktop rail shows the 5 tabs plus a More group. Both clients mirror `packages/test-fixtures/modes/layouts.json`. **Status:** built and merged (PR #3; Plan 9 Tasks 8, 10, 13); waits on the same USER gates as F1–F17. |
| F20 | Gym protein guide: `build_muscle` goal and daily protein guide, protein per serving / 100 g / 100 kcal, protein and whey claim checks, higher-protein sort, compare protein columns and a typed-in price per scoop (client-only), supplements not graded | Plan 9 | 🟡 | 🟡 | 🟡 | `/[locale]/protein`; the public product page also shows protein facts (no personal data). Price per scoop lives only in component state. **Status:** built and merged (PR #3; Plan 9 Tasks 3–7, 11, 14); waits on the same USER gates as F1–F17. Thresholds PENDING CLINICIAN REVIEW; supplements (Task 7, migration 0006) can slip. |

## Web-only additions (do not break parity)

- **Public product pages** `/[locale]/p/[barcode]`: generic facts only (Nutri-Score "calculated by SmartNutri", "high in", claim checks, ingredients, OFF attribution). **Never personal verdicts.** Served by `GET /v1/products/{barcode}/public`.
- **Landing page**, `sitemap.xml`, `hreflang` links for en, hi and mr. `robots.txt` (app routes disallowed). **TODO (not built):** per-page Open Graph images.

## Android-only additions

- Offline scan-to-log (drift) with background sync.
- Native camera barcode scanning (`mobile_scanner`).
