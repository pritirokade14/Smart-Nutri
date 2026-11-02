from collections.abc import AsyncIterator

from fastapi import Request
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.core.config import Settings

# Per process. The API runs on Cloud Run with up to 3 instances against the Supabase session
# pooler, which holds one Postgres connection per client and has a small client limit shared
# with migrations and the dashboard. Budget: 3 instances x (3 + 2) = 15 connections at most.
# Raise these only together with the pooler size / max instances.
POOL_SIZE = 3
MAX_OVERFLOW = 2
POOL_TIMEOUT_S = 10
CONNECT_TIMEOUT_S = 5


def build_engine(settings: Settings) -> AsyncEngine:
    """Create (without connecting) the engine for these settings. Owned by the app."""
    return create_async_engine(
        settings.database_url.get_secret_value(),
        hide_parameters=True,
        pool_pre_ping=True,
        pool_size=POOL_SIZE,
        max_overflow=MAX_OVERFLOW,
        pool_timeout=POOL_TIMEOUT_S,
        connect_args={"connect_timeout": CONNECT_TIMEOUT_S},
    )


def build_sessionmaker(engine: AsyncEngine) -> async_sessionmaker[AsyncSession]:
    return async_sessionmaker(engine, expire_on_commit=False)


async def get_session(request: Request) -> AsyncIterator[AsyncSession]:
    async with request.app.state.sessionmaker() as session:
        yield session
