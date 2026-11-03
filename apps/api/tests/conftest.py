import httpx
import pytest

from app.core.config import Settings, get_settings
from app.main import create_app


@pytest.fixture(autouse=True)
def _isolate_settings(monkeypatch):
    """Tests must never read the real apps/api/.env."""
    monkeypatch.setitem(Settings.model_config, "env_file", None)
    monkeypatch.delenv("SENTRY_DSN", raising=False)
    monkeypatch.delenv("POSTHOG_API_KEY", raising=False)
    get_settings.cache_clear()
    yield
    get_settings.cache_clear()


def _audio(fmt: str, seconds: float, *, silent: bool = False) -> bytes:
    from tests.audio import make_audio, require_ffmpeg

    require_ffmpeg()
    return make_audio(fmt, seconds, silent=silent)


@pytest.fixture
def wav3s() -> bytes:
    return _audio("wav", 3)


@pytest.fixture
def wav31s() -> bytes:
    return _audio("wav", 31)


@pytest.fixture
def m4a3s() -> bytes:
    return _audio("m4a", 3)


@pytest.fixture
def webm3s() -> bytes:
    return _audio("webm", 3)


@pytest.fixture
def ogg3s() -> bytes:
    return _audio("ogg", 3)


@pytest.fixture
def mp3_3s() -> bytes:
    return _audio("mp3", 3)


@pytest.fixture
def silent_wav3s() -> bytes:
    return _audio("wav", 3, silent=True)


@pytest.fixture
def app():
    return create_app(
        Settings(_env_file=None, environment="test", allowed_origins=["http://localhost:3000"])
    )


@pytest.fixture
async def client(app):
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://t") as c:
        yield c
