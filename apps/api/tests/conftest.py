import httpx
import pytest

from app.core.config import Settings, get_settings
from app.main import create_app


@pytest.fixture(autouse=True)
def _isolate_settings(monkeypatch):
    """Tests must never read the real apps/api/.env."""
    monkeypatch.setitem(Settings.model_config, "env_file", None)
    get_settings.cache_clear()
    yield
    get_settings.cache_clear()


@pytest.fixture
def app():
    return create_app(
        Settings(_env_file=None, environment="test", allowed_origins=["http://localhost:3000"])
    )


@pytest.fixture
async def client(app):
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://t") as c:
        yield c
