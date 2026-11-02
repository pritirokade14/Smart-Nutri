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
