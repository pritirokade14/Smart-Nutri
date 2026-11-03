# Account setup (do once, before day 4)

Goal: nothing blocks the first dev deploy (API + web on Cloud Run, Supabase dev, Android test build).

**Golden rule for secrets:** never paste secret keys into chat, Slack, GitHub or code. Keep them in a password manager. Locally they go in the git-ignored `apps/api/.env` and `apps/web/.env.local`. In the cloud they go in Google Secret Manager.

Values marked **public** are safe to share; values marked **SECRET** are not.

---

## 0. Decide the Android package name (permanent)

The Android ID can never change after the first Play Store upload. The prototype uses `com.smartnutri.nutrition_ai`. **Recommended: `com.smartnutri.app`.** Use the same value in steps 3.5 and 4.

---

## 1. CallMissed (AI + voice) · ~10 minutes

1. Sign in at **platform.callmissed.com**.
2. Create a workspace or project called **SmartNutri**.
3. Create **two API keys**, scoped to `llm`, `stt` and `tts` (add `whatsapp:send` and email scopes later, in Plan 4):
   - `smartnutri-dev`: **SECRET** (starts with `cm_`)
   - `smartnutri-prod`: **SECRET**. Create it now; use it only at launch.
4. Plan:
   - Stay on **Free** for development. Signup gives 1,000 credits.
   - Before launch, upgrade to **Starter (₹999/month)**.
5. Money savers:
   - Apply for the **startup programme ($1,000 credits)**.
   - If the company is DPIIT-recognised, claim **50% off**.
6. *(Plan 4, not now)* Connect a WhatsApp Business account and submit an **authentication (OTP) template** for phone login.

---

## 2. Supabase (login + database + photo storage) · ~15 minutes

1. Sign up at **supabase.com**. Using "Continue with GitHub" is easiest.
2. Create an organisation called **SmartNutri** (Free plan for now).
3. **New project:**
   - Name: `smartnutri-dev`
   - Region: **South Asia (Mumbai)**
   - Database password: generate a strong one and save it (**SECRET**)
4. Collect these values. Most are under **Project Settings → API / API Keys** and **Connect**:
   - **Project URL**, e.g. `https://abcd1234.supabase.co`: **public**
   - **Project ref** (the `abcd1234` part): **public**
   - **Publishable key** (`sb_publishable_…`): **public** (goes into the apps)
   - **Secret / service_role key**: **SECRET** (API only, never in the apps)
   - **Database connection string**, Session pooler, port 5432: **SECRET** (used by Alembic)
   - **JWKS URL**: `https://<project-ref>.supabase.co/auth/v1/.well-known/jwks.json`: **public**
5. **Authentication → URL Configuration:**
   - Site URL: `http://localhost:3000`
   - Redirect URLs: add `http://localhost:3000/**` and `com.smartnutri.app://login-callback`
6. **Authentication → Providers → Email:** enabled. Allow OTP / magic link.
7. **Authentication → Providers → Google:** enable it after step 3.5, and paste in the Google client ID and secret.
8. **Label photo storage** (Storage → New bucket):
   - Name: `label-photos`. Private (not public). File size limit: **8 MiB**. Allowed MIME types: `image/jpeg`, `image/png`, `image/webp`.
   - Add **no storage policies**. The API uses the secret key server-side to make signed upload URLs and to read the photo.
   - Dev: created in the dashboard on 2026-11-03.
   - Prod: create it the same way at launch (Plan 8).
   - Local: the bucket comes from `supabase/config.toml`.
   - Photos are deleted after 30 days by the retention job (see "Retention job" below).
   - **Voice answers bucket (Plan 7), REQUIRED before any deploy that could enable voice:** a second bucket, `voice-answers`. **Private** (not public). File size limit **5 MiB**. Allowed MIME type **`audio/mpeg`**. Add **no storage policies**: the API uploads `voice/{account_id}/{uuid}.mp3` with the secret key and hands out 1-hour signed URLs. The name comes from `SUPABASE_VOICE_BUCKET` (default `voice-answers`). Migrations do not create buckets. **USER: dev bucket not created yet; create it now. Prod: create it the same way at launch.** The retention job deletes answers after 24 hours; without the bucket the job and voice both fail.
9. Create the production project, `smartnutri-prod` (Mumbai, **Pro plan**), only at launch (day 13–15).

---

## 3. Google Cloud (hosting + secrets + Google login) · ~30 minutes

### 3.1 Project and billing
1. Go to **console.cloud.google.com** and create a project called **smartnutri**. Note the **Project ID** (**public**).
2. **Billing:** link a billing account (card). This is needed even to stay inside the free tier.
3. **Billing → Budgets & alerts:** create a budget of **₹1,000/month** with email alerts at 50%, 90% and 100%.

### 3.2 Command line (on the Mac; `gcloud` is already installed)

In Claude Code you can type these with a leading `!` so the output lands in our session:

```bash
gcloud auth login
gcloud config set project <PROJECT_ID>
gcloud config set run/region asia-south1
gcloud services enable run.googleapis.com artifactregistry.googleapis.com \
  cloudbuild.googleapis.com secretmanager.googleapis.com
gcloud artifacts repositories create smartnutri \
  --repository-format=docker --location=asia-south1
```

### 3.3 Google login: consent screen
**APIs & Services → OAuth consent screen** (also labelled **Google Auth Platform → Branding**):
- App name: **SmartNutri AI**. Add the user support email and developer contact email.
- Audience: **External**. Leave it in *Testing* for now and add your own Google account as a test user.
- Scopes: only `openid`, `email` and `profile`. These are non-sensitive, so no Google verification is needed.

### 3.4 OAuth client: Web (used by Supabase, for both apps)
**APIs & Services → Credentials → Create credentials → OAuth client ID → Web application:**
- Name: `smartnutri-web`
- Authorised JavaScript origins: `http://localhost:3000`
- Authorised redirect URI: `https://<project-ref>.supabase.co/auth/v1/callback`
- Copy the **Client ID** (**public**) and **Client secret** (**SECRET**) into **Supabase → Providers → Google**.

### 3.5 OAuth client: Android (native Google sign-in)
1. Get your debug SHA-1:
   ```bash
   keytool -list -v -keystore ~/.android/debug.keystore -alias androiddebugkey -storepass android -keypass android | grep SHA1
   ```
2. **Create OAuth client ID → Android:**
   - Package name: `com.smartnutri.app`
   - SHA-1: paste the value from step 1
3. In **Supabase → Providers → Google**, add this Android client ID next to the web client ID (comma-separated) under authorised client IDs.
4. Later, add the **release** and **Play App Signing** SHA-1s in the same way, when we upload to Play.

---

## 4. Google Play Console (personal account) · 15 minutes plus verification time

1. Go to **play.google.com/console** and sign up as a **Personal** account. Pay **$25** (one-time).
2. Complete **identity verification** (government ID). This can take a few days, so start now.
3. Complete any **device verification** Play asks for (via the Play Console app on an Android phone).
4. Don't create the app listing yet. We'll do that with the first closed-testing build (day 15).
5. Reminder: personal accounts need a **closed test with 12+ testers for 14 consecutive days** before public release. The clock starts when testers join.

---

## 5. Can wait until Plan 2 or M6

- **Sentry** (errors) and **PostHog** (analytics): free accounts, created in Plan 2.
- **Domain** (e.g. smartnutri.in): before the production web launch.
- **Privacy policy and terms URLs:** before the Play closed test.

---

## Dev deploy (GitHub Actions + WIF)

Deploys run on GitHub Actions (ADR 0015) with keyless Workload Identity Federation: no service-account keys exist. Google trusts only this repository (by immutable id), the `main` branch, the `deploy-dev.yml` workflow file and `push` / `workflow_dispatch` events. The workflow runs the `api`, `web`, `packages` and `security` workflows first and deploys only if they are all green. Each new revision is deployed with no traffic, smoke-tested on its own tag URL, and only then receives traffic.

**Because anyone who can change `deploy-dev.yml` on `main` can deploy, branch protection (Step 0) is required, not optional.**

**One-time steps, in order (you run them):**

0. **Protect `main` in GitHub (before anything else).**
   - Settings → Rules → Rulesets → New branch ruleset, target `main`, enforcement Active, **no bypass list**:
     - Require a pull request before merging, required approvals **0** (solo maintainer).
     - Require status checks to pass, using the job names `api / test`, `api / contract`, `app / test`, `web / test`, `packages / test` and `security / secrets`.
     - Block force pushes. Restrict deletions.
   - Settings → Actions → General:
     - Workflow permissions: **Read repository contents and packages permissions** (read-only default).
     - Fork pull request workflows: **Require approval for all outside collaborators**.
   - `.github/CODEOWNERS` already covers `.github/workflows/**` and `scripts/**`.
   - Note: the `pull_request` triggers of `api.yml`, `app.yml`, `web.yml`, `packages.yml` and `security.yml` have no `paths` filter (R35), so every required check always runs on PRs to `main`. Only `push` runs are path-filtered. Do not add a `paths` filter to a `pull_request` trigger: a required check that never runs blocks the PR.
1. `bash scripts/push-secrets.sh dev`: copies the dev secrets from `apps/api/.env` into Secret Manager.
   - Secrets are named `<var-lowercase-dashes>-dev`.
   - Empty variables are skipped.
   - `prod` reads `apps/api/.env.production`.
   - `--dry-run` prints the names only.
2. `bash scripts/setup-github-deploy.sh` (or `just setup-github-deploy`) : creates the service accounts, placeholder Cloud Run services with service-level roles, and the WIF pool and provider. Safe to re-run.
3. GitHub repo → Settings → Secrets and variables → Actions → **Variables** → New repository variable `NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY` (the **public** publishable key). Optional variables: `NEXT_PUBLIC_POSTHOG_KEY`, `NEXT_PUBLIC_SENTRY_DSN`, `SENTRY_DSN`.
4. `just db-migrate` (head is now `0004_plan8_deleted_accounts`; migrations 0003 and 0004 must be applied to dev before Plans 5–8 reach `main`) with `apps/api/.env` pointing at the dev database (applies Alembic migrations; the URL is read by the app and never printed).
5. Merge to `main` through a pull request when CI is green. The deploy runs on its own. To redeploy without a code change: `just deploy-dev` (= `gh workflow run deploy-dev.yml --ref main`).

**Dev URLs (deterministic):**

| Service | URL |
|---|---|
| API | https://smartnutri-api-dev-609833507754.asia-south1.run.app |
| Web | https://smartnutri-web-dev-609833507754.asia-south1.run.app |

**After the first deploy:**

- Supabase → Auth → URL Configuration: add `https://smartnutri-web-dev-609833507754.asia-south1.run.app/**` to Redirect URLs.
- Google Cloud → OAuth web client: add `https://smartnutri-web-dev-609833507754.asia-south1.run.app` to Authorised JavaScript origins.
- Supabase → Auth → Email Templates: paste `supabase/templates/magic_link.html` so the email carries the OTP code.
- **Verify `TRUSTED_PROXY_HOPS=1`** (set for a direct `*.run.app` URL) once an endpoint that is rate-limited by IP (a public-bucket endpoint) exists:
  1. Call it from a machine with a known egress IP, with `-H 'X-Forwarded-For: 203.0.113.9'`.
  2. Inspect the new key in `rate_limit_counters`.
  3. Your own egress IP: correct. `203.0.113.9`: the header is spoofable, lower the hops. A Google or `169.254.*` address: everyone shares one bucket, raise the hops.

## Retention job (Cloud Run Job + Cloud Scheduler)

`python -m app.jobs.retention` deletes label photos after 30 days and voice answers after 24 hours, nulls `scans.image_path`, and purges deletion tombstones after 7 days. It logs counts only. `deploy-dev.yml` deploys it on pushes to `main` only, using the same API image and the same runtime service account as the API (`smartnutri-api-dev`; it mounts only `DATABASE_URL` and `SUPABASE_SECRET_KEY` from Secret Manager). The workflow only updates an existing job; if the job does not exist it prints a warning and skips.

**You (USER) run these, in order:**

1. Create the `voice-answers` bucket (section 2, step 8).
2. `bash scripts/setup-retention-schedule.sh setup`: creates the job shell `smartnutri-retention-dev`, gives `github-deployer` `run.developer` on that job only, and creates `smartnutri-scheduler-dev` with `run.invoker` on that job only.
3. Merge to `main` (or `just deploy-dev`) so the workflow deploys the real image and command into the job.
4. `bash scripts/setup-retention-schedule.sh dry-run`: executes the job with `--dry-run`. On a new project expect `photos_deleted=0 voice_deleted=0 scans_nulled=0`.
5. `bash scripts/setup-retention-schedule.sh schedule`: creates the Cloud Scheduler trigger `smartnutri-retention-dev-daily` at **02:30 Asia/Kolkata** every day.

Prod: repeat with prod names when the prod project exists (a prod job, prod secrets, a prod scheduler).

## Email sign-in codes (Google Workspace SMTP — after the domain)

Email sign-in is hidden (`NEXT_PUBLIC_FEATURE_EMAIL_OTP=false` on web, `FEATURE_EMAIL_OTP=false` on Android) because the built-in Supabase email sender cannot send the 6-digit code the app expects: editing the template needs custom SMTP. Until then the built-in sender only delivers to Supabase project team members and sends links, not codes. Use Google or phone sign-in meanwhile.

Once you own a domain:

1. Buy the domain.
2. Create Google Workspace Business Starter with a `no-reply@<domain>` user (or an alias on an existing user).
3. Turn on 2-Step Verification for that user, then create an App Password for it.
4. Supabase → Authentication → Emails → SMTP Settings → Set up SMTP:
   - Host `smtp.gmail.com`, port `465`.
   - Username: the Workspace address. Password: the App Password.
   - Sender email `no-reply@<domain>`, sender name `SmartNutri`.
5. Supabase → Authentication → Emails → Templates → "Magic link or OTP": paste `supabase/templates/magic_link.html` and set the subject to `Your SmartNutri sign-in code`.
6. GitHub repo → Settings → Secrets and variables → Actions → Variables: set `NEXT_PUBLIC_FEATURE_EMAIL_OTP=true`. For Android, build with `FEATURE_EMAIL_OTP=true`.
7. Redeploy (`just deploy-dev`) and ship a new Android build.

Note: Google Workspace limits sending to about 2,000 emails per day per user. That is fine for launch; move to a transactional provider (for example Resend or SES) if sign-in volume grows.

## Schema changes: migrate, then merge

Each API build knows the Alembic head it was built with. `GET /v1/health` returns `503 {"status": "unavailable", "database": "schema_behind"}` until the database's `alembic_version` equals that head, so a new revision is never smoke-tested green, or given traffic, against an old schema.

For a PR that adds a migration:

1. Run `just db-migrate` against the dev database from the PR branch, before merging. Migrations must be backward-compatible with the API revision that is still serving (add columns and tables; drop or rename only in a later PR).
2. Then merge. The deploy's smoke test on `/v1/health` now passes.

The database role the API connects with needs `SELECT` on `public.alembic_version` (the dev `postgres` role has it). Keep that grant when the dedicated production role is created.

---

## What to send back (public values only)

| Value | From |
|---|---|
| Supabase Project URL and project ref | Step 2.4 |
| Google Cloud Project ID | Step 3.1 |
| Google Web OAuth Client ID | Step 3.4 |
| Chosen Android package name | Step 0 |
| "gcloud done" (I can then check it with `gcloud config list`) | Step 3.2 |

For secrets (CallMissed key, Supabase secret key, DB connection string, Google client secret), you'll paste them yourself into `apps/api/.env` and `apps/web/.env.local` when Plan 2 creates the templates. I never need to see them.
