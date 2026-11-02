---
name: api-endpoint
description: Use when adding or changing a FastAPI endpoint in apps/api (feature folders under app/features — members, products, scans, analyze, meals, voice, consents, reports, methodology, me) or its request/response schemas, models, migrations, auth, rate limits or tests.
---

# Adding a FastAPI endpoint

The stack is Python 3.13, FastAPI, Pydantic 2, SQLAlchemy 2 (async), Alembic, pytest with httpx, and `uv`. The layout is feature-based (`apps/api/AGENTS.md`): each feature owns `app/features/<f>/{router,schemas,models,service}.py`.

## Steps

1. **Write the failing API test first** in `tests/api/test_<feature>.py`.
   - Use the `client` fixture (an `httpx.AsyncClient` over the app), `auth_headers(account)` (signs a test JWT), and the per-test database fixture (rolls back after each test).
   - Cover: happy path, 401 without a token, **404 for another account's record** (never 403, which leaks that it exists), 422 on bad input, and 429 if the route is rate-limited.
2. **Schemas** in `app/features/<f>/schemas.py`.
   - Use Pydantic models `<Thing>Create`, `<Thing>Update`, `<Thing>Out`, with explicit constraints (`Field(ge=0, le=100)`, `Literal[...]`, max lengths).
   - No `dict[str, Any]` in public responses: the generated clients need real types.
3. **Models** in `app/features/<f>/models.py` (SQLAlchemy). Every row carries `account_id`, or reaches it through a parent.
4. **Logic** in `app/features/<f>/service.py`.
   - Plain async functions taking `session` and `account_id`. No FastAPI imports.
   - Call other features only through their `service.py`.
5. **Router** in `app/features/<f>/router.py`. Give every route an explicit, stable `operation_id`, which the generated client method names come from:
   ```python
   router = APIRouter(prefix="/members", tags=["members"])

   @router.get("/{member_id}", response_model=MemberOut, operation_id="members_get")
   async def get_member(member_id: UUID, user: CurrentUser = Depends(current_user),
                        session: AsyncSession = Depends(get_session)) -> MemberOut:
       return await service.get(session, account_id=user.account_id, member_id=member_id)
   ```
   Register the router in `app/main.py`.
6. **Database changes** go in an Alembic migration:
   - `uv run alembic revision --autogenerate -m "<what>"`, then review the file by hand.
   - For every new table, add `ENABLE ROW LEVEL SECURITY` and its policies **in the same migration** with `op.execute(...)`. Never add policies in `supabase/`.
7. Run `uv run pytest tests/api -v && uv run ruff check app tests`.
8. **Contract:** run `just contract` (see the `api-contract` skill) and commit `packages/api-contract/` in the same PR.
9. **Parity:**
   - Note in the PR which Android (`apps/app`) and web (`apps/web`) work this endpoint unblocks.
   - Add new reason or error codes to `packages/i18n/messages/{en,hi,mr}.json`.
   - If verdicts change, update `packages/test-fixtures`.

## Rules

- **Auth on everything** except `GET /v1/health`, `GET /v1/methodology` and public product info (generic data only, never verdicts).
  - `current_user` verifies the Supabase JWT against the JWKS (`SUPABASE_JWKS_URL`), checking audience and expiry.
- **Scope every query by `account_id`.** Member-level routes also check that the member belongs to the account.
- **Errors:**
  - Raise domain exceptions in services. One handler maps them to `{"error": {"code": "...", "message_key": "..."}}`.
  - Never return `str(exc)` or stack traces. Log with the request id to Sentry.
- **Verdicts come only from `app.scoring.analyze()`.** An endpoint may add LLM explanation text but never alters the result.
- **Health and personal data:** never log request bodies with conditions or allergies. Responses return reason **codes**, which the clients localise.
- **Uploads:**
  - Sniff the content type from the bytes; don't trust the header. Images are capped at 8 MB, audio at 30 s.
  - Store under a generated UUID name.
- **Rate limits and caching:**
  - Expensive routes (`/scans/label`, `/voice/ask`, `/analyze` explanations) are rate-limited per account, returning 429 with code `rate_limited_<route>`.
  - Cache extractions by image SHA-256 and products by barcode.
- **Blocking work** runs via `anyio.to_thread.run_sync` or a worker.

## Pitfalls

- **CORS:** only `ALLOWED_ORIGINS` (the web origins), never `*` with credentials.
- Changing a field or `operation_id` silently breaks both clients. Regenerate and fix both in the same PR.
- **Open Food Facts:** keep data in `off_product_cache` only, and send a `User-Agent`.
