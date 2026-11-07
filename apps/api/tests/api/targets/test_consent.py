"""Consent mapping for the targets routes (Plan 10 Task 4, Ruling D16, ADR 0022)."""

import pytest

from app.core.consent import REQUIRED, gate_for
from tests.api.routes import api_routes
from tests.api.targets.conftest import ACC_A, ACC_B, G1_SETTINGS, URL

S = f"{URL}/settings"


def _err(r) -> dict:
    return r.json()["error"]


def test_required_purposes():
    assert REQUIRED["targets"] == ("terms", "health_data")
    assert REQUIRED["targets_prefs"] == ("terms",)


@pytest.mark.parametrize(
    ("method", "path", "kwargs"),
    [
        ("get", URL, {}),
        ("put", S, {"json": G1_SETTINGS}),
        ("post", f"{URL}/preview", {"json": G1_SETTINGS}),
        ("get", S, {}),
    ],
)
async def test_targets_routes_need_health_data(client, login, grant, method, path, kwargs):
    await grant(ACC_B, ["terms"])
    login(ACC_B)
    r = await getattr(client, method)(path, **kwargs)
    assert r.status_code == 403, r.text
    assert _err(r)["code"] == "consent_required"
    assert _err(r)["details"]["purposes"] == ["health_data"]


async def test_no_consent_at_all_lists_both(client, login, grant):
    await grant(ACC_B, [])
    login(ACC_B)
    r = await client.get(URL)
    assert _err(r)["details"]["purposes"] == ["terms", "health_data"]


async def test_delete_and_display_need_only_terms(client, login, grant):
    await grant(ACC_B, ["terms"])
    login(ACC_B)
    assert (await client.delete(S)).status_code == 204
    r = await client.put(f"{URL}/display", json={"numbers_display": "hide_all"})
    assert r.status_code == 404  # past the gate: there are no settings
    assert _err(r)["code"] == "goal_settings_not_found"


async def test_delete_without_terms_is_refused(client, login, grant):
    await grant(ACC_B, [])
    login(ACC_B)
    r = await client.delete(S)
    assert r.status_code == 403 and _err(r)["details"]["purposes"] == ["terms"]


async def test_gate_runs_before_the_rate_limit(client, login, grant, app):
    await grant(ACC_B, ["terms"])
    login(ACC_B)
    app.state.settings.rate_limit_diary_settings_per_day = 1
    for _ in range(3):
        r = await client.put(S, json=G1_SETTINGS)
        assert r.status_code == 403 and _err(r)["code"] == "consent_required"  # never 429


def test_every_targets_route_lists_the_gate_first(app):
    routes = [r for r in api_routes(app) if r.path.startswith("/v1/targets")]
    assert len(routes) == 6
    gates = {gate_for("targets"): "targets", gate_for("targets_prefs"): "targets_prefs"}
    seen = {}
    for route in routes:
        first = route.top_level_calls()[0]
        assert first in gates, route.path
        for method in route.methods:
            seen[(route.path, method)] = gates[first]
    assert seen == {
        ("/v1/targets", "GET"): "targets",
        ("/v1/targets/settings", "GET"): "targets",
        ("/v1/targets/settings", "PUT"): "targets",
        ("/v1/targets/preview", "POST"): "targets",
        ("/v1/targets/settings", "DELETE"): "targets_prefs",
        ("/v1/targets/display", "PUT"): "targets_prefs",
    }


def test_operation_ids(app):
    ids = {
        (path, method): op["operationId"]
        for path, item in app.openapi()["paths"].items()
        if path.startswith("/v1/targets")
        for method, op in item.items()
    }
    assert ids == {
        ("/v1/targets", "get"): "targets_get",
        ("/v1/targets/settings", "get"): "targets_settings_get",
        ("/v1/targets/settings", "put"): "targets_settings_put",
        ("/v1/targets/settings", "delete"): "targets_settings_delete",
        ("/v1/targets/preview", "post"): "targets_preview",
        ("/v1/targets/display", "put"): "targets_display_put",
    }


async def test_withdrawal_keeps_stored_settings(client, g1, db_session):
    from sqlalchemy import select

    from app.features.targets.models import DiaryGoalSettings

    await client.put(S, json=G1_SETTINGS)
    r = await client.post(
        "/v1/consents", json={"purpose": "health_data", "version": "2026-11-01", "granted": False}
    )
    assert r.status_code == 200
    assert (await client.get(URL)).status_code == 403  # processing stopped
    rows = (await db_session.scalars(select(DiaryGoalSettings))).all()
    assert len(rows) == 1 and rows[0].account_id == ACC_A  # nothing erased
    await client.post(
        "/v1/consents", json={"purpose": "health_data", "version": "2026-11-01", "granted": True}
    )
    t = (await client.get(URL)).json()
    assert t["status"] == "ready" and t["energy_kcal"] == 2760  # resumes on re-consent
