"""/v1/health against a real Postgres: the schema must be at this build's Alembic head."""

from sqlalchemy import text

from app.db.schema import EXPECTED_ALEMBIC_HEAD
from app.db.session import get_session


async def test_head_matches_after_migrations(app, client, db_session):
    current = (
        await db_session.execute(text("select version_num from alembic_version"))
    ).scalar_one()
    assert current == EXPECTED_ALEMBIC_HEAD
    app.dependency_overrides[get_session] = lambda: db_session
    r = await client.get("/v1/health")
    assert (r.status_code, r.json()) == (200, {"status": "ok", "database": "ok"})


async def test_revision_mismatch_is_schema_behind(app, client, db_session):
    # Rolled back by the db fixture after the test.
    await db_session.execute(text("update alembic_version set version_num = 'x'"))
    app.dependency_overrides[get_session] = lambda: db_session
    r = await client.get("/v1/health")
    assert (r.status_code, r.json()) == (
        503,
        {"status": "unavailable", "database": "schema_behind"},
    )


async def test_missing_alembic_version_is_schema_behind(app, client, db_session):
    await db_session.execute(text("drop table alembic_version"))  # rolled back after the test
    app.dependency_overrides[get_session] = lambda: db_session
    r = await client.get("/v1/health")
    assert (r.status_code, r.json()) == (
        503,
        {"status": "unavailable", "database": "schema_behind"},
    )
