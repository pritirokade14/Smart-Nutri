"""Plan 8 Task 1: the consent gate on processing routes, withdrawal and re-consent (F11)."""

from collections.abc import Iterable
from uuid import UUID, uuid4

import pytest
from sqlalchemy import text

from app.core.consent import REQUIRED, gate_for
from app.core.security import AccountContext, current_account
from app.db.session import get_session
from app.features.consents.models import Consent
from app.features.consents.policy import CURRENT_VERSIONS
from app.features.me.service import ensure_account
from app.main import CONSENT_GATES
from tests.api.routes import api_routes

ACC = UUID("11111111-1111-1111-1111-111111111111")
ALL = ("terms", "health_data", "ai_processing")


@pytest.fixture
def login(app, db_session):
    def _login(account_id: UUID = ACC) -> None:
        app.dependency_overrides[get_session] = lambda: db_session
        app.dependency_overrides[current_account] = lambda: AccountContext(account_id, None)

    return _login


@pytest.fixture
def grant(db_session):
    async def _grant(purposes: Iterable[str] = ALL, version: str | None = None) -> None:
        await ensure_account(db_session, AccountContext(ACC, None))
        for purpose in purposes:
            db_session.add(
                Consent(
                    account_id=ACC, purpose=purpose, version=version or CURRENT_VERSIONS[purpose]
                )
            )
        await db_session.flush()

    return _grant


async def _analyze(client):
    return await client.post("/v1/analyze", json={"product_id": str(uuid4())})


def _consent_error(r) -> list[str]:
    assert r.status_code == 403, r.text
    err = r.json()["error"]
    assert err["code"] == "consent_required"
    assert err["message_key"] == "error.consent_required"
    return err["details"]["purposes"]


async def test_analyze_without_health_consent_403_lists_purposes(client, login, grant):
    await grant(["terms"])
    login()
    assert _consent_error(await _analyze(client)) == ["health_data"]


async def test_analyze_with_no_consents_lists_every_missing_purpose(client, login):
    login()
    assert _consent_error(await _analyze(client)) == ["terms", "health_data"]


async def test_scan_needs_ai_processing_consent(client, login, grant):
    await grant(["terms", "health_data"])
    login()
    r = await client.post("/v1/scans/upload-url", json={"ext": "jpg"})
    assert _consent_error(r) == ["ai_processing"]
    r = await client.post("/v1/scans/label", json={"path": f"{ACC}/{uuid4()}.jpg"})
    assert _consent_error(r) == ["ai_processing"]


async def test_old_version_requires_reconsent(client, login, grant):
    await grant(ALL, version="2020-01-01")
    login()
    assert _consent_error(await _analyze(client)) == ["terms", "health_data"]


async def test_withdraw_then_analyze_403(client, login, grant):
    await grant(ALL)
    login()
    r = await _analyze(client)
    assert r.status_code == 404  # past the gate: the random product does not exist
    body = {"purpose": "health_data", "version": CURRENT_VERSIONS["health_data"], "granted": False}
    assert (await client.post("/v1/consents", json=body)).status_code == 200
    assert _consent_error(await _analyze(client)) == ["health_data"]


async def test_withdraw_accepts_an_old_version(client, login, grant):
    await grant(["health_data"], version="2020-01-01")
    login()
    body = {"purpose": "health_data", "version": "2020-01-01", "granted": False}
    r = await client.post("/v1/consents", json=body)
    assert r.status_code == 200
    state = {s["purpose"]: s for s in r.json()}["health_data"]
    assert state["granted"] is False and state["needs_update"] is False


async def test_get_consents_reports_needs_update(client, login, grant):
    await grant(["health_data"], version="2020-01-01")
    await grant(["terms"])
    login()
    states = {s["purpose"]: s for s in (await client.get("/v1/consents")).json()}
    assert states["health_data"]["needs_update"] is True
    assert states["health_data"]["granted"] is False
    assert states["health_data"]["version"] == "2020-01-01"
    assert states["terms"]["needs_update"] is False and states["terms"]["granted"] is True
    # Never granted: nothing to update, the client asks for a first grant instead.
    assert states["ai_processing"]["needs_update"] is False


async def test_consent_rows_are_append_only(client, login, grant, db_session):
    await grant(["health_data"])
    login()
    body = {"purpose": "health_data", "version": CURRENT_VERSIONS["health_data"], "granted": False}
    await client.post("/v1/consents", json=body)
    await client.post("/v1/consents", json=body)  # a second withdrawal adds nothing
    rows = (
        await db_session.execute(
            text(
                "select version, granted_at, withdrawn_at from consents "
                "where account_id = :a order by coalesce(withdrawn_at, granted_at)"
            ),
            {"a": ACC},
        )
    ).all()
    assert len(rows) == 2
    grant_row, withdrawal = rows
    assert grant_row.withdrawn_at is None  # the original grant is never updated
    assert withdrawal.withdrawn_at is not None
    assert withdrawal.granted_at == grant_row.granted_at  # names the grant it withdraws
    assert withdrawal.version == grant_row.version


async def test_gate_runs_before_the_rate_limit(client, login, db_session):
    login()
    await _analyze(client)
    count = (await db_session.execute(text("select count(*) from rate_limit_counters"))).scalar()
    assert count == 0


async def test_gate_requires_auth(client):
    r = await _analyze(client)
    assert r.status_code == 401


def test_required_purposes_match_the_plan():
    assert REQUIRED == {
        "analyze": ("terms", "health_data"),
        "scans": ("terms", "health_data", "ai_processing"),
        "voice": ("terms", "health_data", "ai_processing"),
        "meals": ("terms", "health_data"),
    }
    assert set(CONSENT_GATES.values()) == set(REQUIRED)


def test_every_route_under_a_gated_prefix_has_the_gate(app):
    gated = 0
    for route in api_routes(app):
        for prefix, feature in CONSENT_GATES.items():
            if route.path == prefix or route.path.startswith(prefix + "/"):
                # First, so it runs before limit() and costs no quota.
                assert route.top_level_calls()[0] is gate_for(feature), route.path
                gated += 1
    assert gated >= 3  # analyze_create, scans upload-url and label (voice/meals when added)


def test_gated_operations_document_403(app):
    paths = app.openapi()["paths"]
    for path in ("/v1/analyze", "/v1/scans/upload-url", "/v1/scans/label"):
        op = paths[path]["post"]
        assert "403" in op["responses"], path
