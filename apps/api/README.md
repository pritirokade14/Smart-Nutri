# SmartNutri API

FastAPI service with the SmartNutri rules engine, CallMissed AI and voice, the Open Food Facts lookup, and the database schema (Alembic). It serves both the Android app and the web app.

> Plans 1–9 are built and merged to `main`. In `.env`, quote JSON values and values with spaces: `uv --env-file` stops at the first bad line.

## Setup

Requirements: [uv](https://docs.astral.sh/uv/). uv installs Python 3.13 for you.

```bash
cd apps/api
uv python install 3.13
uv sync
uv run pytest -v
```

From the repo root, `just setup` and `just test-api` do the same.

## Configuration

Copy `.env.example` to `.env` and fill in:

- `CALLMISSED_API_KEY`: from the CallMissed console. Keep it secret, and never put it in either client.
- `SUPABASE_URL`, `SUPABASE_JWKS_URL`, `DATABASE_URL`: from the Supabase project (Mumbai region).
- `ALLOWED_ORIGINS`: the web app origin(s).
- `SENTRY_DSN`, `POSTHOG_API_KEY`: optional in development.

## The API contract

The OpenAPI schema is exported to `packages/api-contract/openapi.json`. The Dart (Android) and TypeScript (web) clients are generated from it. After changing a route or schema:

```bash
just contract   # export openapi.json and regenerate both clients
```

Commit the result in the same PR. CI fails if the committed contract is out of date.

## Layout and rules

See [AGENTS.md](AGENTS.md) for the feature-based layout, coding rules and commands. The key rule: **the rules engine (`app/scoring`) decides every verdict, and the LLM only explains it.**
