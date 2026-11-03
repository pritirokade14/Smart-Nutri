# CONTEXT.md: SmartNutri AI at a glance

**Read this first.** It's a one-page snapshot for anyone, human or AI agent, picking up the project. Details live in the linked docs. Update the **Status** section whenever a milestone moves.

_Last updated: 2026-11-03_

---

## 1. What we're building

**SmartNutri AI** tells an Indian family whether a packaged food is right for **each member**, and tracks what they actually eat.
- **Scan:** barcode first. If the product isn't found, take a photo of the label. The extracted values are always confirmed by the user.
- **Verdict per member:** OK / Caution / Unknown / Avoid, with reasons. Considers diabetes, blood pressure, kids, allergies, and Jain/vegan/veg diets.
- **Also:** a claim checker ("Sugar-free? It contains maltodextrin"), scan-to-log, voice Q&A, and English / हिंदी / मराठी.
- **Not medical advice.** Health thresholds are *pending clinician review*.

**v1 users:** blood-sugar (diabetes, prediabetes, PCOS) · family health managers (kids and elderly parents) · weight loss (including GLP-1).
**Goal:** a startup product. Build in about 15 days (started 2026-11-02). Android public release is gated by the Play closed test (12+ testers × 14 days).

→ [docs/PRODUCT.md](docs/PRODUCT.md) · [v1 spec](docs/superpowers/specs/2026-11-02-smartnutri-v1-design.md) · [FEATURE_PARITY](docs/FEATURE_PARITY.md)

## 2. Platforms and stack (decided)

| Layer | Choice |
|---|---|
| Android app | **Flutter** (Riverpod, go_router, dio, drift, mobile_scanner). Package `com.smartnutri.app` |
| Web app | **Next.js 16** (TypeScript, Tailwind 4 + shadcn, next-intl, @supabase/ssr). **Full feature parity with Android** |
| Backend | **FastAPI** (Python 3.13, uv, SQLAlchemy 2, Alembic). Feature-based layout |
| Rules engine | `apps/api/app/scoring`: pure Python. **Decides every verdict**; the LLM only explains |
| AI + voice | **CallMissed API** (OpenAI-compatible): vision extraction, explanations (`sarvam-105b`), speech-to-text `saaras:v4`, text-to-speech `bulbul` |
| Login, database, files | **Supabase** (Mumbai): Google OAuth + email OTP now; phone OTP via WhatsApp later |
| Hosting | **Cloud Run, asia-south1 (Mumbai)** for API + web; Google Play for Android |
| Shared | `packages/api-contract` (generated Dart + TS clients), `i18n`, `design-tokens`, `test-fixtures` |

→ [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) · decisions in [docs/adr/](docs/adr/) (0001–0016)

## 3. Repository map

```
apps/api/    FastAPI + rules engine     apps/app/   Flutter Android     apps/web/  Next.js
packages/    api-contract · i18n · design-tokens · test-fixtures
supabase/    auth config + hooks (tables/RLS are owned by Alembic in apps/api)
docs/        PRODUCT · ARCHITECTURE · FEATURE_PARITY · SETUP_ACCOUNTS · adr/ · research/ · superpowers/{specs,plans}
.claude/     skills + subagents         .github/    CI (pinned SHAs, read-only tokens), CODEOWNERS
```

Commands: `just` lists everything (`just setup`, `just test`, `just dev`, `just android`, `just contract`).

## 4. Accounts and IDs (no secrets here)

| Service | Owner account | Identifiers | Plan |
|---|---|---|---|
| CallMissed | prasaddhanade33@gmail.com | keys `smartnutri-dev` (₹2,000 cap), `smartnutri-prod` (₹10,000 cap) | Enterprise (existing credits) |
| Supabase | GitHub `pritirokade14` | org **SmartNutri**, project **smartnutri-dev**, ref `uhjopvrewcwqvugmdhdw`, ap-south-1 | Free (spend cap on) |
| Google Cloud | pritirokade08@gmail.com | project **smartnutri-513518**, Artifact Registry `asia-south1/smartnutri`, budget ₹1,000/month | Free trial (₹28,569 credit) |
| Google OAuth | same project | consent screen "SmartNutri AI" (External, testing); clients `smartnutri-web`, `smartnutri-android-debug` | — |
| GitHub | pritirokade14 | `pritirokade14/Smart-Nutri` (public), branch `v1-rebuild` | Free |
| Google Play | not created yet | personal account planned ($25 one-time) | — |

**gcloud rule:** this Mac's default gcloud profile belongs to other companies. For SmartNutri **always** use
`CLOUDSDK_ACTIVE_CONFIG_NAME=smartnutri gcloud …` (project `smartnutri-513518`, region `asia-south1`). Never change the default profile.

## 5. Secrets and env files

- **Real values live only in git-ignored files:** `apps/api/.env`, `apps/api/.env.production`, `apps/web/.env.local`, `apps/app/env/dev.json`. Templates are the committed `*.example` files.
- **CallMissed, Supabase secret and DB URL:** `apps/api` only. **Never** in the web or Android app. Anything named `NEXT_PUBLIC_*` is public.
- **Never print secrets** in chat or logs. Copying secrets into Google Secret Manager is done by the user running a script (automated secret-store writes are blocked by policy).

## 6. Non-negotiable rules

See [AGENTS.md](AGENTS.md). In short:
- The rules engine decides; the LLM explains.
- Never invent nutrition data. **Unknown ≠ safe.**
- Thresholds live in YAML.
- No medical claims.
- Open Food Facts is ODbL: credit it and keep its data separate.
- Every string goes through i18n.
- Feature parity on Android + web.
- Never hand-edit generated code.

## 7. Plans and build order

| Plan | File | Status |
|---|---|---|
| 1. Rules engine | [plan-1](docs/superpowers/plans/2026-11-02-plan-1-rules-engine.md) | 🔄 in progress (subagent-driven, parallel waves) |
| 2. Foundation (API skeleton, auth, DB/RLS, contract, i18n/tokens, app + web shells, CI, dev deploy) | `docs/superpowers/plans/2026-11-03-plan-2-foundation.md` | ✍️ being written |
| 3. M1: barcode → verdict (Android + web), public product pages | `…-plan-3-m1-barcode-verdict.md` | ✍️ being written |
| 4. M2: label photo → AI extraction → confirm | [plan-4](docs/superpowers/plans/2026-11-03-plan-4-m2-label-scan.md) | 🔄 code complete; M2 gates open (see Status) |
| 5. M3: family members, per-member verdicts, claims, custom alerts | `…-plan-5-m3-family-verdicts.md` | ✍️ being written |
| 6. M4: scan-to-log, weekly summary, alternatives, share | `…-plan-6-m4-log-share.md` | ✍️ being written |
| 7. M5: voice Q&A, AI explanation, How we score, Report a problem | `…-plan-7-m5-voice-methodology-reports.md` | ✍️ being written |
| 8. M6: hardening, consent/DPDP, prod deploy, Play closed test | `…-plan-8-m6-launch.md` | ✍️ being written |

**How plans are executed:** `superpowers:subagent-driven-development`, with a ledger in `.superpowers/sdd/<plan>/progress.md` (git-ignored). Independent tasks run in parallel git worktrees. For each slice: the API first → `just contract` → Android ∥ web → `nutrition-safety-reviewer`.

## 8. Status

**Done:**
- Research on users, competitors, tech, regulation and CallMissed (`docs/research/`).
- Monorepo restructure, docs, ADRs, tooling and CI (commit `5f943ff`).
- Accounts: CallMissed keys, Supabase dev project (database tested), Google Cloud project with billing (free trial), OAuth clients, Google login enabled in Supabase, Cloud Run / Artifact Registry / Secret Manager / Build APIs enabled, ₹1,000 budget alert.
- **Plan 1 (rules engine): complete.** Every ruling is listed in `docs/superpowers/plans/2026-11-02-plan-1-rulings.md`. Follow-up rulings R12/R13/R25 (Plan 2 ledger) add a blood-sugar heart-health caution, an `age_unknown` guard for members without a birth year, and `unknown` when saturated fat or salt is missing for blood-sugar members.
- **Plan 2 (foundation), in progress:** config/logging/errors, health check, Supabase JWT verification, database baseline with RLS (ADR 0013: clients never write through the Supabase Data API), `/v1/me`, rate limits, shared i18n (en/hi/mr) with an engine-param contract test, design tokens, shared test fixtures, Next.js web shell. Live check against the dev database passed (`/v1/health` 200).

- **Plan 2 (foundation): code complete.** Generated Dart/TS clients, Flutter and web login, CSP/HSTS, Sentry/PostHog with health-data scrubbing, Docker images, CI, and the GitHub Actions dev-deploy workflow (keyless WIF, ADR 0015). What's left is the user's one-time deploy setup in `docs/SETUP_ACCOUNTS.md`.
- **Plan 3 (M1: barcode → verdict): code complete on API, Android and web.** Barcode lookup (own products → Open Food Facts cache → OFF), safety-reviewed OFF mapping, `POST /v1/analyze`, a public product page, and scan/result screens on both clients. The clients render identical reason text in en/hi/mr, asserted by a shared fixture.
- **Plan 4 (M2: label scan): code complete on `v1-rebuild`** (API, Android and web). Still open: a final client fix round (R20/R21: the server sends confirm hints, clients render them), the label eval run (needs the photo set and the CallMissed spend) and the manual real-pack check. The extraction model is not chosen yet. See ADR 0016.

**Next:**
- User: the one-time deploy setup (protect `main`, `push-secrets.sh`, `setup-github-deploy.sh`, the repo variable, `db-migrate`), then push and open the PR to `main`.
- After the first dev deploy: a manual login check (Google and email OTP) on web and Android, and the M1 real-pack parity check on a phone and in a browser.
- Finish the M2 gates (client fix round, label eval, manual real-pack check), then Plan 5.

## 9. Open items that only the user can do

- [ ] Run `scripts/push-secrets.sh` (created in Plan 2) to copy secrets into Secret Manager before the first deploy.
- [ ] Create the Google Play Console **personal** account ($25) and complete ID verification.
- [ ] Recruit 12–20 closed-test testers once a usable build exists.
- [ ] Clinician or dietitian review of `apps/api/app/scoring/data/thresholds.yaml` (all values are marked PENDING CLINICIAN REVIEW). Specific questions for them:
  - Over-warning list from Plan 1: rice vermicelli / rava flagged as gluten; pistachio/almond "nuts" flagged for peanut allergy; coconut cream and butter beans flagged for milk; soya keema; chai masala / herbal tea flagged as caffeine for children; plain milk 250 ml for a 2-year-old = avoid; coconut water for diabetics; infant rice cereal salt.
  - Blood-sugar members: is CAUTION the right level for foods high in saturated fat or salt (UK FSA "high" limits: sat fat > 5 g, salt > 1.5 g per 100 g)? Is the 30 g carbs-per-serving threshold right (oats at 26 g per 40 g serving shows ok)?
  - Child rules compare total sugars with a daily free-sugar limit, and ignore saturated fat.
  - Ages come from birth year only. Should infant rules (under 2) also warn about very high natural sugar (dates, raisins), and should a 13-year-old still get child caffeine warnings?
  - Serving sizes: the engine accepts any serving above 0 g and up to 5000 g. Should there be a realistic lower bound (e.g. 1 g)? A confirmed serving of 0.0001 g would inflate per-100 g values by about a million times. Post-conversion plausibility catches this, except when every value is 0.
  - Open Food Facts data is crowd-sourced; the engine treats it at confidence 0.9 (allergen rules run, so an incomplete OFF ingredient list could show `ok` for an allergic member). Is that acceptable, or should OFF products be `unknown` for allergic members unless the label is confirmed?
- [ ] M2 label scan:
  - (a) Photograph 40–60 label packs for the eval (checklist in `apps/api/tests/evals/labels/README.md`) and approve the CallMissed spend.
  - (b) Do the manual 3-pack parity check on a phone and in a browser, including one Hindi or bilingual label and one per-serving-only label.
  - (c) Smoke-test a real photo upload on both clients on dev after the next deploy.
- [ ] Native Hindi and Marathi speaker review of all UI strings: checklist in `packages/i18n/NATIVE_REVIEW.md`.
- [ ] Before launch: domain name, privacy policy and terms, Supabase prod (Pro), CallMissed plan check, WhatsApp OTP template approval.
- [ ] Before Play submission, decide whether to keep the Android package name `com.smartnutri.app` (it is permanent once published).
