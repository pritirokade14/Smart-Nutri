# v1 release checklist (`v1.0.0-beta.1`)

> Plan 8 Task 16. Status values: `DONE`, `TODO`, `USER` (only the user can do it), `BLOCKED` (waiting on something named in the note).
> Update a line only with evidence: a commit, a command output, or a dashboard check.
> Last updated: 2026-11-03, after the Plan 8 code tasks (API side).

## Code and review

| # | Item | Status | Notes |
|---|---|---|---|
| 1 | `just test` green (API, Android, web) | TODO | API: 2155 passed on the Plan 8 branch. Android and web need the Wave 2 client work. |
| 2 | CI green on `v1-rebuild` | TODO | Local CI per user preference, then the PR to `main` |
| 3 | nutrition-safety-reviewer approved (Plans 5–8) | TODO | Plan 8 touches consent gating, the fixture-free telemetry allow-list and the clinician sheet |
| 4 | Whole-branch code review (Opus) | TODO | |
| 5 | gitleaks clean | DONE (API branch) | `gitleaks detect`: no leaks (187 commits). Re-run on the merged branch. |
| 6 | F11 on all three surfaces (consent withdrawal, delete account, policy pages) | TODO | API done (`consents_list.needs_update`, gate, `me_delete`). Android and web screens: Wave 2. |
| 7 | Disclaimer on every verdict, explanation and voice surface (Android and web tests) | TODO | Client compliance tests from Plan 8 Task 6 |
| 8 | Web security headers e2e (`security-headers.spec.ts`) | TODO | Web agent |

## Legal and clinical

| # | Item | Status | Notes |
|---|---|---|---|
| 9 | Privacy policy and terms reviewed by a lawyer | USER | Drafts: `docs/launch/privacy-policy.md`, `terms.md`. Must include DPDP s. 8(7) withdrawal versus erasure (ADR 0018), grievance officer details and children's profiles (s. 9). |
| 10 | Clinician sheet signed | USER | `docs/launch/clinician-review.md` (35 thresholds). Until signed, keep `# PENDING CLINICIAN REVIEW` and the methodology banner. |
| 11 | Native-speaker review of hi and mr | USER | `packages/i18n/NATIVE_REVIEW.md` |
| 12 | Methodology source URLs verified (`url_verified`) | TODO | All `false` today |

## Production (Plan 8 Tasks 8–11)

| # | Item | Status | Notes |
|---|---|---|---|
| 13 | Supabase `smartnutri-prod` (Mumbai, Pro) created | USER | Task 8 Step 1 (payment) |
| 14 | Prod migrations at head | TODO | Task 8 Step 2. The storage buckets (`label-photos` and `voice-answers`, both used by deletion and retention) are **not** created by migrations. Create them private in the dashboard, or add a guarded migration (see `api-report.md`). |
| 15 | Prod secrets in Secret Manager | USER | `bash scripts/push-secrets.sh prod --dry-run`, then `! bash scripts/push-secrets.sh prod` |
| 16 | API and web deployed (min 1, max 4) | TODO | Task 10. `ENVIRONMENT=prod` requires `ALLOWED_ORIGINS` set to https origins, or the API refuses to start. |
| 17 | Retention job and scheduler (02:30 IST) | TODO | `python -m app.jobs.retention`. Run `--dry-run` once first. Expect `photos_deleted=0 voice_deleted=0 scans_nulled=0` on a new project. |
| 18 | Consent, deletion and retention verified on prod | TODO | |
| 19 | Sentry test error shows no PII | TODO | The event must have no body, no query, no auth header, and a hashed user id |
| 20 | PostHog shows only allow-listed events | TODO | `ALLOWED_EVENTS` in `app/integrations/posthog.py`. The clients must mirror it. |
| 21 | Load smoke numbers recorded | TODO | `uv run --with httpx python scripts/load_smoke.py --base-url https://<api> --rps 20 --seconds 60 --barcode <seeded>`. Record p50, p95, max and status counts here. Note: the public limit (60 per minute per IP) gives 429s at 20 rps. |
| 22 | Domain and HTTPS (`app.<domain>`, `api.<domain>`), HSTS | USER, then TODO | Task 11. The API sends HSTS in prod. |
| 23 | Google login on prod web and on the Play internal build | TODO | Task 13 Step 5 |
| 24 | ₹1,000 GCP budget alert in place | USER | |

## Play Store (Tasks 12–14)

| # | Item | Status | Notes |
|---|---|---|---|
| 25 | Release signing and `com.smartnutri.app` in `build.gradle.kts` | TODO | Task 12 Step 1 (Android agent) |
| 26 | Upload keystore created | USER | Task 12 Step 2 |
| 27 | Play Console account, identity verified | USER | Task 13 Step 1 ($25) |
| 28 | Store listing and Data safety entered | USER | Drafts: `docs/launch/store-listing.md`, `data-safety.md` |
| 29 | Closed testing started: date ____, 14-day end date ____ | USER | 12 or more testers opted in for 14 consecutive days |
| 30 | Phone OTP status | OFF | `PHONE_OTP_ENABLED=false` until Meta approves `smartnutri_otp` (Task 14). The CallMissed template body is unverified. |
| 31 | CallMissed plan and budget cap for launch | USER | Task 14 Step 4 |

## Rollback

```bash
CLOUDSDK_ACTIVE_CONFIG_NAME=smartnutri gcloud run revisions list --service smartnutri-api --region asia-south1
CLOUDSDK_ACTIVE_CONFIG_NAME=smartnutri gcloud run services update-traffic smartnutri-api --to-revisions <prev>=100 --region asia-south1
```

Use the same commands for `smartnutri-web`. A migration is never rolled back in place: ship a forward fix.

## Tag

Once every line is `DONE` (or explicitly waived by the user), tag locally with `git tag v1.0.0-beta.1`. **USER** approves pushing the branch and the tag, and the merge `v1-rebuild` → `main`.
