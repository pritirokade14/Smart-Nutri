"""The foods routes need `terms`, and the gate runs before the rate limiter (Plan 12 Task 4).
The real consent gate runs in this folder."""

from uuid import uuid4

import pytest
from sqlalchemy import text

from tests.api.foods.conftest import ACC_A, ACC_B

ROUTES = (
    ("GET", "/v1/foods/search?q=dal", None),
    ("GET", "/v1/foods/units", None),
    ("GET", f"/v1/foods/food/{uuid4()}", None),
    ("GET", "/v1/foods/off/8901063201089", None),
    ("PUT", f"/v1/foods/food/{uuid4()}/portions/roti", {"grams_per_unit": 30}),
    ("DELETE", f"/v1/foods/food/{uuid4()}/portions/roti", None),
)


@pytest.mark.parametrize(("method", "url", "body"), ROUTES)
async def test_foods_routes_need_terms(client, grant, login, method, url, body):
    await grant(ACC_B, ("health_data", "ai_processing"))  # everything but terms
    login(ACC_B)
    r = await client.request(method, url, json=body)
    assert r.status_code == 403, (method, url)
    assert r.json()["error"]["code"] == "consent_required"
    assert r.json()["error"]["details"]["purposes"] == ["terms"]


@pytest.mark.parametrize(("method", "url", "body"), ROUTES)
async def test_foods_routes_need_a_token(client, method, url, body):
    assert (await client.request(method, url, json=body)).status_code == 401


async def test_gate_before_rate_limit(client, grant, login, db_session, app, monkeypatch):
    monkeypatch.setattr(app.state.settings, "rate_limit_diary_writes_per_day", 1)
    monkeypatch.setattr(app.state.settings, "rate_limit_search_per_minute", 1)
    await grant(ACC_B, ("health_data",))
    login(ACC_B)
    for _ in range(3):
        assert (await client.get("/v1/foods/search?q=dal")).status_code == 403
        r = await client.put(f"/v1/foods/food/{uuid4()}/portions/roti", json={"grams_per_unit": 3})
        assert r.status_code == 403  # a refused call never turns into a 429
    used = await db_session.scalar(
        text("select count(*) from rate_limit_counters where key = :k"), {"k": f"acct:{ACC_B}"}
    )
    assert used == 0


async def test_search_uses_the_search_bucket(client, consented, seeded, app, monkeypatch):
    monkeypatch.setattr(app.state.settings, "rate_limit_search_per_minute", 1)
    assert (await client.get("/v1/foods/search?q=dal&kinds=food")).status_code == 200
    r = await client.get("/v1/foods/search?q=dal&kinds=food")
    assert r.status_code == 429 and r.json()["error"]["code"] == "rate_limited"


async def test_get_uses_the_product_lookups_bucket(client, consented, food_ids, app, monkeypatch):
    monkeypatch.setattr(app.state.settings, "rate_limit_product_lookups_per_hour", 1)
    assert (await client.get(f"/v1/foods/food/{food_ids['172437']}")).status_code == 200
    assert (await client.get(f"/v1/foods/food/{food_ids['172437']}")).status_code == 429


def test_foods_prefix_is_gated_on_terms():
    from app.core.consent import REQUIRED
    from app.main import CONSENT_GATES

    assert CONSENT_GATES["/v1/foods"] == "foods"
    assert REQUIRED["foods"] == ("terms",)


def test_acc_a_is_the_consented_account():
    assert ACC_A != ACC_B
