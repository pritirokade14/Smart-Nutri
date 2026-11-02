from sqlalchemy.ext.asyncio import AsyncEngine
from starlette.testclient import TestClient

from app.core.config import Settings
from app.core.errors import ApiError
from app.main import create_app


def _settings(url: str) -> Settings:
    return Settings(_env_file=None, environment="test", database_url=url)


def test_engine_is_built_from_the_given_settings():
    url = "postgresql+psycopg://u:p@db.example.invalid:6543/custom"
    app = create_app(_settings(url))
    assert app.state.engine.url.render_as_string(hide_password=False) == url


def test_two_apps_get_independent_engines():
    a = create_app(_settings("postgresql+psycopg://u:p@h1.invalid/a"))
    b = create_app(_settings("postgresql+psycopg://u:p@h2.invalid/b"))
    assert a.state.engine is not b.state.engine
    assert b.state.engine.url.host == "h2.invalid"


def test_engine_disposed_on_shutdown(monkeypatch):
    disposed = []
    real = AsyncEngine.dispose

    async def spy(self, *a, **kw):
        disposed.append(self)
        return await real(self, *a, **kw)

    monkeypatch.setattr(AsyncEngine, "dispose", spy)
    app = create_app(_settings("postgresql+psycopg://u:p@h.invalid/x"))
    with TestClient(app):
        assert disposed == []
    assert disposed == [app.state.engine]


async def test_api_error_can_carry_headers(app, client):
    @app.get("/hdr")
    async def _():
        raise ApiError("nope", 401, headers={"WWW-Authenticate": "Bearer"})

    r = await client.get("/hdr")
    assert r.status_code == 401 and r.headers["www-authenticate"] == "Bearer"
