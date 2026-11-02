import httpx
import pytest

from app.core.config import Settings
from app.main import create_app


@pytest.fixture
def app():
    return create_app(Settings(environment="test", allowed_origins=["http://localhost:3000"]))


@pytest.fixture
async def client(app):
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://t") as c:
        yield c
