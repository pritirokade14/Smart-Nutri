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


async def test_current_account_row_creates_row_for_new_account(app, client, db_session):
    """Any route writing account-owned rows depends on current_account_row (FK to accounts)."""
    from typing import Annotated

    from fastapi import Depends

    from app.features.me.dependencies import CurrentAccount, current_account_row

    seen = []

    @app.post("/v1/probe-write")
    async def _(current: Annotated[CurrentAccount, Depends(current_account_row)]):
        seen.append(current)
        # A write that needs the account row (FK members.account_id -> accounts.id).
        await db_session.execute(
            text("insert into members (account_id, name, relation) values (:a, 'x', 'self')"),
            {"a": current.account.id},
        )
        return {"id": str(current.account.id)}

    _login(app, db_session)
    before = (await db_session.execute(text("select count(*) from accounts"))).scalar_one()
    assert before == 0
    r = await client.post("/v1/probe-write")
    assert (r.status_code, r.json()) == (200, {"id": A})
    assert seen[0].ctx == AccountContext(UUID(A), "priya@example.com")
    assert seen[0].account.display_name == "priya"
    rows = (await db_session.execute(text("select id from accounts"))).scalars().all()
    assert [str(i) for i in rows] == [A]


async def test_current_account_row_requires_auth(app, client):
    from typing import Annotated

    from fastapi import Depends

    from app.features.me.dependencies import CurrentAccount, current_account_row

    @app.post("/v1/probe-write-2")
    async def _(current: Annotated[CurrentAccount, Depends(current_account_row)]):
        return {}

    r = await client.post("/v1/probe-write-2")
    assert (r.status_code, r.json()["error"]["code"]) == (401, "auth_required")


async def test_me_requires_auth(client):
    r = await client.get("/v1/me")
    assert (r.status_code, r.json()["error"]["code"]) == (401, "auth_required")
    assert r.headers["www-authenticate"] == "Bearer"
