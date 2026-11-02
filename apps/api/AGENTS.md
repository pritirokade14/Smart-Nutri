# apps/api: agent guide

This is the FastAPI service for SmartNutri AI. It holds the **rules engine** (`app/scoring`), the CallMissed AI and voice integration, the Open Food Facts lookup, **all database tables and RLS policies (Alembic)**, and the REST API used by **both** the Android app (`apps/app`) and the web app (`apps/web`). Root rules in `../../AGENTS.md` apply first.

> **Current state:** the files here (`main.py`, `ai/`, `api/`, `database/`, `services/`, `requirements.txt`) are the **old prototype**. Plan 1 Task 1 deletes them and creates the `uv` project. Do not extend the prototype.

## Stack

- Python 3.13 · `uv` · FastAPI · Pydantic 2 + pydantic-settings
- SQLAlchemy 2 (async, psycopg 3) · Alembic
- PyYAML · `openai` SDK (pointed at CallMissed) · httpx
- pytest · ruff · Sentry · PostHog (optional server events, no health data)
- Deployed as a container on Cloud Run (asia-south1). Database and storage are Supabase (ap-south-1).

## Target layout (feature-based)

```
apps/api/
  pyproject.toml  uv.lock  Dockerfile  alembic.ini
  alembic/versions/            # ALL tables AND RLS policies (op.execute), nothing in supabase/
  app/
    main.py                    # app factory, routers, CORS allow-list, error handlers, rate limiter
    core/                      # config.py (settings), security.py (Supabase JWT), logging.py, errors.py, ratelimit.py
    db/                        # session.py, base.py
    features/
      me/ members/ consents/ products/ scans/ analyze/ meals/ voice/ reports/ methodology/
        └─ each: router.py  schemas.py  models.py  service.py
    scoring/                   # pure rules engine (Plan 1)
      data/*.yaml              # thresholds, allergens, diet, ingredient lists
    integrations/              # callmissed.py, openfoodfacts.py, storage.py, posthog.py
    prompts/                   # extraction_v1.md, explanation_v1.md, voice_v1.md (versioned, never edited in place)
  scripts/export_openapi.py    # writes packages/api-contract/openapi.json (used by `just contract`)
  tests/
    unit/                      # pure logic incl. unit/scoring
    api/                       # endpoint tests (httpx + test DB)
    fixtures/                  # loads ../../packages/test-fixtures
    evals/labels/              # extraction eval set (images git-ignored)
```

A feature folder owns its route, schemas, SQLAlchemy models and service. Cross-feature calls go through the other feature's `service.py`, never its router or models.

## Rules for this app

- **`app/scoring` is pure.** No I/O apart from loading its bundled YAML, no network, no database, no LLM. Its public API is `analyze(product, members) -> AnalysisResult`.
- **Verdicts come only from `analyze()`.** LLM text explains the result and never alters it. Clients never recompute verdicts.
- **Thresholds and terms live in `scoring/data/*.yaml`.** Use the `scoring-rule` skill to change them, and update `packages/test-fixtures` expectations in the same PR.
- **Alembic owns the schema, including RLS.**
  - Every new table gets `ENABLE ROW LEVEL SECURITY` plus its policies in the same migration, via `op.execute(...)`.
  - Never create tables or policies through the Supabase dashboard or in `supabase/`.
- **Contract first.**
  - The OpenAPI schema is the contract for both clients. After any change to a route or schema, run `just contract` and commit `packages/api-contract/` in the same PR.
  - Keep `operationId`s stable and explicit (`<feature>_<action>`), because the generated client method names come from them.
- **CallMissed calls go only through `integrations/callmissed.py`,** behind the `LLMProvider` and `SpeechProvider` protocols. Use the `callmissed` skill.
- **Prompts** are Markdown files in `app/prompts/` named `<name>_v<N>.md`. Each LLM call logs the prompt version.
- **Endpoints:**
  - Auth on everything except `/v1/health`, `/v1/methodology` and public product info (`GET /v1/products/{barcode}/public`, which returns generic data only, no verdicts).
  - Every query is scoped by `account_id`.
  - No exception text in responses.
  - Use the `api-endpoint` skill.
- **Rate limits and caching:**
  - Each account has limits on expensive routes, for example 30 label scans a day and a daily cap on voice questions.
  - Over the limit, return `429` with `{"error": {"code": "rate_limited_scans"}}`.
  - Cache label extractions by image SHA-256, and products by barcode (`products` and `off_product_cache`). A repeated input must never trigger a second paid CallMissed call.
- **Never** create mock or fallback nutrition values, or estimate missing macros. Missing data is `None`.
- **Async all the way.** Blocking calls go through `anyio.to_thread` or a worker.

## Environment variables

| Name | Purpose |
|---|---|
| `CALLMISSED_API_KEY` | CallMissed `cm_...` key (server only) |
| `SUPABASE_URL` | Supabase project URL |
| `SUPABASE_JWKS_URL` | JWKS used to verify user JWTs |
| `DATABASE_URL` | Postgres connection (`postgresql+psycopg://...`) |
| `SENTRY_DSN` | Error reporting (optional in dev) |
| `ALLOWED_ORIGINS` | Comma-separated CORS origins (the web app origins) |
| `POSTHOG_API_KEY` | Optional server-side analytics (no health data) |

Model ids (`MODEL_EXTRACTION`, `MODEL_EXPLANATION`, `MODEL_STT`, `MODEL_TTS`), rate-limit values and the storage bucket name are added in Plan 2. Keep `.env.example` in sync. Never commit `.env`.

## Commands

From the repo root: `just api`, `just test-api`, `just contract`, `just db-migrate`, `just db-revision "<message>"`.

From `apps/api`:

| What | Command |
|---|---|
| Install | `uv sync` |
| All tests | `uv run pytest -v` |
| Scoring tests only | `uv run pytest tests/unit/scoring -v` |
| DB, migration and RLS tests | `uv run pytest tests/db -v` |
| Lint | `uv run ruff check app tests` |
| Format | `uv run ruff format app tests` |
| Apply migrations (`just db-migrate`) | `uv run alembic upgrade head` |
| New migration (`just db-revision "add x"`) | `uv run alembic revision --autogenerate -m "add x"` |
| Current revision | `uv run alembic current` |

**Database tests** (`tests/db`) run against `TEST_DATABASE_URL` when it is set (CI's `postgres:17` service). Otherwise they start a throwaway `postgres:17` Docker container for the session and remove it afterwards. They skip with a reason when neither is available. They drop every table, so they refuse a Supabase-hosted URL.

**Migrations:** Alembic reads `DATABASE_URL`. Autogenerate does not emit RLS. Every new table needs `ENABLE` + `FORCE ROW LEVEL SECURITY` and its `TO authenticated` policies added by hand with `op.execute(...)`, plus a case in `tests/db/test_rls.py`.

Commands for running the server and Docker are added by later Plan 2 tasks. Don't invent them before then.

## Conventions

- Type hints everywhere. Frozen dataclasses in `scoring`, Pydantic at the API boundary.
- Snake_case JSON on the wire. The generated Dart and TypeScript clients use these names.
- Commits use the `scoring`, `api` or `contract` scope: `feat(scoring): ...`, `fix(api): ...`, `chore(contract): regenerate clients`.
