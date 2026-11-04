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

## CallMissed AI setup (models, residency, fallbacks, probe)

Why these models: [ADR 0021](adr/0021-callmissed-model-choices.md). Sources: docs.callmissed.com (chat-completion, api-speed, gateway-controls, speech-to-text, text-to-speech, tts-voices, models, data-residency) and the public catalogue `GET https://api.callmissed.com/api/v1/models`, all read on 2026-11-04. **The catalogue is authoritative**: re-check `processing`, `deprecated` and prices there before changing a model.

### Models per job (defaults in `apps/api/app/core/config.py` and `.env.example`)

| Job | Primary | Fallback (tried once) | Request |
|---|---|---|---|
| Label extraction (vision) | `gemma-4-31b` | `glm-5.3-flash` | `POST /v1/chat/completions`, text part + base64 `image_url` part, `response_format` `json_schema` strict, `reasoning_effort: "none"` |
| Explanation and voice answer (text) | `gemma-4-31b` (thinking off with `"none"`) | `deepseek-v4.1-flash-1017` (thinking off with `"none"`) | Same, plus `provider: {"data_residency": "in"}`, 8 s budget |
| Speech-to-text | `saaras:v4` (`language` `en-IN` / `hi-IN` / `mr-IN`) | `whisper` (no `language`: auto-detect) | `POST /v1/audio/transcriptions`, multipart `file`, `model`, `language`; reply `{"text": ...}`; saaras at most 30 s of audio, 25 MB |
| Text-to-speech | `bulbul:v3`, voices en `ratan`, hi `shubh`, mr `ratan` | `gnani-timbre-v3.0`, voice `Chetana` (all three) | `POST /v1/audio/speech`, JSON `model`, `input`, `voice`, `language`, `response_format: "mp3"`; bulbul at most 2,500 characters |

- `sarvam-105b` is no longer the explanation model: it timed out at 8 s. `gemma-4-31b` is the default (ADR 0021).
- The label eval (`label-eval` skill) should compare the three non-deprecated India vision models: `gemma-4-31b`, `glm-5.3-flash`, `deepseek-v4.1-flash-1017`.
- `microsoft-neural-tts` is processed in India but is **voice-sessions only** (400 on `/v1/audio/speech`), so it cannot be the TTS fallback. Gnani Timbre v3 is (India, a different provider from Sarvam, Marathi supported).

### Residency (health data stays in India)

- Every default model has catalogue `processing: "india"`. Models marked `india_preferred` (for example `kimi-k2.5`, `gpt-6-sol`, `gpt-oss-120b`) may be processed outside India and are not used.
- The API refuses, before any request, a health-data call (explanation, voice answer, STT, TTS) whose primary or fallback model is not in `INDIA_PROCESSED_MODELS` (`apps/api/app/integrations/callmissed.py`). Label extraction is not health data, so the eval may try any model.
- Chat calls send `"provider": {"data_residency": "in"}`. The docs document that field for chat, messages, responses and embeddings only. **Also turn on "India-only processing" on each API key** (console, Developer → API keys): the docs say the key setting covers STT and TTS too, and a request can never switch it off.

### Fallbacks

- A primary 5xx, timeout or `400 region_unavailable` switches to the fallback **once**, inside the same deadline. With a fallback the primary may use 60% of the budget (4.8 s of the 8 s explanation budget), so the fallback always has time.
- 402 (credits), 401/403 and other 4xx never fall back. CallMissed's own `models` fallback list is not used: the docs say it never applies to requests with `response_format`.
- Empty `CALLMISSED_*_FALLBACK_MODEL` turns a fallback off.

### Plan and cost

- `gemma-4-31b`, `glm-5.3-flash`, `deepseek-v4.1-flash-1017`, `whisper` and `gnani-timbre-v3.0` are **paid-plan models** (Starter or higher). A Free key gets `403 model_not_available`, which the API treats as "AI unavailable". `saaras:v4`, `bulbul:v3` and `sarvam-105b` are free-tier.
- **`gpt-4o` is deprecated, sunset 2026-11-16, and is not used** (Ruling CM1). It is in `DEPRECATED_MODELS`, the allow-list refuses it, and a test fails if any default or fallback is deprecated. After the sunset it would be answered by `gpt-6-sol`, which is `india_preferred`.
- Prices (US$, US$1 = ₹96): `gemma-4-31b` 0.3646 in / 0.9375 out per 1M tokens; `glm-5.3-flash` 0.2292 / 0.7604; `deepseek-v4.1-flash-1017` 0.4271 / 1.771; `saaras:v4` 0.3125 per hour; `whisper` 0.4167 per hour; `bulbul:v3` 0.3125 per 10K characters; `gnani-timbre-v3.0` 0.2813 per 10K characters.
- Rough cost per call (estimates from those prices, not measured): explanation on `gemma-4-31b` about ₹0.1 (2,000 prompt and 300 answer tokens is about ₹0.1); label extraction on `gemma-4-31b` up to about ₹1; a 30 s voice question about ₹0.25 for STT plus about ₹0.9 for a 300-character spoken answer (TTS), plus the answer's LLM call.

### Probe (run once with a real key, then after any model change)

```bash
cd apps/api
uv run python -m scripts.probe_callmissed              # dry run: the 16 calls and the estimated cost
uv run python -m scripts.probe_callmissed --yes-spend  # spends; at most US$0.07 (about ₹7)
```

It calls each job's primary **and** fallback (chat, vision on a drawn synthetic label, TTS and STT in en, hi and mr) through the API's own client and prints only job, model, language, status and latency. Exit 0 means every call worked. Record the table in `docs/research/` before setting `VOICE_ENABLED=true`.

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
   - **Voice answers bucket: NO LONGER NEEDED (ADR 0020, 2026-11-04).** Voice answers are returned inline in the API response and no voice audio is ever stored, so there is no `voice-answers` bucket and no `SUPABASE_VOICE_BUCKET` setting. Do not create one on prod. **Dev has an unused `voice-answers` bucket that USER may delete** (Storage → `voice-answers` → Delete bucket).
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
- **Gotcha:** web sign-in uses the OAuth code flow, so Supabase must hold the secret of *this web client*. A mismatch shows "Unable to exchange external code" on `/auth/callback` (fixed on dev 2026-11-04 by adding a new secret; the old one may be deleted). Android uses native Google ID tokens and is not affected.

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
4. `just db-migrate` (dev head is `0007_plan9_supplement_category`) with `apps/api/.env` pointing at the dev database (applies Alembic migrations; the URL is read by the app and never printed).
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

`python -m app.jobs.retention` deletes label photos after 30 days, nulls `scans.image_path`, and purges deletion tombstones after 7 days. There is no voice step: voice audio is never stored (ADR 0020). It logs counts only. `deploy-dev.yml` deploys it on pushes to `main` only, using the same API image and the same runtime service account as the API (`smartnutri-api-dev`; it mounts only `DATABASE_URL` and `SUPABASE_SECRET_KEY` from Secret Manager). The workflow only updates an existing job; if the job does not exist it prints a warning and skips.

**You (USER) run these, in order:**

1. Make sure the `label-photos` bucket exists (section 2). No voice bucket is needed.
2. `bash scripts/setup-retention-schedule.sh setup`: creates the job shell `smartnutri-retention-dev`, gives `github-deployer` `run.developer` on that job only, and creates `smartnutri-scheduler-dev` with `run.invoker` on that job only.
3. Merge to `main` (or `just deploy-dev`) so the workflow deploys the real image and command into the job.
4. `bash scripts/setup-retention-schedule.sh dry-run`: executes the job with `--dry-run`. On a new project expect `photos_deleted=0 scans_nulled=0 tombstones_purged=0`.
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
