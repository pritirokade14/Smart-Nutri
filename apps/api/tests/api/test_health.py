import asyncio
import time

from app.db.schema import EXPECTED_ALEMBIC_HEAD
from app.db.session import get_session
from app.features.health import router as health_router


class _Result:
    def __init__(self, versions: list[str]) -> None:
        self._versions = versions

    def scalars(self):
        return self

    def all(self) -> list[str]:
        return self._versions


def _session(versions: list[str]):
    class S:
        async def execute(self, _):
            return _Result(versions)

    return S()


async def test_health_ok(app, client):
    app.dependency_overrides[get_session] = lambda: _session([EXPECTED_ALEMBIC_HEAD])
    r = await client.get("/v1/health")
    assert (r.status_code, r.json()) == (200, {"status": "ok", "database": "ok"})


async def test_health_schema_behind(app, client):
    app.dependency_overrides[get_session] = lambda: _session(["0000_older"])
    r = await client.get("/v1/health")
    assert (r.status_code, r.json()) == (
        503,
        {"status": "unavailable", "database": "schema_behind"},
    )


async def test_health_no_revision_is_schema_behind(app, client):
    app.dependency_overrides[get_session] = lambda: _session([])
    r = await client.get("/v1/health")
    assert (r.status_code, r.json()["database"]) == (503, "schema_behind")


async def test_health_db_down(app, client):
    class S:
        async def execute(self, _):
            raise OSError("down")

    app.dependency_overrides[get_session] = lambda: S()
    r = await client.get("/v1/health")
    assert (r.status_code, r.json()) == (503, {"status": "degraded", "database": "error"})


async def test_health_db_hang_times_out(app, client, monkeypatch):
    monkeypatch.setattr(health_router, "DB_CHECK_TIMEOUT_S", 0.2)

    class S:
        async def execute(self, _):
            await asyncio.sleep(10)

    app.dependency_overrides[get_session] = lambda: S()
    t = time.monotonic()
    r = await client.get("/v1/health")
    assert (r.status_code, r.json()) == (503, {"status": "degraded", "database": "error"})
    assert time.monotonic() - t < 3


def test_expected_head_matches_alembic_scripts():
    from alembic.config import Config
    from alembic.script import ScriptDirectory

    from tests.db.conftest import API_DIR

    cfg = Config(str(API_DIR / "alembic.ini"))
    assert EXPECTED_ALEMBIC_HEAD == ScriptDirectory.from_config(cfg).get_current_head()
    assert EXPECTED_ALEMBIC_HEAD
