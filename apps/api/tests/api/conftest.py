from collections.abc import AsyncIterator

import pytest
from sqlalchemy.ext.asyncio import AsyncConnection, AsyncSession

from tests.db.conftest import alembic_cfg, db, migrated, pg_url  # noqa: F401  (shared DB fixtures)


@pytest.fixture
async def db_session(db: AsyncConnection) -> AsyncIterator[AsyncSession]:  # noqa: F811
    """A session on the rolled-back test connection (superuser, so it bypasses RLS like the API)."""
    async with AsyncSession(
        bind=db, expire_on_commit=False, join_transaction_mode="create_savepoint"
    ) as session:
        yield session
