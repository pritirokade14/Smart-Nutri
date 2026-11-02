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
8. Create the production project, `smartnutri-prod` (Mumbai, **Pro plan**), only at launch (day 13–15).

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

Deploys run on GitHub Actions (ADR 0015) with keyless Workload Identity Federation: no service-account keys exist. Google trusts only this repository (by immutable id), the `main` branch, the `deploy-dev.yml` workflow file and `push` / `workflow_dispatch` events. The workflow runs the `api`, `web` and `security` workflows first and deploys only if they are all green. Each new revision is deployed with no traffic, smoke-tested on its own tag URL, and only then receives traffic.

**Because anyone who can change `deploy-dev.yml` on `main` can deploy, branch protection (Step 0) is required, not optional.**

**One-time steps, in order (you run them):**

0. **Protect `main` in GitHub (before anything else).**
   - Settings → Rules → Rulesets → New branch ruleset, target `main`, enforcement Active, **no bypass list**:
     - Require a pull request before merging, required approvals **0** (solo maintainer).
     - Require status checks to pass, using the job names `api / test`, `api / contract`, `app / test`, `web / test` and `security / secrets`.
     - Block force pushes. Restrict deletions.
   - Settings → Actions → General:
     - Workflow permissions: **Read repository contents and packages permissions** (read-only default).
     - Fork pull request workflows: **Require approval for all outside collaborators**.
   - `.github/CODEOWNERS` already covers `.github/workflows/**` and `scripts/**`.
   - Caveat: `api.yml`, `app.yml` and `web.yml` only run on pull requests that touch their paths. A required check that never runs blocks the PR, so if a docs-only PR gets stuck, drop the `paths` filter from that workflow's `pull_request` trigger.
1. `bash scripts/push-secrets.sh` : copies the three dev secrets from `apps/api/.env` into Secret Manager.
2. `bash scripts/setup-github-deploy.sh` (or `just setup-github-deploy`) : creates the service accounts, placeholder Cloud Run services with service-level roles, and the WIF pool and provider. Safe to re-run.
3. GitHub repo → Settings → Secrets and variables → Actions → **Variables** → New repository variable `NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY` (the **public** publishable key). Optional variables: `NEXT_PUBLIC_POSTHOG_KEY`, `NEXT_PUBLIC_SENTRY_DSN`, `SENTRY_DSN`.
4. `just db-migrate` with `apps/api/.env` pointing at the dev database (applies Alembic migrations; the URL is read by the app and never printed).
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
