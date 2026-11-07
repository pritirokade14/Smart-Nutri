import asyncio
import uuid
from collections.abc import AsyncIterator
from datetime import UTC

import httpx
import pytest
from fastapi import Depends, FastAPI, Request
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import NullPool

from app.core.config import Settings
from app.core.ratelimit import limit
from app.core.security import AccountContext, current_account
from app.db.session import get_session
from app.main import create_app

A = uuid.uuid4()
B = uuid.uuid4()


@pytest.fixture
async def rl_app(migrated, pg_url):
    engine = create_async_engine(pg_url, poolclass=NullPool)
    maker = async_sessionmaker(engine, expire_on_commit=False)
    async with engine.begin() as conn:
        await conn.execute(text("truncate rate_limit_counters"))

    settings = Settings(
        _env_file=None,
        environment="test",
        rate_limit_label_scans_per_day=2,
        rate_limit_voice_per_day=2,
        rate_limit_analyze_per_hour=2,
        rate_limit_public_per_minute=2,
    )
    app: FastAPI = create_app(settings)

    async def _session() -> AsyncIterator[AsyncSession]:
        async with maker() as s:
            yield s

    async def _account(request: Request) -> AccountContext:
        return AccountContext(account_id=uuid.UUID(request.headers["x-acct"]), email=None)

    app.dependency_overrides[get_session] = _session
    app.dependency_overrides[current_account] = _account

    @app.post("/t", dependencies=[Depends(limit("label_scans"))])
    async def t() -> dict:
        return {"ok": True}

    @app.post("/v", dependencies=[Depends(limit("voice"))])
    async def v() -> dict:
        return {"ok": True}

    @app.post("/a", dependencies=[Depends(limit("analyze"))])
    async def a() -> dict:
        return {"ok": True}

    @app.post("/p", dependencies=[Depends(limit("public"))])
    async def p() -> dict:
        return {"ok": True}

    yield app
    await engine.dispose()


def _client(app: FastAPI, ip: str = "10.0.0.1") -> httpx.AsyncClient:
    return httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app, client=(ip, 1234)), base_url="http://t"
    )


async def test_third_call_is_429(rl_app):
    async with _client(rl_app) as c:
        h = {"x-acct": str(A)}
        codes = [(await c.post("/t", headers=h)).status_code for _ in range(3)]
        assert codes == [200, 200, 429]
        resp = await c.post("/t", headers=h)
    body = resp.json()["error"]
    assert body["code"] == "rate_limited_scans"
    assert 0 < body["details"]["retry_after"] <= 86400
    assert int(resp.headers["retry-after"]) >= 1


async def test_voice_and_generic_codes(rl_app):
    async with _client(rl_app) as c:
        h = {"x-acct": str(A)}
        for _ in range(2):
            await c.post("/v", headers=h)
            await c.post("/a", headers=h)
        assert (await c.post("/v", headers=h)).json()["error"]["code"] == "rate_limited_voice"
        resp = await c.post("/a", headers=h)
    assert resp.status_code == 429
    assert resp.json()["error"]["code"] == "rate_limited"
    assert 0 < resp.json()["error"]["details"]["retry_after"] <= 3600


async def test_limits_are_per_account(rl_app):
    async with _client(rl_app) as c:
        ha, hb = {"x-acct": str(A)}, {"x-acct": str(B)}
        for _ in range(3):
            await c.post("/t", headers=ha)
        assert (await c.post("/t", headers=ha)).status_code == 429
        assert (await c.post("/t", headers=hb)).status_code == 200


async def test_buckets_are_independent(rl_app):
    async with _client(rl_app) as c:
        h = {"x-acct": str(A)}
        for _ in range(3):
            await c.post("/t", headers=h)
        assert (await c.post("/a", headers=h)).status_code == 200


async def test_public_bucket_keys_by_ip(rl_app):
    async with _client(rl_app, "1.1.1.1") as c1, _client(rl_app, "2.2.2.2") as c2:
        # no auth header: the public bucket must not require an account
        assert [(await c1.post("/p")).status_code for _ in range(3)] == [200, 200, 429]
        assert (await c2.post("/p")).status_code == 200


async def test_concurrent_requests_never_over_admit(rl_app):
    async with _client(rl_app) as c:
        h = {"x-acct": str(A)}
        results = await asyncio.gather(*[c.post("/t", headers=h) for _ in range(12)])
    codes = sorted(r.status_code for r in results)
    assert codes == [200, 200] + [429] * 10


async def test_windows_are_utc_aligned(rl_app, pg_url):
    async with _client(rl_app) as c:
        await c.post("/t", headers={"x-acct": str(A)})
        await c.post("/a", headers={"x-acct": str(A)})
    engine = create_async_engine(pg_url, poolclass=NullPool)
    async with engine.connect() as conn:
        rows = (
            await conn.execute(text("select bucket, window_start, count from rate_limit_counters"))
        ).all()
    await engine.dispose()
    by = {r.bucket: r for r in rows}
    day = by["label_scans"].window_start.astimezone(UTC)
    assert (day.hour, day.minute, day.second) == (0, 0, 0)
    hour = by["analyze"].window_start.astimezone(UTC)
    assert (hour.minute, hour.second) == (0, 0)
    assert by["label_scans"].count == 1


async def test_consume_n(db_session):
    """`consume(n=...)` counts each created row of a batch (Plan 11 Task 6)."""
    from app.core.errors import ApiError
    from app.core.ratelimit import consume

    settings = Settings(_env_file=None, environment="test", rate_limit_meal_logs_per_day=5)
    key = uuid.uuid4()
    await consume(db_session, settings, account_id=key, bucket="meal_logs", n=3)
    await consume(db_session, settings, account_id=key, bucket="meal_logs", n=2)  # exactly 5
    with pytest.raises(ApiError) as exc:
        await consume(db_session, settings, account_id=key, bucket="meal_logs")
    assert exc.value.status == 429 and exc.value.code == "rate_limited"
    count = await db_session.scalar(
        text("select count from rate_limit_counters where key = :k and bucket = 'meal_logs'"),
        {"k": f"acct:{key}"},
    )
    assert count == 6
    other = uuid.uuid4()
    with pytest.raises(ApiError):  # 6 in one go is over a limit of 5
        await consume(db_session, settings, account_id=other, bucket="meal_logs", n=6)
    with pytest.raises(ValueError):
        await consume(db_session, settings, account_id=other, bucket="meal_logs", n=0)
