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

## What to send back (public values only)

| Value | From |
|---|---|
| Supabase Project URL and project ref | Step 2.4 |
| Google Cloud Project ID | Step 3.1 |
| Google Web OAuth Client ID | Step 3.4 |
| Chosen Android package name | Step 0 |
| "gcloud done" (I can then check it with `gcloud config list`) | Step 3.2 |

For secrets (CallMissed key, Supabase secret key, DB connection string, Google client secret), you'll paste them yourself into `apps/api/.env` and `apps/web/.env.local` when Plan 2 creates the templates. I never need to see them.
