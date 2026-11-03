from uuid import UUID

from sqlalchemy import text

from app.core.security import AccountContext, current_account
from app.db.session import get_session
from app.features.consents.service import has_active_consent

ACC_A = UUID("11111111-1111-1111-1111-111111111111")
ACC_B = UUID("22222222-2222-2222-2222-222222222222")
V = "2026-11-01"


def _login(app, db_session, account=ACC_A):
    app.dependency_overrides[current_account] = lambda: AccountContext(account, "a@example.com")
    app.dependency_overrides[get_session] = lambda: db_session


def _body(purpose, granted, version=V):
    return {"purpose": purpose, "version": version, "granted": granted}


async def test_grant_then_list(app, client, db_session):
    _login(app, db_session)
    r = await client.post("/v1/consents", json=_body("health_data", True))
    assert r.status_code == 200
    states = {s["purpose"]: s for s in (await client.get("/v1/consents")).json()}
    assert states["health_data"]["granted"] is True
    assert states["health_data"]["version"] == V
    assert states["ai_processing"]["granted"] is False
    assert states["ai_processing"]["version"] is None
    assert states["ai_processing"]["current_version"] == V


async def test_withdraw_deactivates_and_keeps_history(app, client, db_session):
    _login(app, db_session)
    await client.post("/v1/consents", json=_body("health_data", True))
    assert await has_active_consent(db_session, ACC_A, ["health_data"]) is True
    r = await client.post("/v1/consents", json=_body("health_data", False))
    assert r.status_code == 200
    assert await has_active_consent(db_session, ACC_A, ["health_data"]) is False
    rows = (
        await db_session.execute(
            text("select withdrawn_at from consents where account_id = :a"), {"a": ACC_A}
        )
    ).all()
    assert len(rows) == 1 and rows[0][0] is not None  # history kept, not deleted


async def test_regrant_after_withdrawal_adds_new_row(app, client, db_session):
    _login(app, db_session)
    await client.post("/v1/consents", json=_body("health_data", True))
    await client.post("/v1/consents", json=_body("health_data", False))
    await client.post("/v1/consents", json=_body("health_data", True))
    assert await has_active_consent(db_session, ACC_A, "health_data") is True
    count = (await db_session.execute(text("select count(*) from consents"))).scalar_one()
    assert count == 2


async def test_grant_is_idempotent(app, client, db_session):
    _login(app, db_session)
    await client.post("/v1/consents", json=_body("terms", True))
    await client.post("/v1/consents", json=_body("terms", True))
    count = (await db_session.execute(text("select count(*) from consents"))).scalar_one()
    assert count == 1


async def test_has_active_consent_requires_all_purposes(app, client, db_session):
    _login(app, db_session)
    await client.post("/v1/consents", json=_body("health_data", True))
    assert await has_active_consent(db_session, ACC_A, ["health_data", "ai_processing"]) is False


async def test_old_version_grant_is_not_active(app, client, db_session):
    _login(app, db_session)
    await client.get("/v1/me")
    await db_session.execute(
        text(
            "insert into consents (account_id, purpose, version) values (:a, 'health_data', 'old')"
        ),
        {"a": ACC_A},
    )
    assert await has_active_consent(db_session, ACC_A, ["health_data"]) is False
    states = {s["purpose"]: s for s in (await client.get("/v1/consents")).json()}
    assert states["health_data"]["granted"] is False and states["health_data"]["version"] == "old"


async def test_wrong_version_rejected(app, client, db_session):
    _login(app, db_session)
    r = await client.post("/v1/consents", json=_body("terms", True, "old"))
    assert r.status_code == 422
    err = r.json()["error"]
    assert err["code"] == "consent_version_mismatch"
    assert err["message_key"] == "error.consent_version_mismatch"


async def test_unknown_purpose_rejected(app, client, db_session):
    _login(app, db_session)
    r = await client.post("/v1/consents", json=_body("marketing", True))
    assert r.status_code == 422 and r.json()["error"]["code"] == "validation_error"


async def test_accounts_are_isolated(app, client, db_session):
    _login(app, db_session, ACC_A)
    await client.post("/v1/consents", json=_body("health_data", True))
    _login(app, db_session, ACC_B)
    states = {s["purpose"]: s for s in (await client.get("/v1/consents")).json()}
    assert states["health_data"]["granted"] is False and states["health_data"]["version"] is None
    assert await has_active_consent(db_session, ACC_B, ["health_data"]) is False
    # B withdrawing must not touch A's consent.
    await client.post("/v1/consents", json=_body("health_data", False))
    assert await has_active_consent(db_session, ACC_A, ["health_data"]) is True


async def test_requires_auth(client):
    assert (await client.get("/v1/consents")).status_code == 401
    r = await client.post("/v1/consents", json=_body("terms", True))
    assert r.status_code == 401
