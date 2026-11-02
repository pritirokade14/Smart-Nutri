from app.db.session import get_session


async def test_health_ok(app, client):
    class S:
        async def execute(self, _):
            return None

    app.dependency_overrides[get_session] = lambda: S()
    r = await client.get("/v1/health")
    assert (r.status_code, r.json()) == (200, {"status": "ok", "database": "ok"})


async def test_health_db_down(app, client):
    class S:
        async def execute(self, _):
            raise OSError("down")

    app.dependency_overrides[get_session] = lambda: S()
    r = await client.get("/v1/health")
    assert (r.status_code, r.json()) == (503, {"status": "degraded", "database": "error"})


async def test_health_db_hang_times_out(app, client, monkeypatch):
    import asyncio
    import time

    from app.features.health import router as health_router

    monkeypatch.setattr(health_router, "DB_CHECK_TIMEOUT_S", 0.2)

    class S:
        async def execute(self, _):
            await asyncio.sleep(10)

    app.dependency_overrides[get_session] = lambda: S()
    t = time.monotonic()
    r = await client.get("/v1/health")
    assert (r.status_code, r.json()) == (503, {"status": "degraded", "database": "error"})
    assert time.monotonic() - t < 3
