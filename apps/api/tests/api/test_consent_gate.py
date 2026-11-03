"""Plan 8 Task 1: the consent gate on processing routes, withdrawal and re-consent (F11).

Scope is ruling G1 (the user's decision, wave 2 integration): analyze, scans, meals and
products_create need only `terms`; voice needs `terms` and `ai_processing`. Saving member health
fields keeps the members `health_data` check, and the analyze explanation keeps its own
`ai_processing` check.
"""

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
from app.features.members.models import Member
from app.main import CONSENT_GATES
from scripts.export_fixture_responses import fixture_product_record
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


async def test_analyze_needs_only_terms(client, login, grant):
    await grant(["terms"])
    login()
    r = await _analyze(client)
    assert r.status_code == 404  # past the gate: the random product does not exist


async def test_analyze_with_no_consents_403_lists_terms(client, login):
    login()
    assert _consent_error(await _analyze(client)) == ["terms"]


async def test_scans_need_only_terms(client, login, grant):
    login()
    r = await client.post("/v1/scans/upload-url", json={"ext": "jpg"})
    assert _consent_error(r) == ["terms"]
    r = await client.post("/v1/scans/label", json={"path": f"{ACC}/{uuid4()}.jpg"})
    assert _consent_error(r) == ["terms"]
    await grant(["terms"])
    r = await client.post("/v1/scans/label", json={"path": "not-a-valid-path"})
    assert r.status_code != 403, r.text  # past the gate


async def test_meals_need_only_terms(client, login, grant):
    login()
    assert _consent_error(await client.post("/v1/meals", json={})) == ["terms"]
    await grant(["terms"])
    r = await client.post("/v1/meals", json={})
    assert r.status_code == 422, r.text  # past the gate: the body is invalid


async def test_voice_needs_terms_and_ai_processing(client, login, grant):
    login()
    assert _consent_error(await client.post("/v1/voice/ask")) == ["terms", "ai_processing"]
    await grant(["terms", "health_data"])
    assert _consent_error(await client.post("/v1/voice/ask")) == ["ai_processing"]


async def test_products_create_needs_terms(client, login, grant):
    login()
    assert _consent_error(await client.post("/v1/products", json={})) == ["terms"]
    await grant(["terms"])
    r = await client.post("/v1/products", json={})
    assert r.status_code == 422, r.text  # past the gate: the body is invalid


async def test_old_version_requires_reconsent(client, login, grant):
    await grant(ALL, version="2020-01-01")
    login()
    assert _consent_error(await _analyze(client)) == ["terms"]


async def test_withdraw_terms_then_analyze_403(client, login, grant):
    await grant(ALL)
    login()
    r = await _analyze(client)
    assert r.status_code == 404  # past the gate: the random product does not exist
    body = {"purpose": "terms", "version": CURRENT_VERSIONS["terms"], "granted": False}
    assert (await client.post("/v1/consents", json=body)).status_code == 200
    assert _consent_error(await _analyze(client)) == ["terms"]


async def test_withdrawn_health_data_still_protects_an_allergic_member(
    client, login, grant, db_session
):
    """Withdrawing health_data must not make analyze ignore stored allergies: dropping them
    would show `ok` to an allergic member. Withdrawal stops new health-field saves only."""
    await grant(ALL)
    db_session.add(
        Member(
            account_id=ACC,
            name="Peanut Allergic",
            relation="other",
            birth_year=1990,
            diet="non_veg",
            allergens=["peanut"],
        )
    )
    product = fixture_product_record("namkeen")
    db_session.add(product)
    await db_session.flush()
    login()
    body = {"purpose": "health_data", "version": CURRENT_VERSIONS["health_data"], "granted": False}
    assert (await client.post("/v1/consents", json=body)).status_code == 200
    r = await client.post("/v1/analyze", json={"product_id": str(product.id)})
    assert r.status_code == 200, r.text
    statuses = {v["member_name"]: v["status"] for v in r.json()["verdicts"]}
    assert statuses["Peanut Allergic"] == "avoid"


async def test_no_ai_processing_means_no_explanation_call(client, login, grant, db_session, app):
    """Plan 5's ai_processing check on the explanation survives the G1 gate: with only terms
    (and health_data) granted, analyze answers but never calls the LLM."""
    from app.integrations.callmissed import get_llm_provider

    class NoCallLLM:
        calls = 0

        async def chat_json(self, **kwargs):
            NoCallLLM.calls += 1
            raise AssertionError("the explanation must not call the LLM without consent")

        async def extract_label(self, **kwargs):  # pragma: no cover
            raise AssertionError("not used")

    app.dependency_overrides[get_llm_provider] = lambda: NoCallLLM()
    await grant(["terms", "health_data"])
    product = fixture_product_record("sf_biscuit")
    db_session.add(product)
    await db_session.flush()
    login()
    r = await client.post("/v1/analyze", json={"product_id": str(product.id)})
    assert r.status_code == 200, r.text
    assert r.json()["explanation"]["source"] == "unavailable"
    assert r.json()["explanation"]["text"] is None
    assert NoCallLLM.calls == 0


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


def test_required_purposes_match_ruling_g1():
    assert REQUIRED == {
        "analyze": ("terms",),
        "scans": ("terms",),
        "meals": ("terms",),
        "products_create": ("terms",),
        "voice": ("terms", "ai_processing"),
    }
    # products_create is gated on its route only: a /v1/products prefix gate would 401 the
    # public /v1/products/{barcode}/public page.
    assert set(CONSENT_GATES.values()) == set(REQUIRED) - {"products_create"}
    assert "/v1/products" not in CONSENT_GATES


def test_only_products_create_is_gated_under_products(app):
    gated = set()
    for route in api_routes(app):
        under_products = route.path == "/v1/products" or route.path.startswith("/v1/products/")
        if under_products and gate_for("products_create") in route.calls():
            gated.add((route.path, frozenset(route.methods)))
            # First, so it runs before limit() and costs no quota.
            assert route.top_level_calls()[0] is gate_for("products_create")
    assert gated == {("/v1/products", frozenset({"POST"}))}


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
    for path in ("/v1/analyze", "/v1/scans/upload-url", "/v1/scans/label", "/v1/products"):
        op = paths[path]["post"]
        assert "403" in op["responses"], path
