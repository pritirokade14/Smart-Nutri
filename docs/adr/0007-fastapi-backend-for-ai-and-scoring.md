# ADR 0007: Keep a FastAPI backend for AI orchestration and scoring

- **Status:** Accepted
- **Date:** 2026-11-02

## Context

With Supabase providing auth, database and storage (ADR 0003), we could put all logic in Supabase Edge Functions (Deno/TypeScript) and drop our own backend. However:
- The rules engine is the safety-critical core.
- Label extraction and voice need multi-step orchestration across the CallMissed and Open Food Facts APIs, with retries, schemas and cost logging.
- The team already works in Python, and the prototype backend is FastAPI.

## Decision

Keep a **FastAPI** service (`apps/api`) on Cloud Run in `asia-south1`, next to the Supabase Mumbai database.

- It owns:
  - the rules engine
  - the CallMissed and OFF integrations
  - all secrets
  - Alembic migrations
  - the public `/v1` API that the app calls with a Supabase JWT
- It runs Python 3.13 with Pydantic 2, SQLAlchemy 2 and `uv`.
- Supabase hooks (Send-SMS, later Send-Email) call back into FastAPI internal endpoints.
- Edge Functions are not used in v1.
- Code is organised by feature (`app/features/<feature>/{router,schemas,models,service}.py`), with shared `core/`, `db/`, `integrations/` and `prompts/`. The rules engine stays a standalone pure package in `app/scoring/`. Both the Android and web clients use this one API through generated clients (ADR 0010).

## Consequences

- The rules engine is pure Python with full pytest coverage. One language holds the safety logic, the evaluation harness and the AI orchestration.
- We operate one more service (container, deploys, scaling). Cloud Run scaling to zero keeps cost near zero at low traffic.
- There is an extra network hop compared with calling Supabase directly from the app. That is acceptable, because the app needs the API for every verdict anyway.
- Simple CRUD (for example members) could be served by Supabase directly with RLS. In v1 we route everything through the API for one consistent contract. We will revisit if latency matters.
