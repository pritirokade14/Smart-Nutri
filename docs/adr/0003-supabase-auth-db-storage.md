# ADR 0003: Supabase for auth, Postgres and storage

- **Status:** Accepted
- **Date:** 2026-11-02

## Context

v1 needs:
- Login: Google OAuth and email OTP or magic link now, and phone OTP later.
- A relational database: families → members → logs, products, consents.
- Private file storage for label photos.
- Data hosted in India, for DPDP readiness and latency.

The deadline is 15 days with a very small team. The options were:
- **Supabase**
- **Firebase:** Auth, Firestore and Storage
- **Self-managed:** Postgres, custom JWT auth and S3/R2

## Decision

Use **Supabase**, in the Mumbai region (`ap-south-1`).

- **Auth:**
  - Google OAuth and email OTP or magic link are built in.
  - Phone OTP is supported through the **Send-SMS hook**, which lets us deliver codes over a WhatsApp authentication template via CallMissed instead of India DLT SMS.
  - Supabase issues JWTs, which our FastAPI service verifies via JWKS.
- **Database:**
  - Real Postgres, so our data model stays relational and portable.
  - Row-level security gives defence in depth for family data.
  - Schema migrations stay in Alembic (owned by `apps/api`), so we are not locked in.
- **Storage:** private buckets with signed URLs, for label photos with 30-day retention.
- **Cost:** a free tier for development. Pro (about $25/month) covers about 100k MAU at launch.

## Consequences

- **Faster than self-managed.** We don't build auth, password reset, OTP or OAuth plumbing ourselves.
- **Better fit than Firebase.** Firestore's document model fits joins and reports (weekly totals per member, family views) poorly. Firebase phone auth also bills SMS per message and doesn't offer the WhatsApp route as easily.
- **Vendor dependency on Supabase Auth.** Mitigations:
  - Standard JWTs.
  - Postgres stays plain (Alembic migrations, no Supabase-only features in business logic).
  - The rest of the stack can move to any Postgres.
- **Two places touch the database.** The Supabase dashboard and Alembic migrations both reach it. The rule is that schema changes go only through Alembic, while RLS policies are versioned in `supabase/` or in migrations.
- **Production email.** It needs custom SMTP or a Send-Email hook, because the default mailer is rate-limited.
