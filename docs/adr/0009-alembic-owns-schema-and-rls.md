# ADR 0009: Alembic owns the database schema, including RLS

- **Status:** Accepted
- **Date:** 2026-11-02

## Context

Postgres lives in Supabase, and two tools could change it: Alembic, in the FastAPI project, and Supabase CLI migrations, in `supabase/`. If both run, the schema drifts. Their histories conflict, and RLS policies get lost or duplicated.

## Decision

**Alembic in `apps/api/alembic/` is the only tool that changes the database schema.** That covers tables, indexes, enums, row-level security and policies (via `op.execute`), and storage bucket policies when needed.

`supabase/` holds only:
- `config.toml`
- auth provider settings (Google, email OTP, phone)
- auth hooks (Send-SMS → API → CallMissed WhatsApp OTP)
- email templates

Supabase CLI migrations are not used.

## Consequences

- There is one migration history, reviewable in PRs and testable in CI against a disposable Postgres.
- RLS policies are written as SQL inside Alembic revisions. The safety reviewer checks every revision that changes a policy.
- The local stack is the Supabase CLI for Auth and Storage, with Alembic run against its Postgres (`just db-migrate`).
- Supabase dashboard "table editor" changes are forbidden in shared environments.
