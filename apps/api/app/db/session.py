from collections.abc import AsyncIterator
from functools import cache

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.core.config import get_settings

POOL_SIZE = 5
MAX_OVERFLOW = 5
POOL_TIMEOUT_S = 10
CONNECT_TIMEOUT_S = 5


@cache
def get_engine() -> AsyncEngine:
    url = get_settings().database_url.get_secret_value()
    return create_async_engine(
        url,
        pool_pre_ping=True,
        pool_size=POOL_SIZE,
        max_overflow=MAX_OVERFLOW,
        pool_timeout=POOL_TIMEOUT_S,
        connect_args={"connect_timeout": CONNECT_TIMEOUT_S},
    )


@cache
def _sessionmaker() -> async_sessionmaker[AsyncSession]:
    return async_sessionmaker(get_engine(), expire_on_commit=False)


async def get_session() -> AsyncIterator[AsyncSession]:
    async with _sessionmaker()() as session:
        yield session
