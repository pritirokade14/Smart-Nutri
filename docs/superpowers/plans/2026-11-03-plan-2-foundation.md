# Plan 2: Foundation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Everything the feature slices (M1–M6) build on, with no product features yet:
- the API skeleton (config, errors, auth, database, migrations with RLS, rate limits, `/v1/health`, `/v1/me`)
- the contract, i18n, tokens and fixtures packages
- the Flutter Android shell with login
- the Next.js web shell with login
- observability, CI, Docker images
- a working **dev deploy** of the API and web app to Cloud Run Mumbai

**Architecture:**
- Feature-based FastAPI app (`app/features/<f>/{router,schemas,models,service}.py`) on async SQLAlchemy 2 with psycopg 3. Alembic owns every table and RLS policy (ADR 0009).
- Supabase access tokens are verified against the project JWKS.
- `openapi.json` is exported from the app and turned into the Dart (`smartnutri_api`) and TypeScript (`@smartnutri/api-client`) clients (ADR 0010).
- Both clients are thin. Login goes through Supabase. Every API call uses the generated client with the session's bearer token.

**Tech Stack:**
- **API:** Python 3.13, uv, FastAPI, pydantic-settings, SQLAlchemy 2 (async) + psycopg 3, Alembic, PyJWT[crypto], httpx, sentry-sdk.
- **Android:** Flutter (latest stable), Riverpod 3, go_router, dio, supabase_flutter 2.18.3, google_sign_in, sentry_flutter, posthog_flutter, swagger_parser 1.45.1.
- **Web:** Next.js 16.4.4, React 19.3, Tailwind 4.3, shadcn 4.23, next-intl 4.14, `@supabase/ssr` 0.12.7, TanStack Query 5.105, openapi-fetch 0.17, Biome 2.6, Vitest 5.1, Playwright 1.64, `@sentry/nextjs` 11.10, posthog-js 1.444.
- **Shared:** style-dictionary 5.7, openapi-typescript 7.13.
- **Infra:** Docker, Cloud Run (asia-south1), Artifact Registry, Secret Manager.

**Spec:** `docs/superpowers/specs/2026-11-02-smartnutri-v1-design.md` (§2 F1, §3, §4, §5, §7, §8 Plan 2). Also `docs/ARCHITECTURE.md` and ADRs 0008–0012.

**Depends on:** Plan 1 (rules engine) merged. Task 10 imports `app.scoring.analyze`.

## Global Constraints

- **Naming contract (other plans depend on it; use these exact names):**
  - `app.main:create_app()`
  - `app.core.config.Settings` + `get_settings()`
  - `app.core.security.current_account` → `AccountContext(account_id: UUID, email: str | None)`
  - `app.db.session.get_session` → `AsyncSession`
  - ORM models in `app/features/<f>/models.py` on `app.db.base.Base`
  - Routers at `app/features/<f>/router.py`, mounted at `/v1/<f>`
  - `operation_id = "<feature>_<action>"`
  - `app.core.errors.ApiError(code, status, message_key)`
  - `app.core.ratelimit.limit(bucket: str)`
  - Providers: `app.integrations.providers.LLMProvider` / `SpeechProvider`, `app.integrations.callmissed.CallMissedClient`, `app.integrations.openfoodfacts.OffClient`, `app.integrations.storage.StorageClient`
  - Prompts: `app/prompts/<name>_v<N>.md`
- **Error envelope, always:** `{"error": {"code": str, "message_key": str, "details": dict}}`. Never include exception text. `message_key` is an i18n key (`error.<code>`).
- **Env var names** are exactly those in `apps/api/.env.example`, `apps/web/.env.example` and `apps/app/env/example.json`. Publishable keys are `SUPABASE_PUBLISHABLE_KEY` and `NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY`.
  - New keys added by this plan: `RATE_LIMIT_PUBLIC_PER_MINUTE` (API, default 60), `NEXT_PUBLIC_FEATURE_PHONE_OTP` (web, default `false`), `FEATURE_PHONE_OTP` (Android, default `false`).
- **Secrets:**
  - Never read, print or commit real env files.
  - Claude agents **never write to Secret Manager**. `scripts/push-secrets.sh` is written by the agent and **run by the user**.
- **gcloud:** prefix every command with `CLOUDSDK_ACTIVE_CONFIG_NAME=smartnutri`.
  - Project `smartnutri-513518`, region `asia-south1`.
  - Registry `asia-south1-docker.pkg.dev/smartnutri-513518/smartnutri`.
  - Never change the default gcloud configuration.
- **Android ID:** `com.smartnutri.app`, for both `applicationId` and `namespace`. The OAuth redirect is `com.smartnutri.app://login-callback`, already registered in Supabase. The pubspec name stays `smartnutri_ai`.
- **Generated code is committed and never hand-edited:** `packages/api-contract/{openapi.json,dart,ts}`, `apps/app/lib/core/l10n/*.arb`, and the token outputs.
- **No product features in this plan.** Feature routers other than `health` and `me` get created in M1–M6.
- **Login methods:** Google and email OTP are on. Phone OTP is built and off by default on both clients.
- **Commands:** use `just` recipes from the repo root. Commit scopes are `api`, `app`, `web`, `contract`, `i18n`, `tokens`, `fixtures`, `ci` and `supabase`.

## Review Focus

1. **A forged, expired or wrong-audience JWT, or a rotated key** (a `kid` that isn't cached) → `401 auth_invalid`. The JWKS is re-fetched once for an unknown `kid`. Owned by Task 3.
2. **Account B reading account A's rows.** RLS policies must block it, and `meal_logs` is scoped through `members`. Owned by Task 4.
3. **An unhandled exception** → `500` with code `internal_error` and no exception text, including on validation errors (`422 validation_error`). Owned by Task 1.
4. **A Hindi or Marathi file missing a key, or with a different ICU placeholder** → `just i18n` check fails. Owned by Task 8.
5. **A web `(app)` route without a session** → redirect to `/<locale>/sign-in`. Public routes never require a session, and the CSP header is present on every response. Owned by Task 14.

## Execution waves (for parallel execution)

`[T1] → [T2 ∥ T8 ∥ T9] → [T3 ∥ T4 ∥ T10] → [T5 ∥ T6 ∥ T11] → [T7 ∥ T12 ∥ T13] → [T14] → [T15] → [T16] → [T17]`

Within a wave, tasks touch disjoint files. T15 touches all three apps, so it runs alone.

## File Map

```
apps/api/
  pyproject.toml (deps)  Dockerfile  .dockerignore  alembic.ini
  alembic/env.py  alembic/versions/0001_baseline.py
  app/main.py  app/core/{config,logging,errors,security,ratelimit,observability}.py
  app/db/{base,session}.py
  app/features/health/router.py
  app/features/me/{router,schemas,models,service}.py
  app/features/{members,consents,products,scans,meals,reports}/models.py
  app/features/ratelimit/models.py            # rate_limit_counters, explanation_cache
  scripts/export_openapi.py
  tests/conftest.py  tests/api/*  tests/db/*  tests/fixtures/{loader.py,test_shared_fixtures.py}
packages/api-contract/{dart/{pubspec.yaml,swagger_parser.yaml,lib/},ts/{package.json,src/index.ts,src/schema.d.ts}}
packages/i18n/{package.json,messages/{en,hi,mr}.json,scripts/{build-arb.mjs,check-keys.mjs,*.test.mjs}}
packages/design-tokens/{package.json,tokens.json,style-dictionary.config.mjs,scripts/*.test.mjs,build/}
packages/test-fixtures/{products,members,expected}/*.json  README.md
apps/app/  pubspec.yaml  l10n.yaml  android/app/{build.gradle.kts,src/main/AndroidManifest.xml,src/main/kotlin/com/smartnutri/app/MainActivity.kt}
           lib/{main,app,bootstrap}.dart  lib/core/{config,network,router,theme,l10n}/  lib/features/{auth,home}/
           test/**  env/example.json
apps/web/  (create-next-app) package.json next.config.ts biome.json vitest.config.ts playwright.config.ts Dockerfile
           src/{proxy.ts,i18n/*,lib/{supabase,api}/*,app/[locale]/{layout.tsx,(public)/{page,sign-in/page}.tsx,(app)/home/page.tsx},app/auth/callback/route.ts}
           tests/*  e2e/*  .env.example
supabase/config.toml
scripts/push-secrets.sh  justfile  .github/workflows/{api,app,web}.yml
```

---

### Task 1: API config, logging, error envelope and app factory

**Files:**
- Modify: `apps/api/pyproject.toml`
- Create:
  - `apps/api/app/main.py`
  - `apps/api/app/core/{__init__,config,logging,errors}.py`
  - `apps/api/app/features/__init__.py`
  - `apps/api/tests/conftest.py`
  - `apps/api/tests/api/{__init__,test_errors,test_config}.py`
- Modify: `apps/api/.env.example` (add `RATE_LIMIT_PUBLIC_PER_MINUTE=60`)

**Interfaces:** Produces:

```python
# core/config.py  (pydantic-settings, env_file=".env", extra="ignore")
class Settings(BaseSettings):
    environment: Literal["dev", "staging", "prod", "test"] = "dev"
    callmissed_api_key: SecretStr | None = None
    callmissed_base_url: str = "https://api.callmissed.com/v1"
    callmissed_resource_url: str = "https://api.callmissed.com/api/v1"
    callmissed_extraction_model: str = "kimi-k2.5"
    callmissed_explanation_model: str = "sarvam-105b"
    callmissed_stt_model: str = "saaras:v4"
    callmissed_tts_model: str = "bulbul:v3"
    supabase_url: str = ""
    supabase_project_ref: str = ""
    supabase_jwks_url: str = ""
    supabase_secret_key: SecretStr | None = None
    supabase_storage_bucket: str = "label-photos"
    database_url: SecretStr = SecretStr("postgresql+psycopg://postgres:postgres@127.0.0.1:54322/postgres")
    allowed_origins: list[str] = ["http://localhost:3000"]   # env: comma-separated string
    off_user_agent: str = "SmartNutri/0.1"
    rate_limit_label_scans_per_day: int = 30
    rate_limit_voice_per_day: int = 20
    rate_limit_analyze_per_hour: int = 120
    rate_limit_public_per_minute: int = 60
    sentry_dsn: str | None = None
    posthog_api_key: str | None = None
def get_settings() -> Settings          # functools.cache

# core/errors.py
class ApiError(Exception):
    def __init__(self, code: str, status: int, message_key: str | None = None, details: dict | None = None) -> None
        # message_key defaults to f"error.{code}"
def install_error_handlers(app: FastAPI) -> None
    # ApiError → its status; RequestValidationError → 422 code "validation_error",
    #   details={"fields": [loc strings]}; HTTPException 404 → "not_found";
    #   any other Exception → 500 "internal_error" (logged with traceback, never returned)

# core/logging.py
def configure_logging(environment: str) -> None   # JSON lines on stdout; level INFO (DEBUG in dev)

# main.py
def create_app(settings: Settings | None = None) -> FastAPI
    # title "SmartNutri API", version from package metadata, CORS allow-list from settings,
    # error handlers, includes feature routers listed in ROUTERS (empty list here; Task 2 adds health)
```

- [ ] **Step 1: Add dependencies.**
  - Runtime: `fastapi[standard]>=0.120`, `pydantic-settings>=2.6`, `sqlalchemy[asyncio]>=2.0.40`, `psycopg[binary]>=3.2`, `alembic>=1.14`, `pyjwt[crypto]>=2.10`, `httpx>=0.28`, `sentry-sdk>=2.20`.
  - Dev: `pytest-asyncio>=0.25`.
  - Then run `cd apps/api && uv add ... && uv sync`.
  - Expected: `uv.lock` updated, and the Plan 1 tests still pass (`uv run pytest -q`).
- [ ] **Step 2: Write failing tests**

```python
# tests/conftest.py
@pytest.fixture
def app():
    return create_app(Settings(environment="test", allowed_origins=["http://localhost:3000"]))
@pytest.fixture
async def client(app):
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://t") as c:
        yield c

# tests/api/test_errors.py — the test adds throwaway routes to the app instance
async def test_api_error_envelope(app, client):
    @app.get("/boom-api")
    async def _(): raise ApiError("not_found", 404)
    r = await client.get("/boom-api")
    assert r.status_code == 404
    assert r.json() == {"error": {"code": "not_found", "message_key": "error.not_found", "details": {}}}

async def test_unhandled_exception_hides_text(app):
    @app.get("/boom")
    async def _(): raise RuntimeError("secret db password in message")
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app, raise_app_exceptions=False), base_url="http://t") as c:
        r = await c.get("/boom")
    assert r.status_code == 500 and r.json()["error"]["code"] == "internal_error"
    assert "secret" not in r.text

async def test_validation_error_envelope(app, client):
    @app.get("/v")
    async def _(n: int): return {}
    r = await client.get("/v?n=abc")
    assert r.status_code == 422 and r.json()["error"]["code"] == "validation_error"
    assert r.json()["error"]["details"]["fields"] == ["query.n"]

async def test_cors_allow_list(client):
    r = await client.options("/anything", headers={"Origin": "https://evil.example", "Access-Control-Request-Method": "GET"})
    assert "access-control-allow-origin" not in r.headers

# tests/api/test_config.py
def test_allowed_origins_from_comma_string(monkeypatch):
    monkeypatch.setenv("ALLOWED_ORIGINS", "http://localhost:3000,https://smartnutri.in")
    assert Settings(_env_file=None).allowed_origins == ["http://localhost:3000", "https://smartnutri.in"]
```

Add `[tool.pytest.ini_options] asyncio_mode = "auto"` to `pyproject.toml`.

- [ ] **Step 3: Run them to verify they fail.** Run `cd apps/api && uv run pytest tests/api -v`. Expected: FAIL (`ModuleNotFoundError: app.main`).
- [ ] **Step 4: Implement** to the Interfaces block. Parse `allowed_origins` with a `field_validator(mode="before")` that splits a comma string.
- [ ] **Step 5: Run the tests to verify they pass.** Run `uv run pytest -q && uv run ruff check app tests`. Expected: all pass.
- [ ] **Step 6: Commit** with message `feat(api): settings, JSON logging, error envelope and app factory`.

---

### Task 2: Database session and `/v1/health`

**Files:**
- Create:
  - `apps/api/app/db/{__init__,base,session}.py`
  - `apps/api/app/features/health/{__init__,router}.py`
  - `apps/api/tests/api/test_health.py`
- Modify: `apps/api/app/main.py` (register the health router), the `justfile` (the `api` recipe)

**Interfaces:**
- Consumes: Task 1.
- Produces:

```python
# db/base.py
class Base(DeclarativeBase): metadata = MetaData(naming_convention={...standard ix/uq/ck/fk/pk...})
# db/session.py
def get_engine() -> AsyncEngine                      # cached; from settings.database_url; pool_pre_ping=True
async def get_session() -> AsyncIterator[AsyncSession]   # FastAPI dependency
# features/health/router.py
router = APIRouter(prefix="/v1/health", tags=["health"])
GET ""  operation_id="health_get"  → 200 {"status": "ok", "database": "ok"}
                                   → 503 {"status": "degraded", "database": "error"}  (when SELECT 1 fails)
```

`/v1/health` is public. Its response bodies are exact, and the 503 body is **not** wrapped in the error envelope, because it is a status report.

- [ ] **Step 1: Write failing tests** (override `get_session` with fakes)

```python
async def test_health_ok(app, client):
    class S:
        async def execute(self, _): return None
    app.dependency_overrides[get_session] = lambda: S()
    r = await client.get("/v1/health")
    assert (r.status_code, r.json()) == (200, {"status": "ok", "database": "ok"})

async def test_health_db_down(app, client):
    class S:
        async def execute(self, _): raise OSError("down")
    app.dependency_overrides[get_session] = lambda: S()
    r = await client.get("/v1/health")
    assert (r.status_code, r.json()) == (503, {"status": "degraded", "database": "error"})
```

- [ ] **Step 2: Run them to verify they fail.** Run `uv run pytest tests/api/test_health.py -v`. Expected: FAIL (404).
- [ ] **Step 3: Implement** to the Interfaces block.
- [ ] **Step 4: Run the tests to verify they pass.** Then change the `justfile` `api` recipe to `cd apps/api && uv run uvicorn app.main:create_app --factory --reload --port 8000`, run `just api` against the dev DB (`apps/api/.env`), and `curl localhost:8000/v1/health`. Expected: `{"status":"ok","database":"ok"}`.
- [ ] **Step 5: Commit** with message `feat(api): async database session and /v1/health`.

---

### Task 3: Supabase JWT verification

**Files:**
- Create: `apps/api/app/core/security.py`, `apps/api/tests/api/test_security.py`

**Interfaces:**
- Consumes: Task 1 (`Settings`, `ApiError`).
- Produces:

```python
@dataclass(frozen=True, slots=True)
class AccountContext:
    account_id: UUID
    email: str | None
class JwksCache:
    def __init__(self, jwks_url: str, ttl_seconds: int = 600, fetch: Callable[[str], Awaitable[dict]] | None = None) -> None
    async def key_for(self, kid: str) -> jwt.PyJWK      # refetch once if kid unknown or TTL expired; else ApiError auth_invalid
def get_jwks_cache() -> JwksCache                       # cached per process, from settings.supabase_jwks_url
async def current_account(authorization: str | None = Header(default=None),
                          jwks: JwksCache = Depends(get_jwks_cache),
                          settings: Settings = Depends(get_settings)) -> AccountContext
```

Verification rules:
- Algorithms are `ES256` and `RS256` only.
- `aud == "authenticated"`.
- `iss == f"{settings.supabase_url}/auth/v1"`.
- `exp` is required, with 30 s leeway.
- `sub` is a UUID and becomes `account_id`.

Errors:
- A missing header or a non-Bearer header → `ApiError("auth_required", 401)`.
- Any other failure → `ApiError("auth_invalid", 401)`.

- [ ] **Step 1: Write failing tests.** Generate an EC P-256 key in a fixture, serve its JWKS through the `fetch` parameter, and mint tokens with PyJWT.

```python
async def test_valid_token(make_token, jwks):        # helper fixtures in this test file
    ctx = await current_account(f"Bearer {make_token()}", jwks, settings)
    assert ctx.account_id == UUID(SUB) and ctx.email == "a@b.c"
@pytest.mark.parametrize("override", [{"aud": "anon"}, {"iss": "https://evil/auth/v1"}, {"exp": -60}])
async def test_bad_claims_rejected(make_token, jwks, override):
    with pytest.raises(ApiError) as e: await current_account(f"Bearer {make_token(**override)}", jwks, settings)
    assert (e.value.code, e.value.status) == ("auth_invalid", 401)
async def test_missing_header():
    with pytest.raises(ApiError) as e: await current_account(None, jwks, settings)
    assert e.value.code == "auth_required"
async def test_unknown_kid_refetches_once(rotating_fetch):   # fetch returns old JWKS then new
    ... # token signed with new key verifies; fetch called exactly 2 times
async def test_hs256_token_rejected(...):                   # alg confusion
```

- [ ] **Step 2: Run them to verify they fail.** Run `uv run pytest tests/api/test_security.py -v`. Expected: FAIL.
- [ ] **Step 3: Implement** to the Interfaces block. The default fetch uses `httpx.AsyncClient(timeout=5)`.
- [ ] **Step 4: Run the tests to verify they pass.**
- [ ] **Step 5: Commit** with message `feat(api): verify Supabase JWTs via JWKS`.

---

### Task 4: ORM models, Alembic baseline and RLS

**Files:**
- Create:
  - `apps/api/alembic.ini`, `apps/api/alembic/env.py` (async), `apps/api/alembic/versions/0001_baseline.py`
  - `apps/api/app/features/{me,members,consents,products,scans,meals,reports,ratelimit}/{__init__,models}.py`
  - `apps/api/tests/db/{__init__,conftest,test_migrations,test_rls}.py`
  - `supabase/config.toml` (via `supabase init`, then edited)
- Modify: `apps/api/AGENTS.md` (the commands section gains `just db-migrate` / `db-revision`)

**Interfaces:**
- Consumes: `Base` (Task 2).
- Produces the ORM classes `Account`, `Member`, `Consent`, `Product`, `OffProductCache`, `Scan`, `MealLog`, `ProductReport`, `RateLimitCounter` and `ExplanationCache`, with columns exactly as spec §4.

Additions to spec §4:
- `scans.image_sha256 text` with index `ix_scans_image_sha256`.
- `products.barcode` is unique. `products.verification_status` defaults to `'pending'`.
- `members.custom_alerts text[] default '{}'`.
- `accounts.language default 'en'`.
- `rate_limit_counters (key text, bucket text, window_start timestamptz, count int, PK(key,bucket,window_start))`.
- `explanation_cache (product_id uuid, profile_hash text, language text, payload jsonb, created_at timestamptz, PK(product_id,profile_hash,language))`.
- `accounts.id` has no FK to `auth.users`, because the tests run on vanilla Postgres.

**Migration `0001_baseline` in order:**
1. **Supabase shim**, guarded so it is a no-op on Supabase:
   - Create the roles `anon` and `authenticated` if missing.
   - Create schema `auth` and the function `auth.uid()` if missing. The function returns `nullif(current_setting('request.jwt.claim.sub', true), '')::uuid`.
2. **All tables, and check constraints for the enums:**
   - relation, diet, purpose, category, source, verification_status, reason and report status
   - language in (`'en'`, `'hi'`, `'mr'`)
3. **`ALTER TABLE … ENABLE ROW LEVEL SECURITY` on all ten tables.**
4. **Policies, all `TO authenticated`:**
   - `accounts`: `id = auth.uid()` (select/update).
   - `members`, `consents`, `scans`, `product_reports`: `account_id = auth.uid()` (all).
   - `meal_logs`: `EXISTS (SELECT 1 FROM members m WHERE m.id = meal_logs.member_id AND m.account_id = auth.uid())` (all).
   - `products`: select only, for any authenticated user.
   - `off_product_cache`, `rate_limit_counters`, `explanation_cache`: **no policies**, so they are server-only.
5. **Downgrade** drops everything in reverse. It does not drop the shim.

- [ ] **Step 1: Test database.**
  - Locally: install the Supabase CLI (`brew install supabase/tap/supabase`; the user may need to approve), run `supabase init` in the repo root, and edit `supabase/config.toml`:
    - `project_id = "smartnutri"`
    - `[auth] site_url = "http://localhost:3000"`
    - `additional_redirect_urls = ["http://localhost:3000/**", "com.smartnutri.app://login-callback"]`
    - `[auth.external.google] enabled = true`, `client_id = "env(SUPABASE_AUTH_EXTERNAL_GOOGLE_CLIENT_ID)"`, `secret = "env(SUPABASE_AUTH_EXTERNAL_GOOGLE_SECRET)"`, `skip_nonce_check = false`
    - `[auth.email] enable_signup = true`
    - `[auth.sms] enable_signup = false`
  - Then run `supabase start`.
  - Tests read `TEST_DATABASE_URL`, default `postgresql+psycopg://postgres:postgres@127.0.0.1:54322/postgres`, and **skip with a clear reason** when it is unreachable.
  - CI (Task 16) provides a `postgres:17` service.
- [ ] **Step 2: Write failing tests**

```python
# tests/db/conftest.py: fresh schema per session: alembic downgrade base → upgrade head on TEST_DATABASE_URL
TABLES = {"accounts","members","consents","products","off_product_cache","scans","meal_logs",
          "product_reports","rate_limit_counters","explanation_cache"}
async def test_all_tables_have_rls(db):
    rows = await db.execute(text("select relname, relrowsecurity from pg_class where relname = any(:t)"), {"t": list(TABLES)})
    assert {r.relname: r.relrowsecurity for r in rows} == {t: True for t in TABLES}

async def test_member_isolation(db, two_accounts):             # inserts A and B with one member each as postgres
    async with as_user(db, two_accounts.b):                   # SET LOCAL ROLE authenticated; set_config('request.jwt.claim.sub', b, true)
        names = (await db.execute(text("select name from members"))).scalars().all()
    assert names == ["B member"]

async def test_meal_logs_scoped_through_members(db, two_accounts): ...   # B sees 0 of A's meal_logs
async def test_server_only_tables_hidden(db, two_accounts):
    async with as_user(db, two_accounts.a):
        assert (await db.execute(text("select count(*) from off_product_cache"))).scalar() == 0  # row exists as postgres
async def test_downgrade_then_upgrade_is_clean(alembic_cfg): ...
```

- [ ] **Step 3: Run them to verify they fail.** Run `uv run pytest tests/db -v`. Expected: FAIL (no alembic env).
- [ ] **Step 4: Implement** the models, an async `alembic/env.py` (importing every `features/*/models.py` so autogenerate sees them), and the hand-written `0001_baseline.py` with the policies as `op.execute` SQL. Add `just db-migrate` and `just db-revision` usage to `apps/api/AGENTS.md`.
- [ ] **Step 5: Run the tests to verify they pass.** Then run `just db-migrate` against the **dev** Supabase project. Expected: `alembic current` prints `0001_baseline (head)`.
- [ ] **Step 6: Commit** with message `feat(api): baseline schema with RLS on every table`. Include `supabase/config.toml` in the commit with scope `supabase` noted in the body.

---

### Task 5: `/v1/me` and automatic account creation on first login

**Files:**
- Create: `apps/api/app/features/me/{router,schemas,service}.py`, `apps/api/tests/api/test_me.py`
- Modify: `apps/api/app/main.py`

**Interfaces:**
- Consumes: `current_account` (Task 3), `get_session` and `Account` (Task 4).
- Produces:

```python
# me/schemas.py
class MeOut(BaseModel): id: UUID; email: str | None; display_name: str | None; language: Literal["en","hi","mr"]; created_at: datetime
# me/service.py
async def ensure_account(session: AsyncSession, ctx: AccountContext) -> Account
    # INSERT … ON CONFLICT (id) DO NOTHING, then SELECT; display_name defaults to the email local part
# me/router.py  prefix "/v1/me"
GET ""  operation_id="me_get"  response_model=MeOut   (auth required)
```

PATCH and DELETE `/me` are built in M3 and M6, not here.

- [ ] **Step 1: Write failing tests** (they need the DB from Task 4; override `current_account`)

```python
async def test_first_call_creates_account(app, client, db_session):
    app.dependency_overrides[current_account] = lambda: AccountContext(UUID(A), "priya@example.com")
    r = await client.get("/v1/me")
    assert r.status_code == 200 and r.json()["display_name"] == "priya" and r.json()["language"] == "en"
async def test_second_call_is_idempotent(...): ...      # still 1 row in accounts
async def test_me_requires_auth(client):
    r = await client.get("/v1/me"); assert (r.status_code, r.json()["error"]["code"]) == (401, "auth_required")
```

- [ ] **Step 2: Run them to verify they fail.** Run `uv run pytest tests/api/test_me.py -v`. Expected: FAIL.
- [ ] **Step 3: Implement.**
- [ ] **Step 4: Run the tests to verify they pass.**
- [ ] **Step 5: Commit** with message `feat(api): /v1/me with account creation on first login`.

---

### Task 6: Rate-limit dependency

**Files:**
- Create: `apps/api/app/core/ratelimit.py`, `apps/api/tests/api/test_ratelimit.py`

**Interfaces:**
- Consumes: `RateLimitCounter` (Task 4), `current_account`, `Settings`, `ApiError`.
- Produces:

```python
BUCKETS: dict[str, tuple[str, int]]   # bucket -> (window "day"|"hour"|"minute", settings attribute name)
#   "label_scans" -> ("day", "rate_limit_label_scans_per_day")
#   "voice"       -> ("day", "rate_limit_voice_per_day")
#   "analyze"     -> ("hour", "rate_limit_analyze_per_hour")
#   "public"      -> ("minute", "rate_limit_public_per_minute")   # keyed by client IP, no auth
ERROR_CODES = {"label_scans": "rate_limited_scans", "voice": "rate_limited_voice"}   # others → "rate_limited"
def limit(bucket: str) -> Callable[..., Awaitable[None]]
    # FastAPI dependency: UPSERT count+1 for (key, bucket, window_start) and compare with the limit;
    # over the limit → ApiError(code, 429, details={"retry_after": seconds_until_window_end})
```

The window start is UTC-aligned: `date_trunc('day'|'hour'|'minute', now())`. Feature routes adopt `Depends(limit("..."))` from M1 onwards.

- [ ] **Step 1: Write failing tests** (DB-backed; a throwaway route with `Depends(limit("label_scans"))` and the limit overridden to 2)

```python
async def test_third_call_is_429(app, client, ...):
    assert [ (await client.post("/t")).status_code for _ in range(3) ] == [200, 200, 429]
    body = (await client.post("/t")).json()["error"]
    assert body["code"] == "rate_limited_scans" and 0 < body["details"]["retry_after"] <= 86400
async def test_limits_are_per_account(...): ...           # account B unaffected by A
async def test_public_bucket_keys_by_ip(...): ...
```

- [ ] **Step 2: Run them to verify they fail.**
- [ ] **Step 3: Implement.**
- [ ] **Step 4: Run the tests to verify they pass.**
- [ ] **Step 5: Commit** with message `feat(api): per-account and per-IP rate-limit dependency`.

---

### Task 7: OpenAPI export and generated clients

**Files:**
- Create:
  - `apps/api/scripts/export_openapi.py`
  - `apps/api/tests/api/test_openapi.py`
  - `packages/api-contract/dart/{pubspec.yaml,swagger_parser.yaml,analysis_options.yaml}`
  - `packages/api-contract/ts/{package.json,tsconfig.json,src/index.ts}`
- Generated: `packages/api-contract/openapi.json`, `dart/lib/**`, `ts/src/schema.d.ts`
- Modify: the `justfile` (`contract` recipe adds `dart pub get` and `dart run build_runner build --delete-conflicting-outputs` after swagger_parser)

**Interfaces:**
- Consumes: `create_app` (Tasks 1–6).
- Produces:

```python
# scripts/export_openapi.py: prints json.dumps(create_app(Settings(environment="test")).openapi(), indent=2, sort_keys=True)
```
```yaml
# dart/pubspec.yaml: name smartnutri_api; deps dio, retrofit, json_annotation; dev swagger_parser 1.45.1, build_runner, retrofit_generator, json_serializable
# dart/swagger_parser.yaml
swagger_parser: {schema_path: ../openapi.json, output_directory: lib/src, language: dart,
                 json_serializer: json_serializable, root_client: true, root_client_name: SmartNutriApiClient}
```
```ts
// ts/src/index.ts  (package "@smartnutri/api-client", "type": "module", exports "./src/index.ts")
import type { paths } from "./schema";
export type { paths, components } from "./schema";
export function createApiClient(baseUrl: string, getAccessToken: () => Promise<string | null>): Client<paths>
  // openapi-fetch createClient + middleware onRequest: sets Authorization: Bearer <token> when present
// ts/package.json scripts: "generate": "openapi-typescript ../openapi.json -o src/schema.d.ts", "typecheck": "tsc --noEmit"
```

- [ ] **Step 1: Write failing tests**

```python
def test_every_route_has_feature_operation_id():
    spec = create_app(Settings(environment="test")).openapi()
    ids = [op["operationId"] for p in spec["paths"].values() for op in p.values()]
    assert ids and len(ids) == len(set(ids))
    assert all(re.fullmatch(r"[a-z]+_[a-z_]+", i) for i in ids)
    assert {"health_get", "me_get"} <= set(ids)
```

- [ ] **Step 2: Run it to verify it fails** (until the routes set `operation_id`, FastAPI auto-generates names that fail the regex). Run `uv run pytest tests/api/test_openapi.py -v`.
- [ ] **Step 3: Implement** the script and the packages, then run `just contract`.
- [ ] **Step 4: Verify.**
  - `uv run pytest -q` passes.
  - `cd packages/api-contract/dart && dart analyze` reports no issues.
  - `pnpm --filter @smartnutri/api-client typecheck` passes.
  - The generated Dart client exposes `SmartNutriApiClient` with `health` and `me` getters (read `dart/lib/src/`).
- [ ] **Step 5: Commit** with message `feat(contract): export openapi.json and generate Dart and TS clients`.

---

### Task 8: i18n package

**Files:**
- Create:
  - `packages/i18n/package.json`
  - `packages/i18n/messages/{en,hi,mr}.json`
  - `packages/i18n/scripts/{build-arb.mjs,check-keys.mjs,build-arb.test.mjs,check-keys.test.mjs}`

**Interfaces:** Produces:
- `@smartnutri/i18n` (`"type": "module"`). Exports `./messages/*.json`. Scripts: `build`, which writes `../../apps/app/lib/core/l10n/app_{en,hi,mr}.arb`, then `check`, then `test` (`node --test scripts`).
- `flatten(obj) -> Record<string,string>`: nested keys become camelCase (`auth.signIn.google` → `authSignInGoogle`).
- `checkKeys(messagesByLocale) -> string[]` (errors): missing or extra keys versus `en`, and differing ICU placeholder sets.

`en.json` seed keys, with exact English values:

```json
{"app": {"name": "SmartNutri AI"},
 "common": {"disclaimer": "Information, not medical advice.", "loading": "Loading…", "retry": "Try again"},
 "auth": {"title": "Sign in", "google": "Continue with Google", "email": "Continue with email",
          "emailLabel": "Email address", "sendCode": "Send code", "codeLabel": "6-digit code",
          "verify": "Verify", "phone": "Continue with phone", "signOut": "Sign out"},
 "home": {"welcome": "Hello, {name}"},
 "verdict": {"status": {"ok": "OK", "caution": "Caution", "unknown": "Label unclear", "avoid": "Avoid"}},
 "error": {"auth_required": "Please sign in.", "auth_invalid": "Your session expired. Please sign in again.",
           "not_found": "Not found.", "validation_error": "Please check the highlighted fields.",
           "rate_limited": "Too many requests. Please wait a moment.",
           "rate_limited_scans": "You've reached today's label-scan limit.",
           "rate_limited_voice": "You've reached today's voice-question limit.",
           "internal_error": "Something went wrong. Please try again.", "network": "No internet connection."}}
```

`hi.json` and `mr.json` must have the same keys, translated by the implementer. List every translated key in the PR under "needs native-speaker review".

- [ ] **Step 1: Write failing tests**

```js
test("flatten camelCases nested keys", () => assert.deepEqual(flatten({auth:{signIn:{google:"x"}}}), {authSignInGoogle:"x"}));
test("missing key reported", () => assert.match(checkKeys({en:{a:"x",b:"y"}, hi:{a:"x"}}).join(), /hi.*missing.*b/));
test("placeholder mismatch reported", () => assert.match(checkKeys({en:{w:"Hi {name}"}, mr:{w:"Hi {nom}"}}).join(), /mr.*w.*placeholder/));
test("repo messages are consistent", () => assert.deepEqual(checkKeys(loadAll()), []));
```

- [ ] **Step 2: Run them to verify they fail.** Run `pnpm --filter @smartnutri/i18n test`. Expected: FAIL.
- [ ] **Step 3: Implement.** The ARB files carry `"@@locale"`. The build is deterministic (sorted keys).
- [ ] **Step 4: Run the tests to verify they pass.** Then run `just i18n`. Expected: three ARB files written, and `check` exits 0.
- [ ] **Step 5: Commit** with message `feat(i18n): shared messages en/hi/mr, ARB build and key check`.

---

### Task 9: Design tokens package

**Files:**
- Create: `packages/design-tokens/{package.json,tokens.json,style-dictionary.config.mjs,scripts/tokens.test.mjs}`
- Generated: `build/css/tokens.css`, `build/dart/tokens.dart` (committed)

**Interfaces:** Produces:
- `@smartnutri/design-tokens`, which exports `./tokens.css` (→ `build/css/tokens.css`).
- Its `build` script also copies the Dart output to `apps/app/lib/core/theme/tokens.g.dart`.
- CSS: a Tailwind 4 `@theme { --color-verdict-ok: …; … }` block (a custom style-dictionary format named `css/tailwind-theme`).
- Dart: `abstract final class SnTokens { static const Color verdictOk = Color(0xFF15803D); … }`.

Pinned token values (DTCG format):

| token | value |
|---|---|
| `color.verdict.ok` | `#15803D` |
| `color.verdict.caution` | `#B45309` |
| `color.verdict.avoid` | `#B91C1C` |
| `color.verdict.unknown` | `#4B5563` |
| `color.grade.a` … `color.grade.e` | `#038141` `#85BB2F` `#FECB02` `#EE8100` `#E63E11` (Nutri-Score) |
| `color.text.primary` / `color.surface.default` | `#111827` / `#FFFFFF` |
| `space.1…6` | 4 8 12 16 24 32 px |
| `radius.sm/md/lg` | 4 8 16 px |
| `font.size.sm/md/lg/xl` | 14 16 20 24 px |

- [ ] **Step 1: Write failing tests**

```js
test("verdict colours meet WCAG AA on white", () => { for (const k of ["ok","caution","avoid","unknown"]) assert.ok(contrast(tok(`color.verdict.${k}`), "#FFFFFF") >= 4.5) });
test("unknown is never green", () => { const [h,s] = hsl(tok("color.verdict.unknown")); assert.ok(s < 0.15 || h < 70 || h > 170) });
test("css output exposes verdict vars", () => assert.match(readFileSync(css), /--color-verdict-unknown:\s*#4B5563/i));
```

- [ ] **Step 2: Run them to verify they fail.** Run `pnpm --filter @smartnutri/design-tokens test`.
- [ ] **Step 3: Implement** `tokens.json` and the config with the custom format, then run `just tokens`.
- [ ] **Step 4: Run the tests to verify they pass.**
- [ ] **Step 5: Commit** with message `feat(tokens): shared verdict, grade and spacing tokens for Dart and CSS`.

---

### Task 10: Shared test fixtures and the API fixture test

**Files:**
- Create:
  - `packages/test-fixtures/{package.json,products/*.json,members/*.json,expected/*.json}`
  - `apps/api/tests/fixtures/{__init__,loader,test_shared_fixtures}.py`
- Modify: `packages/test-fixtures/README.md` (layout becomes `products/<name>.json`, `members/<id>.json`, `expected/<name>.<member>.json`)

**Interfaces:**
- Consumes: Plan 1 `app.scoring` (`analyze`, `Product`, `Nutrients`, `Member`, `Category`, `Diet`).
- Produces:

```python
# tests/fixtures/loader.py
FIXTURES = Path(__file__).parents[4] / "packages" / "test-fixtures"
def load_product(name: str) -> Product        # JSON keys mirror the Product/Nutrients field names (snake_case)
def load_member(member_id: str) -> Member
def expected_cases() -> list[tuple[str, str, dict]]   # (product, member, {"status": str, "reason_codes": [str]})
```

**Content:**
- **Products:** the seven Plan 1 products (`sf_biscuit`, `namkeen`, `curd`, `oats`, `cola`, `water`, `no_ingredients`), with values copied exactly from the Plan 1 fixture table. Each file also has `"source": "plan-1 fixture"`.
- **Members:** the nine Plan 1 members.
- **Expected files.** Reason codes are in engine order: severity rank descending, then code.

| file | status | reason_codes |
|---|---|---|
| `sf_biscuit.diabetic_adult.json` | avoid | `["misleading_sugar_claim", "hidden_sugars"]` |
| `sf_biscuit.milk_allergic_child.json` | avoid | `["allergen_contains"]` |
| `sf_biscuit.weight_loss_adult.json` | caution | `["energy_dense", "nutriscore_low"]` |
| `namkeen.bp_parent.json` | avoid | `["salt_high"]` |
| `namkeen.jain_adult.json` | avoid | `["diet_violation"]` |
| `namkeen.peanut_allergic.json` | avoid | `["allergen_contains"]` |
| `curd.diabetic_adult.json` | ok | `[]` |
| `curd.vegan_adult.json` | avoid | `["diet_violation"]` |
| `curd.milk_allergic_child.json` | avoid | `["allergen_contains"]` |
| `no_ingredients.peanut_allergic.json` | unknown | `["allergen_unknown"]` |

- [ ] **Step 1: Write the failing test.** Parametrize over `expected_cases()`, and for each case assert `analyze(load_product(p), [load_member(m)]).verdicts[0]` has the expected `status.value` and `[r.code for r in reasons]`.
- [ ] **Step 2: Run it to verify it fails.** Run `uv run pytest tests/fixtures -v`. Expected: FAIL (no fixture files).
- [ ] **Step 3: Write the JSON files and the loader.**
- [ ] **Step 4: Run the tests to verify they pass.** If a case disagrees with the engine, **stop and report it**. Never edit an expectation to match the code without a `nutrition-safety-reviewer` ruling.
- [ ] **Step 5: Commit** with message `test(fixtures): shared Plan 1 products, members and expected verdicts`.

---

### Task 11: Flutter Android shell: platform, dependencies, config, bootstrap

**Files:**
- Delete: `apps/app/lib/**` (prototype), `apps/app/test/widget_test.dart`, `apps/app/android/app/src/main/kotlin/com/smartnutri/nutrition_ai/`
- Create:
  - `apps/app/android/app/src/main/kotlin/com/smartnutri/app/MainActivity.kt`
  - `apps/app/lib/{main,app,bootstrap}.dart`
  - `apps/app/lib/core/config/app_config.dart`, `apps/app/lib/core/theme/app_theme.dart`, `apps/app/l10n.yaml`
  - `apps/app/test/core/app_config_test.dart`
- Modify:
  - `apps/app/pubspec.yaml`
  - `apps/app/android/app/build.gradle.kts` (`namespace` and `applicationId` = `com.smartnutri.app`)
  - `apps/app/android/app/src/main/AndroidManifest.xml`
  - `apps/app/env/example.json` (add `"FEATURE_PHONE_OTP": "false"`)
  - `apps/app/AGENTS.md` (the `applicationId` line becomes `com.smartnutri.app`)
  - `supabase/README.md` (the deep link becomes `com.smartnutri.app://login-callback`)

**Interfaces:**
- Consumes: the generated ARB files (Task 8), `tokens.g.dart` (Task 9), `smartnutri_api` (Task 7).
- Produces:

```dart
class AppConfig {  // all from String/bool.fromEnvironment
  final String environment, apiBaseUrl, supabaseUrl, supabasePublishableKey, googleWebClientId, sentryDsn, posthogKey;
  final bool featurePhoneOtp;               // FEATURE_PHONE_OTP, default false
  const AppConfig.fromEnvironment();
  List<String> missingRequired();           // names of empty required keys: API_BASE_URL, SUPABASE_URL, SUPABASE_PUBLISHABLE_KEY
}
final appConfigProvider = Provider<AppConfig>((ref) => const AppConfig.fromEnvironment());
Future<void> bootstrap();                    // Supabase.initialize, then runApp(ProviderScope(child: SmartNutriApp()))
ThemeData buildAppTheme();                   // ColorScheme built from SnTokens
```

**Dependencies:**
- `flutter_riverpod ^3`, `riverpod_annotation`, `go_router`, `dio`, `supabase_flutter ^2.18.3`, `google_sign_in`, `sentry_flutter`, `posthog_flutter`, `flutter_localizations`, `intl`
- `smartnutri_api: {path: ../../packages/api-contract/dart}`
- Dev: `riverpod_generator`, `build_runner`, `flutter_lints`
- Remove `translator`, `provider`, `http`, `file_picker`, `speech_to_text`, `flutter_tts` and `shared_preferences`.

**Manifest:**
- The `INTERNET`, `CAMERA` and `RECORD_AUDIO` permissions.
- An intent filter on `MainActivity` for `android:scheme="com.smartnutri.app" android:host="login-callback"`.
- `android:label="SmartNutri AI"`.

- [ ] **Step 0:** run `flutter upgrade`. Record the version in the commit body.
- [ ] **Step 1: Write the failing test**

```dart
test('missingRequired lists empty required keys', () {
  const c = AppConfig(environment: 'dev', apiBaseUrl: '', supabaseUrl: 'x', supabasePublishableKey: '', googleWebClientId: '', sentryDsn: '', posthogKey: '', featurePhoneOtp: false);
  expect(c.missingRequired(), ['API_BASE_URL', 'SUPABASE_PUBLISHABLE_KEY']);
});
```

- [ ] **Step 2: Run it to verify it fails.** Run `cd apps/app && flutter test test/core`.
- [ ] **Step 3: Implement.**
  - Delete the prototype.
  - Update Gradle and the manifest.
  - Move `MainActivity.kt` to package `com.smartnutri.app`.
  - Write the files above.
  - `l10n.yaml`: `arb-dir: lib/core/l10n`, `template-arb-file: app_en.arb`, `output-localization-file: app_localizations.dart`.
- [ ] **Step 4: Verify.**
  - `flutter pub get && flutter gen-l10n && flutter analyze && flutter test` all pass.
  - `flutter build apk --debug --dart-define-from-file=env/dev.json` succeeds.
- [ ] **Step 5: Commit** with message `feat(app): Android shell — com.smartnutri.app, Riverpod, config, theme tokens, l10n`.

---

### Task 12: Flutter login, router and authenticated API client

**Files:**
- Create:
  - `apps/app/lib/core/router/app_router.dart`
  - `apps/app/lib/core/network/{api_client.dart,auth_interceptor.dart}`
  - `apps/app/lib/features/auth/data/auth_repository.dart`
  - `apps/app/lib/features/auth/presentation/{sign_in_screen,email_otp_screen,phone_otp_screen}.dart`
  - `apps/app/lib/features/home/presentation/home_screen.dart`
  - `apps/app/test/{core/auth_interceptor_test.dart,features/auth/sign_in_screen_test.dart,core/router_test.dart}`

**Interfaces:**
- Consumes: Task 11, and `SmartNutriApiClient` (Task 7).
- Produces:

```dart
abstract interface class AuthRepository {
  Stream<bool> authStateChanges();  bool get isSignedIn;  Future<String?> accessToken();
  Future<void> signInWithGoogle();                 // google_sign_in → idToken → supabase.auth.signInWithIdToken(OAuthProvider.google)
  Future<void> sendEmailOtp(String email);  Future<void> verifyEmailOtp(String email, String code);
  Future<void> sendPhoneOtp(String phone);  Future<void> verifyPhoneOtp(String phone, String code);
  Future<void> signOut();
}
final authRepositoryProvider = Provider<AuthRepository>(...);       // SupabaseAuthRepository
class AuthInterceptor extends Interceptor { AuthInterceptor(Future<String?> Function() token, Future<void> Function() onUnauthorized); }
final apiClientProvider = Provider<SmartNutriApiClient>(...);      // Dio(baseUrl: config.apiBaseUrl) + AuthInterceptor
final routerProvider = Provider<GoRouter>(...);   // routes: /sign-in, /sign-in/email, /sign-in/phone (only when featurePhoneOtp), /home
                                                  // redirect: signed-out → /sign-in; signed-in on /sign-in* → /home
```

`HomeScreen` calls `me_get` through `apiClientProvider` and shows `home.welcome` with `display_name`, plus `common.disclaimer` and a sign-out action. Errors from the API envelope map to `error.<code>` strings.

- [ ] **Step 1: Write failing tests**

```dart
test('adds bearer token', ...);             // fake handler captures headers → 'Authorization': 'Bearer t1'
test('401 triggers onUnauthorized', ...);
testWidgets('sign-in shows Google and email, hides phone when flag off', ...);  // finds l10n strings, not literals
testWidgets('signed-out user is redirected to /sign-in', ...);                   // fake AuthRepository
```

- [ ] **Step 2: Run them to verify they fail.** Run `flutter test`.
- [ ] **Step 3: Implement.** Google sign-in uses the `google_sign_in` API current on pub.dev; check its README. Use `serverClientId = config.googleWebClientId` so the ID token's audience is the web client that Supabase trusts.
- [ ] **Step 4: Verify.**
  - `flutter analyze && flutter test` pass.
  - Manually on an emulator, with the API running locally: Google login and email OTP both reach `/home` and show the name from `GET /v1/me`.
- [ ] **Step 5: Commit** with message `feat(app): Supabase login (Google, email OTP; phone behind flag), router guard, authed API client`.

---

### Task 13: Next.js shell (scaffold, i18n, tokens, Biome, tests)

**Files:**
- Create:
  - `apps/web/**` (from `create-next-app`)
  - `apps/web/{biome.json,vitest.config.ts,playwright.config.ts}`
  - `apps/web/src/i18n/{routing.ts,request.ts}`
  - `apps/web/src/app/[locale]/{layout.tsx,(public)/page.tsx}`
  - `apps/web/tests/landing.test.tsx`, `apps/web/e2e/smoke.spec.ts`
- Modify: `apps/web/.env.example` (add `NEXT_PUBLIC_FEATURE_PHONE_OTP=false`)

**Interfaces:**
- Consumes: `@smartnutri/i18n` messages (Task 8), `@smartnutri/design-tokens/tokens.css` (Task 9).
- Produces:

```ts
// src/i18n/routing.ts
export const routing = defineRouting({ locales: ["en", "hi", "mr"], defaultLocale: "en" });
// src/i18n/request.ts: getRequestConfig → messages from `@smartnutri/i18n/messages/${locale}.json`
// package.json: name "@smartnutri/web"; scripts dev, build, start, test (vitest run), e2e (playwright test),
//               lint (biome check .), typecheck (tsc --noEmit)
// next.config.ts: output "standalone", next-intl plugin, transpilePackages ["@smartnutri/api-client"]
```

- [ ] **Step 1: Scaffold.**
  - Run `pnpm create next-app@16.4.4 apps/web` with TypeScript, App Router, `src/`, Tailwind and pnpm, and **no ESLint**. Check `--help` for the exact flag names.
  - Rename the package to `@smartnutri/web`, and add the workspace dependencies `@smartnutri/i18n`, `@smartnutri/design-tokens` and `@smartnutri/api-client` (`workspace:*`).
  - Install `next-intl@4.14.9`, `@biomejs/biome@2.6.4`, `vitest@5.1.0`, `@testing-library/react@16.3.3`, `jsdom` and `@playwright/test@1.64.1`.
  - Run `pnpm dlx shadcn@4.23.0 init`.
  - Keep the TypeScript version the scaffold pins.
- [ ] **Step 2: Write failing tests**

```tsx
// tests/landing.test.tsx: render the landing page under NextIntlClientProvider(en) → app.name and common.disclaimer visible
// e2e/smoke.spec.ts
test("en landing renders", async ({ page }) => { await page.goto("/en"); await expect(page.getByRole("heading", { name: "SmartNutri AI" })).toBeVisible(); });
test("hi sets html lang", async ({ page }) => { await page.goto("/hi"); await expect(page.locator("html")).toHaveAttribute("lang", "hi"); });
```

- [ ] **Step 3: Run them to verify they fail.** Run `pnpm --filter @smartnutri/web test`.
- [ ] **Step 4: Implement.**
  - `globals.css`: `@import "tailwindcss"; @import "@smartnutri/design-tokens/tokens.css";`
  - Layout: `<html lang={locale}>`.
  - Landing: heading `app.name`, disclaimer, and a link to `/[locale]/sign-in`. No literal strings.
- [ ] **Step 5: Verify.** Run `pnpm --filter @smartnutri/web lint && pnpm --filter @smartnutri/web typecheck && pnpm --filter @smartnutri/web test && pnpm --filter @smartnutri/web build && pnpm --filter @smartnutri/web e2e`. Playwright's `webServer` runs `pnpm start`. All must pass.
- [ ] **Step 6: Commit** with message `feat(web): Next.js 16 shell with next-intl, token theme, Biome, Vitest and Playwright`.

---

### Task 14: Web login, session middleware, security headers and authed API client

**Files:**
- Create:
  - `apps/web/src/lib/supabase/{client,server,middleware}.ts`
  - `apps/web/src/lib/api/client.ts`
  - `apps/web/src/proxy.ts` (Next 16 renamed middleware to proxy)
  - `apps/web/src/app/providers.tsx`
  - `apps/web/src/app/auth/callback/route.ts`
  - `apps/web/src/app/[locale]/(public)/sign-in/page.tsx`
  - `apps/web/src/features/auth/components/{SignInPanel,EmailOtpForm,PhoneOtpForm}.tsx`
  - `apps/web/src/app/[locale]/(app)/{layout.tsx,home/page.tsx}`
  - `apps/web/tests/{sign-in.test.tsx,middleware.test.ts}`, `apps/web/e2e/auth.spec.ts`

**Interfaces:**
- Consumes: `createApiClient` (Task 7), `routing` (Task 13).
- Produces:

```ts
export function createSupabaseBrowserClient(): SupabaseClient            // lib/supabase/client.ts
export async function createSupabaseServerClient(): Promise<SupabaseClient> // lib/supabase/server.ts (cookies())
export async function updateSession(req: NextRequest, res: NextResponse): Promise<{ res: NextResponse; signedIn: boolean }>
export function getApi(): Client<paths>          // lib/api/client.ts: browser client; token from supabase.auth.getSession()
export const PROTECTED_SEGMENT = "(app)"         // middleware matches /:locale/(home|scan|members|history|meals|product|settings)...
export function securityHeaders(nonce: string): Record<string, string>
// CSP: default-src 'self'; script-src 'self' 'nonce-<n>' 'strict-dynamic'; connect-src 'self' <API_BASE_URL> <SUPABASE_URL>
//      https://*.sentry.io https://*.posthog.com; img-src 'self' data: blob: https://images.openfoodfacts.org;
//      frame-ancestors 'none'  ·  X-Frame-Options DENY · Referrer-Policy strict-origin-when-cross-origin
//      · Permissions-Policy camera=(self), microphone=(self)
```

Middleware order:
1. next-intl locale.
2. Supabase session refresh.
3. An unauthenticated request to a protected path → `302 /<locale>/sign-in?next=<path>`.
4. Attach the security headers with a per-request nonce.

The sign-in page:
- **Google:** `signInWithOAuth({provider: "google", options: {redirectTo: `${NEXT_PUBLIC_SITE_URL}/auth/callback?next=/<locale>/home`}})`.
- **Email OTP:** `signInWithOtp`, then `verifyOtp({type: "email"})`.
- **Phone:** shown only when `NEXT_PUBLIC_FEATURE_PHONE_OTP === "true"`.
- The callback route exchanges the code for a session (`exchangeCodeForSession`) and redirects to a **same-origin** `next` only.

`(app)/home/page.tsx` is a client component. It calls `getApi().GET("/v1/me")` via TanStack Query and shows `home.welcome`. The API envelope's `error.code` maps to `error.<code>`.

- [ ] **Step 1: Write failing tests**

```ts
test("phone hidden when flag off", ...);                      // render SignInPanel, flag "false" → no "auth.phone" button
test("protected path redirects when signed out", async () => { const res = await middleware(req("/en/home")); expect(res.headers.get("location")).toMatch(/\/en\/sign-in\?next=%2Fen%2Fhome/); });
test("public path never redirects", async () => { expect((await middleware(req("/hi"))).status).not.toBe(302); });
test("csp present with nonce", async () => { expect((await middleware(req("/en"))).headers.get("content-security-policy")).toMatch(/script-src 'self' 'nonce-/); });
test("callback ignores cross-origin next", ...);              // ?next=https://evil.example → redirect to /en/home
// e2e/auth.spec.ts: /en/home → lands on /en/sign-in; response has X-Frame-Options DENY
```

- [ ] **Step 2: Run them to verify they fail.**
- [ ] **Step 3: Implement.** Follow the `@supabase/ssr` 0.12 Next.js guide for the cookie get/set API. Mock Supabase in the unit tests.
- [ ] **Step 4: Verify.**
  - `lint`, `typecheck`, `test`, `build` and `e2e` all pass.
  - Manually: Google and email OTP login on `http://localhost:3000/en/sign-in` reach `/en/home` with the account name from `/v1/me`.
- [ ] **Step 5: Commit** with message `feat(web): Supabase cookie auth, protected routes, CSP and authed API client`.

---

### Task 15: Sentry and PostHog in all three apps (no health data)

**Files:**
- Create:
  - `apps/api/app/core/observability.py`, `apps/api/tests/api/test_observability.py`
  - `apps/web/src/instrumentation.ts`, `apps/web/src/instrumentation-client.ts`, `apps/web/src/lib/analytics.ts`
  - `apps/app/lib/core/observability/analytics.dart`, `apps/app/test/core/analytics_test.dart`
- Modify: `apps/api/app/main.py`, `apps/web/next.config.ts`, `apps/app/lib/bootstrap.dart`

**Interfaces:** Produces:

```python
ALLOWED_EVENT_PROPS = frozenset({"platform", "locale", "screen", "status_code", "source"})
def scrub_event(event: dict, hint: dict) -> dict | None   # Sentry before_send: drop request.data, cookies, headers.authorization, user.email
def init_observability(settings: Settings) -> None        # sentry_sdk.init only when settings.sentry_dsn; send_default_pii=False
def capture(event: str, distinct_id: str, properties: dict | None = None) -> None   # PostHog; no-op without key; drops keys not in ALLOWED_EVENT_PROPS
```

Web (`lib/analytics.ts`) and Android (`analytics.dart`) expose `track(event, props)` with **the same allow-list** and a no-op without a key. Both run Sentry with PII off.

On the web, PostHog is initialised with `person_profiles: "identified_only"`, `autocapture: false` and `capture_pageview: true`.

- [ ] **Step 1: Write failing tests** (API: `scrub_event` removes the body, auth header and email. Web and Android: `track` drops `{"conditions": [...]}` and keeps `{"screen": "home"}`.)
- [ ] **Step 2: Run them to verify they fail.**
- [ ] **Step 3: Implement.**
- [ ] **Step 4: Run all three suites** (`just test`).
- [ ] **Step 5: Commit** with message `feat: Sentry and PostHog with PII scrubbing and an event-property allow-list`.

---

### Task 16: Dockerfiles, real CI and pre-commit

**Files:**
- Create: `apps/api/{Dockerfile,.dockerignore}`, `apps/web/{Dockerfile,.dockerignore}`
- Modify: `.github/workflows/{api,app,web}.yml`, the `justfile` (adds the `docker-api` and `docker-web` recipes)

**Specifics:**
- **API image:**
  - `python:3.13-slim`, plus the `uv` binary copied from `ghcr.io/astral-sh/uv`.
  - `uv sync --frozen --no-dev`. Runs as a non-root user.
  - `CMD uvicorn app.main:create_app --factory --host 0.0.0.0 --port ${PORT:-8080}`.
- **Web image:**
  - Multi-stage `node:24-slim`, with the **repo root** as the build context.
  - `corepack enable`, `pnpm install --frozen-lockfile --filter @smartnutri/web...`, `pnpm --filter @smartnutri/web build`.
  - The runner stage copies `.next/standalone`, `.next/static` and `public`. Runs as non-root with `PORT=8080`.
  - The `NEXT_PUBLIC_*` values arrive as **build args**. They are public.
- **`api.yml`:**
  - Add a `postgres:17` service with `TEST_DATABASE_URL`, so the `tests/db` suite runs.
  - Add a `contract` job: setup-uv, Dart (`dart-lang/setup-dart`, pinned SHA), pnpm, `just contract`, then `git diff --exit-code packages/api-contract`. Install `just` via `extractions/setup-just`, pinned SHA.
- **`app.yml`:** `flutter pub get`, `flutter gen-l10n`, then the existing steps.
- **`web.yml`:** after the build, `pnpm exec playwright install --with-deps chromium` and `pnpm --filter @smartnutri/web e2e`. The i18n check step already exists.
- **Every new action** is pinned to a full commit SHA with a version comment, and `permissions: contents: read` stays.
- **Pre-commit:** run `uv tool install pre-commit && pre-commit install && pre-commit run --all-files`, and fix any findings it raises in generated files by adding excludes, never by editing generated output.

- [ ] **Step 1: Verify the images build:** `docker build -t sn-api apps/api` and `docker build -f apps/web/Dockerfile -t sn-web .`.
- [ ] **Step 2: Run the API image** with a dev `.env`: `docker run --env-file apps/api/.env -p 8080:8080 sn-api`, then `curl localhost:8080/v1/health`. Expected: `{"status":"ok","database":"ok"}`.
- [ ] **Step 3: Push the branch to GitHub** (`git push -u origin v1-rebuild`). This needs the user's go-ahead, because it publishes to the shared remote. All four workflows must be green.
- [ ] **Step 4: Commit** with message `ci: real API/app/web pipelines, contract drift job, Dockerfiles`.

---

### Task 17: Dev deploy to Cloud Run (API + web)

**Files:**
- Create: `scripts/push-secrets.sh`, `scripts/deploy-dev.sh`
- Modify:
  - the `justfile` (adds `deploy-api-dev` and `deploy-web-dev`)
  - `docs/SETUP_ACCOUNTS.md` (records the dev URLs)
  - `docs/FEATURE_PARITY.md` (F1 → 🟡)

**Specifics.** `C="CLOUDSDK_ACTIVE_CONFIG_NAME=smartnutri"` prefixes every command.

**`scripts/push-secrets.sh` (the user runs it, not an agent):**
- Reads `apps/api/.env` without echoing anything.
- For each of `callmissed-api-key-dev` (from `CALLMISSED_API_KEY`), `supabase-secret-key-dev` and `database-url-dev`, runs `gcloud secrets create … --replication-policy=user-managed --locations=asia-south1 --data-file=-`. If the secret exists, it runs `gcloud secrets versions add` instead.
- Prints only the secret names and "ok".

**Service account:**
- Create `smartnutri-api-dev@smartnutri-513518.iam.gserviceaccount.com`.
- Grant `roles/secretmanager.secretAccessor` on those three secrets only.

**`deploy-api-dev`:**
- `gcloud builds submit apps/api --tag asia-south1-docker.pkg.dev/smartnutri-513518/smartnutri/api:$(git rev-parse --short HEAD)`
- `gcloud run deploy smartnutri-api-dev` with:
  - `--region asia-south1 --service-account <sa> --allow-unauthenticated`
  - `--min-instances 0 --max-instances 3 --memory 512Mi --cpu 1`
  - `--set-secrets CALLMISSED_API_KEY=callmissed-api-key-dev:latest,SUPABASE_SECRET_KEY=supabase-secret-key-dev:latest,DATABASE_URL=database-url-dev:latest`
  - `--set-env-vars` with the non-secret values from `apps/api/.env.example` (`ENVIRONMENT=dev`, `SUPABASE_URL`, `SUPABASE_PROJECT_REF`, `SUPABASE_JWKS_URL`, `ALLOWED_ORIGINS=<web dev URL>,http://localhost:3000`, model ids, rate limits)
- **Auth is enforced in the app** (`current_account`), not by Cloud Run IAM. The web app and Android app call it directly.

**`deploy-web-dev`:**
- `gcloud builds submit .` with a cloudbuild step that passes the `NEXT_PUBLIC_*` build args (`NEXT_PUBLIC_API_BASE_URL=<api dev URL>`, `NEXT_PUBLIC_SITE_URL=<web dev URL>`).
- `gcloud run deploy smartnutri-web-dev --allow-unauthenticated --min-instances 0 --max-instances 3`.

- [ ] **Step 1: Ask the user to run `! bash scripts/push-secrets.sh`.** Do not run it yourself. Then verify with `gcloud secrets list` (names only).
- [ ] **Step 2: Deploy the API.** Run `just deploy-api-dev`, then `curl <api-dev-url>/v1/health`. Expected: `{"status":"ok","database":"ok"}`.
- [ ] **Step 3: Deploy the web app.** Run `just deploy-web-dev`, then open `<web-dev-url>/en`. Expected: the landing page renders, with a CSP header.
- [ ] **Step 4: Register the dev web origin** with the user, via Chrome:
  - Supabase Auth → URL Configuration: add `<web-dev-url>/**`.
  - The Google OAuth web client: add `<web-dev-url>` as an authorised JavaScript origin.
  - Then redeploy the API with `ALLOWED_ORIGINS` including it.
- [ ] **Step 5: End-to-end check.**
  - Sign in on the dev web URL with Google, then with email OTP. Both reach `/en/home` and show the name from `/v1/me`.
  - On Android, set `API_BASE_URL` in `env/dev.json` to the API dev URL and repeat.
- [ ] **Step 6: Commit** with message `chore(ci): dev deploy scripts for Cloud Run (API + web) and secrets push script`.

---

## Self-review notes (plan author)

- **Spec coverage, Plan 2 bullets in §8:**
  - Root tooling: T16. CODEOWNERS and the PR template already exist.
  - API skeleton: T1–T6. `openapi.json` export: T7.
  - The contract, i18n, tokens and fixtures packages: T7–T10.
  - Flutter shell: T11–T12. Desktop folders were removed earlier.
  - Next shell: T13–T14.
  - Observability: T15. Docker and CI: T16. Dev deploy: T17.
- **Deferred on purpose:**
  - PATCH/DELETE `/me` (M3, M6).
  - Workload Identity Federation for GitHub deploys (M6).
  - The prod Supabase project and the Send-SMS hook (M6).
  - The explanation-cache reader (M3).
- **Contract names** match the shared naming contract exactly. `AccountContext` is produced in Task 3 and consumed by Tasks 5–6. `RateLimitCounter` is produced in Task 4 and consumed by Task 6.
