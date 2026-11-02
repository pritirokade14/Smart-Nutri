# ADR 0013: Clients never use the Supabase Data API for app tables

- **Status:** Accepted
- **Date:** 2026-11-03

## Context

Supabase gives the `anon` and `authenticated` roles ALL privileges on every new table in `public` (default privileges), and exposes them through the Data API (PostgREST) to anyone holding the publishable key. Row-level security filters rows, but it does not cover `TRUNCATE`, `REFERENCES` or `TRIGGER`, and Alembic's own `alembic_version` table has no RLS at all. The baseline migration (ADR 0009) used to GRANT without revoking, so these defaults survived. A security review flagged this.

Our architecture already routes all app traffic through FastAPI (ADR 0007). Clients have no need to touch tables directly.

## Decision

Clients (Android and web) never use the Supabase Data API for app tables. All reads and writes go through FastAPI, which connects as a role with `BYPASSRLS` (Supabase `postgres` or `service_role`).

The baseline migration therefore:

- `REVOKE ALL` on every app table from `PUBLIC`, `anon` and `authenticated`.
- `GRANT SELECT` to `authenticated` only on `accounts`, `members`, `consents`, `scans`, `meal_logs`, `product_reports` and `products`. RLS still limits those reads to the caller's own rows (products are readable by all).
- Grants nothing to `authenticated` or `anon` on the server-only tables `off_product_cache`, `rate_limit_counters` and `explanation_cache`.
- Keeps `ALL` for `service_role`.
- Enables RLS on `alembic_version` and revokes everything on it from `PUBLIC`, `anon` and `authenticated`.
- Keeps all existing RLS policies as defence in depth in case a write grant is ever added.

Operational rules:

- The Supabase dashboard setting "Data API auto-expose" stays off.
- The API's database role must have `BYPASSRLS`.
- Because the API bypasses RLS, user isolation inside the API depends on `WHERE account_id = ctx.account_id` in every service. Every endpoint needs a foreign-account 404 test.

## Consequences

- A leaked publishable key cannot write, truncate or alter any table, and cannot read migration state.
- Tests emulate Supabase's default privileges before migrating and assert the exact privilege set per role (`tests/db/test_grants.py`).
- Isolation is now enforced by application code as well as RLS, so a missing `account_id` filter in the API is a real data leak. Review for it.
- Any future direct client read or write needs an explicit grant in a new migration and a new ADR.
