"""Plan 8 Task 1: the consent gate on processing routes, withdrawal and re-consent (F11).

Scope is ruling G1 (the user's decision, wave 2 integration): analyze, scans, meals and
products_create need only `terms`; voice needs `terms` and `ai_processing`. Saving member health
fields keeps the members `health_data` check, and the analyze explanation keeps its own
`ai_processing` check.
"""

from collections.abc import Iterable
from typing import get_args
from uuid import UUID, uuid4

import pytest
from pydantic import BaseModel
from sqlalchemy import text

from app.core.consent import REQUIRED, gate_for
from app.core.security import AccountContext, current_account
from app.db.session import get_session
from app.features.consents.models import Consent
from app.features.consents.policy import CURRENT_VERSIONS
from app.features.me.service import ensure_account
from app.features.members.models import Member
from app.features.products.router import search_consent_gate, search_loads_member
from app.main import CONSENT_GATES, PRE_GATE_DEPENDENCIES
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


async def test_voice_needs_terms_and_ai_processing(app, client, login, grant):
    app.state.settings.voice_enabled = True
    login()
    assert _consent_error(await client.post("/v1/voice/ask")) == ["terms", "ai_processing"]
    await grant(["terms", "health_data"])
    assert _consent_error(await client.post("/v1/voice/ask")) == ["ai_processing"]


async def test_voice_disabled_wins_over_the_consent_gate(app, client, login, db_session):
    """m1: with VOICE_ENABLED off, voice answers 503 ai_unavailable before the consent gate,
    so nobody is sent to a consent screen for a feature that is switched off."""
    app.state.settings.voice_enabled = False
    login()  # no consents at all
    r = await client.post("/v1/voice/ask")
    assert (r.status_code, r.json()["error"]["code"]) == (503, "ai_unavailable")
    # The gate never ran: it would have created no rows either, but it reads the session.
    count = await db_session.scalar(text("select count(*) from rate_limit_counters"))
    assert count == 0


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
        "product_verdicts": ("terms",),
        "voice": ("terms", "ai_processing"),
        "targets": ("terms", "health_data"),
        "targets_prefs": ("terms",),
        "meal_slots": ("terms",),
        "diary": ("terms",),
        "foods": ("terms",),
        "custom_foods": ("terms",),
        "recipes": ("terms",),
        "favourites": ("terms",),
        "weights": ("terms", "health_data"),
        "weights_erase": ("terms",),
    }
    # products_create and product_verdicts are gated on their routes only: a /v1/products
    # prefix gate would 401 the public /v1/products/{barcode}/public page.
    # The targets and weights routes carry their gate on each route (delete, display and the
    # weigh-in erase need only terms).
    route_only = {
        "products_create",
        "product_verdicts",
        "targets",
        "targets_prefs",
        "weights",
        "weights_erase",
    }
    assert set(CONSENT_GATES.values()) == set(REQUIRED) - route_only
    assert "/v1/products" not in CONSENT_GATES


# Routes under /v1/products with a route-level gate, and which one (I3: alternatives and
# compare return rules-engine statuses, for a member when member_id is given).
PRODUCT_GATES = {
    ("/v1/products", "POST"): "products_create",
    ("/v1/products/{product_id}/alternatives", "GET"): "product_verdicts",
    ("/v1/products/barcode/{code}/alternatives", "GET"): "product_verdicts",
    ("/v1/products/compare", "GET"): "product_verdicts",
}
# Search is gated only when member_id is given (Plan 9 integration): plain search returns no
# member statuses and stays open to anyone signed in.
PRODUCT_MEMBER_GATES = {("/v1/products/search", "GET"): "product_verdicts"}


def test_product_routes_gated_exactly_as_listed(app):
    gates = {gate_for(f): f for f in REQUIRED}
    gated = {}
    for route in api_routes(app):
        if not (route.path == "/v1/products" or route.path.startswith("/v1/products/")):
            continue
        found = [gates[c] for c in route.calls() if c in gates]
        if found:
            assert len(found) == 1, route.path
            for method in route.methods:
                gated[(route.path, method)] = found[0]
            # First, so it runs before limit() and costs no quota.
            assert route.top_level_calls()[0] is gate_for(found[0]), route.path
    assert gated == PRODUCT_GATES


def test_search_gate_is_the_conditional_gate(app):
    found = {}
    for route in api_routes(app):
        if search_consent_gate in route.calls():
            for method in route.methods:
                found[(route.path, method)] = "product_verdicts"
            assert not {gate_for(f) for f in REQUIRED} & route.calls(), route.path
            assert route.top_level_calls()[0] is search_consent_gate, route.path
    assert found == PRODUCT_MEMBER_GATES


def test_search_loads_member_predicate():
    from app.features.products.schemas import SearchSort

    assert not search_loads_member(None, SearchSort.RELEVANCE)
    assert search_loads_member(uuid4(), SearchSort.RELEVANCE)
    assert search_loads_member(None, SearchSort.PROTEIN)


def test_every_route_that_loads_a_member_is_gated(app):
    """Explicit member id or the primary member: any handler calling `_member_or_primary`
    (or reading the primary member) must carry a gate or the conditional search gate."""
    import inspect

    gates = {gate_for(f) for f in REQUIRED} | {search_consent_gate}
    seen = 0
    for route in api_routes(app):
        src = inspect.getsource(route.dependant.call)
        # Managing the member profile itself stays open (see MEMBER_ROUTES_WITHOUT_GATE).
        if route.path.startswith(("/v1/members", "/v1/me")):
            continue
        if "_member_or_primary(" in src or "get_or_create_primary(" in src:
            seen += 1
            assert gates & route.calls(), f"{route.path} loads a member, no gate"
    assert seen >= 1


async def test_search_without_member_id_needs_no_consent(client, login, grant):
    await grant([])
    login()
    r = await client.get("/v1/products/search?q=biscuit")
    assert r.status_code == 200, r.text


async def test_search_protein_sort_without_member_id_needs_terms(client, login, grant):
    await grant([])
    login()
    r = await client.get("/v1/products/search?q=biscuit&sort=protein")
    assert _consent_error(r) == ["terms"]
    await grant(["terms"])
    r = await client.get("/v1/products/search?q=biscuit&sort=protein")
    assert r.status_code != 403, r.text


async def test_search_with_member_id_needs_terms(client, login, grant):
    await grant([])
    login()
    r = await client.get(f"/v1/products/search?q=biscuit&member_id={uuid4()}")
    assert _consent_error(r) == ["terms"]
    await grant(["terms"])
    r = await client.get(f"/v1/products/search?q=biscuit&member_id={uuid4()}")
    assert r.status_code == 404, r.text  # past the gate: the member does not exist


@pytest.mark.parametrize(
    "path",
    [
        f"/v1/products/{uuid4()}/alternatives",
        "/v1/products/barcode/8901234567890/alternatives",
        f"/v1/products/compare?a={uuid4()}&b={uuid4()}",
    ],
)
async def test_alternatives_and_compare_need_terms(client, login, grant, path):
    login()
    assert _consent_error(await client.get(path)) == ["terms"]
    assert _consent_error(
        await client.get(f"{path}{'&' if '?' in path else '?'}member_id={uuid4()}")
    ) == ["terms"]


async def test_alternatives_and_compare_past_the_gate_with_terms(client, login, grant):
    await grant(["terms"])
    login()
    # Past the gate: a random product id or member is simply not found.
    r = await client.get(f"/v1/products/{uuid4()}/alternatives")
    assert r.status_code == 404, r.text
    r = await client.get(f"/v1/products/compare?a={uuid4()}&b={uuid4()}&member_id={uuid4()}")
    assert r.status_code == 404, r.text


def test_every_route_under_a_gated_prefix_has_the_gate(app):
    gated = 0
    for route in api_routes(app):
        for prefix, feature in CONSENT_GATES.items():
            if route.path == prefix or route.path.startswith(prefix + "/"):
                # Right after the session-free pre-gate checks (m1: the voice switch), so it
                # runs before limit() and costs no quota.
                pre = list(PRE_GATE_DEPENDENCIES.get(prefix, ()))
                calls = route.top_level_calls()
                assert calls[: len(pre)] == pre, route.path
                assert calls[len(pre)] is gate_for(feature), route.path
                gated += 1
    assert gated >= 3  # analyze_create, scans upload-url and label (voice/meals when added)


def test_voice_switch_runs_before_the_consent_gate(app):
    from app.features.voice.router import require_voice_enabled

    assert PRE_GATE_DEPENDENCIES == {"/v1/voice": (require_voice_enabled,)}
    (route,) = [r for r in api_routes(app) if r.path == "/v1/voice/ask"]
    calls = route.top_level_calls()
    assert calls[0] is require_voice_enabled and calls[1] is gate_for("voice")
    # Listed once more on the route itself (for the contract and for routers mounted
    # without the gate); FastAPI's per-request dependency cache runs it only once.
    assert calls.count(require_voice_enabled) == 2


def test_gated_operations_document_403(app):
    paths = app.openapi()["paths"]
    for path in ("/v1/analyze", "/v1/scans/upload-url", "/v1/scans/label", "/v1/products"):
        op = paths[path]["post"]
        assert "403" in op["responses"], path
    for path, _ in {**PRODUCT_GATES, **PRODUCT_MEMBER_GATES}:
        for op in paths[path].values():
            assert "403" in op["responses"], path


# --- I3: every route that takes a member id is consent-gated -----------------------------------

MEMBER_PARAMS = {"member_id", "member_ids"}
# Routes that take a member id without a route gate, and why.
MEMBER_ROUTES_WITHOUT_GATE = {
    # Managing the member profile itself. Its health fields need `health_data` consent in
    # members/service; reading and deleting a member must keep working after a withdrawal, so
    # people can see and erase their own data (ADR 0018).
    ("/v1/members/{member_id}", "GET"),
    ("/v1/members/{member_id}", "PATCH"),
    ("/v1/members/{member_id}", "DELETE"),
}


def _models(annotation) -> list[type[BaseModel]]:
    if isinstance(annotation, type) and issubclass(annotation, BaseModel):
        return [annotation]
    return [m for arg in get_args(annotation) for m in _models(arg)]


def _param_names(dependant) -> set[str]:
    """Every path, query, header, cookie and body parameter name (and body model field)."""
    names: set[str] = set()
    stack = [dependant]
    while stack:
        dep = stack.pop()
        for param in (
            *dep.path_params,
            *dep.query_params,
            *dep.header_params,
            *dep.cookie_params,
            *dep.body_params,
        ):
            names.update({param.name, param.alias})
            for model in _models(param.field_info.annotation):
                names.update(model.model_fields)
                names.update(f.alias for f in model.model_fields.values() if f.alias)
        stack.extend(dep.dependencies)
    return names


def test_every_route_taking_a_member_id_is_consent_gated(app):
    gates = {gate_for(f) for f in REQUIRED}
    with_member: set[tuple[str, str]] = set()
    for route in api_routes(app):
        if not MEMBER_PARAMS & _param_names(route.dependant):
            continue
        for method in route.methods:
            key = (route.path, method)
            with_member.add(key)
            if key in MEMBER_ROUTES_WITHOUT_GATE:
                continue
            assert (gates | {search_consent_gate}) & route.calls(), (
                f"{method} {route.path} takes a member id, no gate"
            )
    # The scan sees the routes it should (analyze body, voice form, meals and product queries).
    assert {
        ("/v1/analyze", "POST"),
        ("/v1/voice/ask", "POST"),
        ("/v1/meals", "GET"),
        ("/v1/products/compare", "GET"),
        ("/v1/products/{product_id}/alternatives", "GET"),
        ("/v1/products/search", "GET"),
    } <= with_member
    assert MEMBER_ROUTES_WITHOUT_GATE <= with_member  # no stale exemptions
