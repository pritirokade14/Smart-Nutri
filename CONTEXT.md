# CONTEXT.md: SmartNutri AI at a glance

**Read this first.** It's a one-page snapshot for anyone, human or AI agent, picking up the project. Details live in the linked docs. Update the **Status** section whenever a milestone moves.

_Last updated: 2026-11-04_

---

## 1. What we're building

**SmartNutri AI** tells an Indian family whether a packaged food is right for **each member**, and tracks what they actually eat.
- **Scan:** barcode first. If the product isn't found, take a photo of the label. The extracted values are always confirmed by the user.
- **Verdict per member:** OK / Caution / Unknown / Avoid, with reasons. Considers diabetes, blood pressure, kids, allergies, and Jain/vegan/veg diets.
- **Also:** a claim checker ("Sugar-free? It contains maltodextrin"), scan-to-log, voice Q&A, and English / हिंदी / मराठी.
- **Not medical advice.** Health thresholds are *pending clinician review*.

**v1 users:** blood-sugar (diabetes, prediabetes, PCOS) · family health managers (kids and elderly parents) · weight loss (including GLP-1).
**Plan 9 (built):** after Terms, users pick up to 3 of 6 user types (health condition, family, weight loss, gym and fitness, allergy or special diet, just eating better). Each gets a focused mode: its own Home cards and tab bar, with everything else in More. Gym users get a protein guide. The type never changes a verdict (ADR 0019).
**Goal:** a startup product. Build in about 15 days (started 2026-11-02). Android public release is gated by the Play closed test (12+ testers × 14 days).

→ [docs/PRODUCT.md](docs/PRODUCT.md) · [v1 spec](docs/superpowers/specs/2026-11-02-smartnutri-v1-design.md) · [FEATURE_PARITY](docs/FEATURE_PARITY.md)

## 2. Platforms and stack (decided)

| Layer | Choice |
|---|---|
| Android app | **Flutter** (Riverpod, go_router, dio, drift, mobile_scanner). Package `com.smartnutri.app` |
| Web app | **Next.js 16** (TypeScript, Tailwind 4 + shadcn, next-intl, @supabase/ssr). **Full feature parity with Android** |
| Backend | **FastAPI** (Python 3.13, uv, SQLAlchemy 2, Alembic). Feature-based layout |
| Rules engine | `apps/api/app/scoring`: pure Python. **Decides every verdict**; the LLM only explains |
| AI + voice | **CallMissed API** (OpenAI-compatible): vision extraction, models per ADR 0021, all India-processed: extraction and explanation `gemma-4-31b`, speech-to-text `saaras:v4`, text-to-speech `bulbul:v3` (fallbacks in `docs/SETUP_ACCOUNTS.md`) |
| Login, database, files | **Supabase** (Mumbai): Google OAuth + email OTP now; phone OTP via WhatsApp later |
| Hosting | **Cloud Run, asia-south1 (Mumbai)** for API + web; Google Play for Android |
| Shared | `packages/api-contract` (generated Dart + TS clients), `i18n`, `design-tokens`, `test-fixtures` |

→ [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) · decisions in [docs/adr/](docs/adr/) (0001–0021)

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
| CallMissed | project owner's CallMissed account (kept in local notes) | keys `smartnutri-dev` (₹2,000 cap), `smartnutri-prod` (₹10,000 cap) | Enterprise (existing credits) |
| Supabase | GitHub `pritirokade14` | org **SmartNutri**, project **smartnutri-dev**, ref `uhjopvrewcwqvugmdhdw`, ap-south-1 | Free (spend cap on) |
| Google Cloud | project owner's Google account (kept in local notes) | project **smartnutri-513518**, Artifact Registry `asia-south1/smartnutri`, budget ₹1,000/month | Free trial (₹28,569 credit) |
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

Plans 1–9 are **code complete and merged to `main`** (PR #3, merge `6a9735f`, 2026-11-04). PR #4 (`4bcf1c0`) switched voice on in dev and PR #5 (`b152a49`) merged the QA fixes. The dev DB is at alembic head `0007_plan9_supplement_category`, and the dev API and web are deployed and healthy.

| Plan | File | Status |
|---|---|---|
| 1. Rules engine | [plan-1](docs/superpowers/plans/2026-11-02-plan-1-rules-engine.md) | Done. Thresholds still PENDING CLINICIAN REVIEW |
| 2. Foundation | `docs/superpowers/plans/2026-11-03-plan-2-foundation.md` | Code complete; dev deploy live |
| 3. M1: barcode → verdict, public product pages | `…-plan-3-m1-barcode-verdict.md` | Code complete; manual real-pack check is USER |
| 4. M2: label scan | [plan-4](docs/superpowers/plans/2026-11-03-plan-4-m2-label-scan.md) | Code complete, merged to `main`; label eval and real-pack check are USER |
| 5. M3: family members, per-member verdicts, explanation, alerts | `…-plan-5-m3-family-verdicts.md` | Code complete, merged (PR #3), deployed to dev |
| 6. M4: scan-to-log, weekly summary, alternatives, compare, share | `…-plan-6-m4-log-share.md` | Code complete, merged (PR #3), deployed to dev |
| 7. M5: voice Q&A, How we score, Report a problem | `…-plan-7-m5-voice-methodology-reports.md` | Code complete; voice is **ON on dev** (repo variables `VOICE_ENABLED` and `NEXT_PUBLIC_FEATURE_VOICE`, 2026-11-04) |
| 8. M6: consent/DPDP, deletion, retention, release checklist | `…-plan-8-m6-launch.md` | Code complete; prod deploy, Play Store and legal are USER |
| 9. User types, focused modes, gym protein guide | [plan-9](docs/superpowers/plans/2026-11-04-plan-9-personas.md) | Code complete, merged (PR #3), deployed to dev. Migrations 0006 (user types) and 0007 (supplement category). ADR 0019 |

**How plans are executed:** `superpowers:subagent-driven-development`, with a ledger in `.superpowers/sdd/<plan>/progress.md` (git-ignored). Independent tasks run in parallel git worktrees. For each slice: the API first → `just contract` → Android ∥ web → `nutrition-safety-reviewer`.

## 8. Status

**Done:**
- Research on users, competitors, tech, regulation and CallMissed (`docs/research/`).
- Monorepo restructure, docs, ADRs, tooling and CI (commit `5f943ff`).
- Accounts: CallMissed keys, Supabase dev project (database tested), Google Cloud project with billing (free trial), OAuth clients, Google login enabled in Supabase, Cloud Run / Artifact Registry / Secret Manager / Build APIs enabled, ₹1,000 budget alert.
- **Plan 1 (rules engine): complete.** Every ruling is listed in `docs/superpowers/plans/2026-11-02-plan-1-rulings.md`. Follow-up rulings R12/R13/R25 (Plan 2 ledger) add a blood-sugar heart-health caution, an `age_unknown` guard for members without a birth year, and `unknown` when saturated fat or salt is missing for blood-sugar members.
- **Plan 2 (foundation): code complete.** Generated clients, login on both apps, CSP/HSTS, Sentry/PostHog with health-data scrubbing, Docker images, CI and the keyless GitHub Actions dev deploy (ADR 0015). Dev API and web are deployed.
- **Plan 3 (M1) and Plan 4 (M2):** barcode and label scan to verdict on API, Android and web. Plan 4 was merged to `main` (PR #2, `7d9fd3d`); dev migration 0002 applied.
- **Plans 5–8 (code complete, merged to `main` in PR #3):**
  - Plan 5: family members, per-member verdicts, claim checker, custom ingredient alerts, LLM explanation (consent gate G1: `terms` for core use, `health_data` to save member health fields, `ai_processing` for explanations and voice).
  - Plan 6: scan-to-log (Android offline queue, web online-only), daily and weekly totals, alternatives, compare, search, share (member statuses opt-in, off by default). ADR 0017.
  - Plan 7: voice Q&A (STT, guarded answer, TTS), How we score, Report a problem. Voice defaults to off in code (`VOICE_ENABLED`, `NEXT_PUBLIC_FEATURE_VOICE`, `FEATURE_VOICE` on Android); dev turns it on through the GitHub repo variables `VOICE_ENABLED` (API, read in `deploy-dev.yml`) and `NEXT_PUBLIC_FEATURE_VOICE` (web build), both `true` since 2026-11-04. To switch it off, set both to `false` and redeploy. No voice audio is stored (ADR 0020).
  - Plan 8: consent and withdrawal (ADR 0018), account deletion with a tombstone (migration `0004_plan8_deleted_accounts`), retention job, EXIF stripping, telemetry allow-list, privacy policy and terms drafts, release checklist (`docs/launch/RELEASE_CHECKLIST.md`).
  - Whole-branch nutrition-safety review: APPROVE WITH CHANGES; the fix batch addressed them.
  - PR #5 QA fixes: Android camera/scanner attach fix, web how-we-score wrap, search `?q=`, tab highlight, Family "You" shown once on both clients, per-member accessible labels, 360px overflow sweep.
- **Plan 9 (user types, focused modes, gym protein guide):** code complete, safety-reviewed, merged (PR #3).
- **Plan 10 slice 1 (daily guide, hide numbers, protein basis):** built on API, Android and web and safety-reviewed (merge pending); the food diary is slice 2.
- **Tests (2026-11-04):** API 3,972; Flutter 1,511; web 1,298 unit and 47 e2e. Experiments E1–E7 were re-run on `2003e9c`.

**Not done, by design or waiting on the user:**
- Android has no release signing yet and nothing is on Play. No prod project exists.
- OG share-card images (`og:image`) are **not built** (TODO in FEATURE_PARITY). `robots.txt`, the sitemap and hreflang exist. The long manual-entry form on mobile is a known minor UX issue.
- Phone OTP is OFF (needs Meta template approval). Email OTP is OFF (needs a domain and SMTP).
- Voice is ON on dev only (repo variables). Prod stays off until the prod launch.

**Next (all USER unless noted):**
1. Run `bash scripts/setup-retention-schedule.sh setup`, then after the deploy `dry-run`, then `schedule` (02:30 IST).
2. Run the label eval, the manual real-pack parity checks, clinician and native-language reviews, lawyer review, Play Store steps (all in section 9 and `docs/launch/RELEASE_CHECKLIST.md`).

## 9. Open items that only the user can do

- [ ] **USER:** `scripts/push-secrets.sh prod` before the prod deploy (dev secrets are already in Secret Manager).
- [ ] **USER (optional): delete the unused dev `voice-answers` bucket** (voice answers come back inline; ADR 0020) and the old web OAuth client secret in GCP (see `docs/SETUP_ACCOUNTS.md`).
- [ ] **USER: retention job schedule** (`scripts/setup-retention-schedule.sh`: `setup`, `dry-run`, `schedule`).
- [ ] **USER: lawyer review** of the privacy policy and terms drafts (`docs/launch/`), including DPDP withdrawal versus erasure (ADR 0018) and children's profiles.
- [ ] **USER: Play Store:** create the Google Play Console **personal** account ($25) and complete ID verification.
- [ ] **USER:** recruit 12–20 closed-test testers once a usable build exists.
- [ ] **USER: clinician or dietitian review** (sheet: `docs/launch/clinician-review.md`) of `apps/api/app/scoring/data/thresholds.yaml` (all values are marked PENDING CLINICIAN REVIEW). Specific questions for them:
  - Over-warning list from Plan 1: rice vermicelli / rava flagged as gluten; pistachio/almond "nuts" flagged for peanut allergy; coconut cream and butter beans flagged for milk; soya keema; chai masala / herbal tea flagged as caffeine for children; plain milk 250 ml for a 2-year-old = avoid; coconut water for diabetics; infant rice cereal salt.
  - Blood-sugar members: is CAUTION the right level for foods high in saturated fat or salt (UK FSA "high" limits: sat fat > 5 g, salt > 1.5 g per 100 g)? Is the 30 g carbs-per-serving threshold right (oats at 26 g per 40 g serving shows ok)?
  - Child rules compare total sugars with a daily free-sugar limit, and ignore saturated fat.
  - Ages come from birth year only. Should infant rules (under 2) also warn about very high natural sugar (dates, raisins), and should a 13-year-old still get child caffeine warnings?
  - Serving sizes: the engine accepts any serving above 0 g and up to 5000 g. Should there be a realistic lower bound (e.g. 1 g)? A confirmed serving of 0.0001 g would inflate per-100 g values by about a million times. Post-conversion plausibility catches this, except when every value is 0.
  - Plan 9: the `build_muscle` protein target of 1.6 g/kg (adults with a weight; should members with diabetes or BP keep it? there is no kidney field), whether weight loss should get 1.2 g/kg, the 10 % protein-claim shortfall, and supplements (caution for ages 2–17, avoid under 2).
  - Open Food Facts data is crowd-sourced; the engine treats it at confidence 0.9 (allergen rules run, so an incomplete OFF ingredient list could show `ok` for an allergic member). Is that acceptable, or should OFF products be `unknown` for allergic members unless the label is confirmed?
- [ ] **USER: M2 label scan:**
  - (a) Photograph 40–60 label packs for the eval (checklist in `apps/api/tests/evals/labels/README.md`) and approve the CallMissed spend.
  - (b) Do the manual 3-pack parity check on a phone and in a browser, including one Hindi or bilingual label and one per-serving-only label.
  - (c) Smoke-test a real photo upload on both clients on dev after the next deploy.
- [ ] **USER: native Hindi and Marathi speaker review** of all UI strings: checklist in `packages/i18n/NATIVE_REVIEW.md`.
- [ ] **USER:** before launch: domain name, privacy policy and terms, Supabase prod (Pro), CallMissed plan check, WhatsApp OTP template approval.
- [ ] **USER:** before Play submission, decide whether to keep the Android package name `com.smartnutri.app` (it is permanent once published).
