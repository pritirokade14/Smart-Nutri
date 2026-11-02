from uuid import UUID

from sqlalchemy import text

from app.core.security import AccountContext, current_account
from app.db.session import get_session

A = "11111111-1111-1111-1111-111111111111"


def _login(app, db_session, email="priya@example.com"):
    app.dependency_overrides[current_account] = lambda: AccountContext(UUID(A), email)
    app.dependency_overrides[get_session] = lambda: db_session


async def test_first_call_creates_account(app, client, db_session):
    _login(app, db_session)
    r = await client.get("/v1/me")
    assert r.status_code == 200
    body = r.json()
    assert body["display_name"] == "priya" and body["language"] == "en"
    assert body["id"] == A and body["email"] == "priya@example.com"
    assert body["created_at"]


async def test_second_call_is_idempotent(app, client, db_session):
    _login(app, db_session)
    r1 = await client.get("/v1/me")
    r2 = await client.get("/v1/me")
    assert r1.json() == r2.json()
    count = (await db_session.execute(text("select count(*) from accounts"))).scalar_one()
    assert count == 1


async def test_existing_display_name_is_not_overwritten(app, client, db_session):
    await db_session.execute(
        text("insert into accounts (id, display_name) values (:i, 'Custom')"), {"i": A}
    )
    _login(app, db_session)
    assert (await client.get("/v1/me")).json()["display_name"] == "Custom"


async def test_missing_email_leaves_display_name_null(app, client, db_session):
    _login(app, db_session, email=None)
    body = (await client.get("/v1/me")).json()
    assert body["display_name"] is None and body["email"] is None


async def test_me_requires_auth(client):
    r = await client.get("/v1/me")
    assert (r.status_code, r.json()["error"]["code"]) == (401, "auth_required")
    assert r.headers["www-authenticate"] == "Bearer"
