# Supabase

Supabase provides **Auth, Postgres and Storage** for SmartNutri. The project lives in **Mumbai (ap-south-1)** so user data stays in India. The Android app (`supabase_flutter`) and the web app (`@supabase/ssr`) use the same project for sign-in.

> Most of this folder is **added in Plan 2 (auth and local setup) and the launch plan (production setup)**. This README describes what will live here.

## Ownership: what lives here and what doesn't

| Lives here (`supabase/`) | Lives in `apps/api/alembic/` |
|---|---|
| `config.toml`: local CLI config, auth providers, redirect URLs | **All tables** |
| Auth hooks (Send-SMS hook for WhatsApp OTP) | **All RLS policies** (`ENABLE ROW LEVEL SECURITY` + `CREATE POLICY` via `op.execute`) |
| Email templates (OTP, magic link; en, hi, mr) | Indexes, functions and triggers the app needs |
| Storage bucket config (`label-photos`, private) | |

**Never create or change tables or policies here or in the Supabase dashboard.** Alembic is the only schema owner, so local, dev and prod stay identical.

## Contents (planned)

| Path | Purpose |
|---|---|
| `config.toml` | Supabase CLI local config: auth providers and redirect URLs for the web origin and the Android deep link |
| `functions/send-sms-hook/` | **Send-SMS auth hook.** Delivers phone OTP through a CallMissed WhatsApp AUTHENTICATION template instead of SMS, which avoids DLT |
| `templates/` | Email OTP and magic-link templates (en, hi, mr) |
| `seed.sql` | Local development seed data only (no real users). It runs after Alembic migrations. |

## Setup (local)

The Supabase CLI is not installed on this machine yet:

```bash
brew install supabase/tap/supabase
supabase login
supabase start        # local stack (needs Docker)
just db-migrate       # Alembic creates tables + RLS in the local database
```

`just dev` runs `supabase start`, the API and the web app together.

## Auth providers

1. **Google OAuth** (v1):
   - Create OAuth credentials in Google Cloud Console: a **Web** client (used by Supabase and the Next.js web app), plus an **Android** client with the app's SHA-1.
   - In Supabase, go to Auth, then Providers, then Google, and paste the Web client ID and secret.
   - Redirect URLs:
     - The web app origins (`http://localhost:3000/**`, the prod domain).
     - The Android deep link (`com.smartnutri.nutrition_ai://login-callback`).
2. **Email OTP and magic link** (v1):
   - Enable the Email provider and use the 6-digit OTP template.
   - Configure custom SMTP, or a Send-Email hook via the CallMissed email API, before launch. Supabase's built-in mailer is rate-limited.
3. **Phone OTP** (code ready, **switched off**):
   - Enable it only after the WhatsApp OTP template is approved for our WhatsApp Business account.
   - Delivery goes through the Send-SMS hook to the CallMissed WhatsApp template API.
   - SMS via DLT is not planned. CallMissed SMS support was not found in its docs.

## Rules

- RLS is **on** for every table, with no exceptions. It is enforced by the Alembic migrations.
- The service-role key is used only by `apps/api` and server-side hooks. Never use it in the Android app or the web app, including Next.js server code.
- Storage bucket `label-photos` is private. Uploads use signed URLs, and objects are deleted after 30 days.
