from datetime import UTC, datetime, timedelta
from uuid import uuid4

import pytest

from app.features.meals.service import snapshot
from app.scoring import Nutrients
from tests.api.meals.conftest import ACC_C, OFF_BARCODE, FakeOff

pytestmark = pytest.mark.usefixtures("family")


def _body(member, product=None, **kw):
    body = {"member_id": str(member)}
    if product is not None:
        body["product_id"] = str(product)
    return body | kw


# --- plan tests --------------------------------------------------------------------------


async def test_log_by_servings_snapshots(client, family, sf_biscuit_product_id):
    r = await client.post("/v1/meals", json=_body(family.me, sf_biscuit_product_id, servings=2))
    assert r.status_code == 201
    j = r.json()
    n = j["nutrients"]
    # 25 g serving x2; salt 0.9 -> 0.45 -> 0.5 (1 dp, ROUND_HALF_UP)
    assert (j["grams"], n["energy_kcal"], n["sugars_g"], n["salt_g"]) == (50, 225.0, 1.0, 0.5)
    assert (j["product_name"], j["grade"], j["attribution"]) == ("Sugar Free Biscuit", "D", None)


async def test_client_id_is_idempotent(client, family, sf_biscuit_product_id, db_session):
    body = _body(family.me, sf_biscuit_product_id, grams=30, client_id=str(uuid4()))
    a = await client.post("/v1/meals", json=body)
    b = await client.post("/v1/meals", json=body)
    assert (a.status_code, b.status_code) == (201, 200) and a.json()["id"] == b.json()["id"]
    listed = (await client.get(f"/v1/meals?member_id={family.me}")).json()
    assert [m["id"] for m in listed] == [a.json()["id"]]


async def test_portion_required(client, family, sf_biscuit_product_id):
    r = await client.post("/v1/meals", json=_body(family.me, sf_biscuit_product_id))
    assert r.status_code == 422 and r.json()["error"]["code"] == "portion_required"


async def test_foreign_member_404(client, family, other_account_member_id, sf_biscuit_product_id):
    r = await client.post(
        "/v1/meals", json=_body(other_account_member_id, sf_biscuit_product_id, grams=10)
    )
    assert r.status_code == 404 and r.json()["error"]["code"] == "member_not_found"


def test_snapshot_keeps_none():
    s = snapshot(Nutrients(energy_kcal=400, sugars_g=None), 50)
    assert (s.energy_kcal, s.sugars_g) == (200.0, None)


# --- more ---------------------------------------------------------------------------------


def test_snapshot_salt_from_sodium_and_drops_implausible():
    s = snapshot(Nutrients(sodium_mg=400, sugars_g=250, carbs_g=300), 100)
    assert (s.salt_g, s.sugars_g, s.carbs_g) == (1.0, None, None)


async def test_both_portions_is_portion_required(client, family, sf_biscuit_product_id):
    r = await client.post(
        "/v1/meals", json=_body(family.me, sf_biscuit_product_id, grams=10, servings=1)
    )
    assert r.status_code == 422 and r.json()["error"]["code"] == "portion_required"


async def test_servings_without_serving_size(client, family, db_session):
    from scripts.export_fixture_responses import fixture_product_record

    record = fixture_product_record("no_ingredients")  # serving_size_g is null
    db_session.add(record)
    await db_session.flush()
    r = await client.post("/v1/meals", json=_body(family.me, record.id, servings=1))
    assert r.status_code == 422 and r.json()["error"]["code"] == "serving_size_unknown"


@pytest.mark.parametrize("delta", [timedelta(minutes=10), timedelta(days=-31)])
async def test_eaten_at_out_of_range(client, family, sf_biscuit_product_id, delta):
    eaten = (datetime.now(UTC) + delta).isoformat()
    r = await client.post(
        "/v1/meals", json=_body(family.me, sf_biscuit_product_id, grams=10, eaten_at=eaten)
    )
    assert r.status_code == 422 and r.json()["error"]["code"] == "eaten_at_out_of_range"


async def test_naive_eaten_at_rejected(client, family, sf_biscuit_product_id):
    r = await client.post(
        "/v1/meals",
        json=_body(family.me, sf_biscuit_product_id, grams=10, eaten_at="2026-11-03T10:00:00"),
    )
    assert r.status_code == 422 and r.json()["error"]["code"] == "validation_error"


async def test_product_ref_exactly_one(client, family, sf_biscuit_product_id):
    neither = await client.post("/v1/meals", json=_body(family.me, grams=10))
    both = await client.post(
        "/v1/meals",
        json=_body(family.me, sf_biscuit_product_id, grams=10, barcode=OFF_BARCODE),
    )
    assert [r.json()["error"]["code"] for r in (neither, both)] == ["invalid_product_ref"] * 2


async def test_log_off_product_by_barcode_keeps_missing_sugars(client, family):
    r = await client.post("/v1/meals", json=_body(family.dad, barcode=OFF_BARCODE, grams=30))
    assert r.status_code == 201
    j = r.json()
    assert (j["product_id"], j["barcode"], j["product_name"]) == (None, OFF_BARCODE, "OFF Namkeen")
    assert j["attribution"] == "attribution.off"
    assert j["nutrients"]["sugars_g"] is None  # never 0
    assert j["nutrients"]["energy_kcal"] == 165.0
    assert j["grade"] is None  # no sugars -> the engine cannot grade it


async def test_unknown_product_404(client, family):
    r = await client.post("/v1/meals", json=_body(family.me, uuid4(), grams=10))
    assert r.status_code == 404 and r.json()["error"]["code"] == "product_not_found"


async def test_off_down_503(client, family, login):
    login(off=FakeOff(fail=True))
    r = await client.post("/v1/meals", json=_body(family.me, barcode=OFF_BARCODE, grams=10))
    assert r.status_code == 503 and r.json()["error"]["code"] == "off_unavailable"


async def test_idempotent_retry_does_not_need_off(client, family, login):
    body = _body(family.me, barcode=OFF_BARCODE, grams=30, client_id=str(uuid4()))
    first = await client.post("/v1/meals", json=body)
    login(off=FakeOff(fail=True))
    again = await client.post("/v1/meals", json=body)
    assert (first.status_code, again.status_code) == (201, 200)


async def test_client_id_is_per_account(client, family, sf_biscuit_product_id, login, db_session):
    from app.core.security import AccountContext
    from app.features.me.service import ensure_account
    from app.features.members.models import Member

    client_id = str(uuid4())
    a = await client.post(
        "/v1/meals", json=_body(family.me, sf_biscuit_product_id, grams=30, client_id=client_id)
    )
    await ensure_account(db_session, AccountContext(ACC_C, None))
    other = Member(account_id=ACC_C, name="C", relation="self", is_primary=True)
    db_session.add(other)
    await db_session.flush()
    login(ACC_C)
    b = await client.post(
        "/v1/meals", json=_body(other.id, sf_biscuit_product_id, grams=30, client_id=client_id)
    )
    assert (a.status_code, b.status_code) == (201, 201) and a.json()["id"] != b.json()["id"]


async def test_list_is_per_member_and_newest_first(client, family, sf_biscuit_product_id):
    now = datetime.now(UTC)
    for minutes, member in ((60, family.me), (5, family.me), (30, family.dad)):
        eaten = (now - timedelta(minutes=minutes)).isoformat()
        r = await client.post(
            "/v1/meals", json=_body(member, sf_biscuit_product_id, grams=10, eaten_at=eaten)
        )
        assert r.status_code == 201
    mine = (await client.get(f"/v1/meals?member_id={family.me}")).json()
    assert len(mine) == 2 and mine[0]["eaten_at"] > mine[1]["eaten_at"]
    assert {m["member_id"] for m in mine} == {str(family.me)}


async def test_list_range(client, family, sf_biscuit_product_id):
    now = datetime.now(UTC)
    old = (now - timedelta(days=10)).isoformat()
    await client.post(
        "/v1/meals", json=_body(family.me, sf_biscuit_product_id, grams=10, eaten_at=old)
    )
    await client.post("/v1/meals", json=_body(family.me, sf_biscuit_product_id, grams=10))
    default = (await client.get(f"/v1/meals?member_id={family.me}")).json()
    assert len(default) == 1  # last 7 IST days
    start = (now - timedelta(days=11)).isoformat()
    wide = await client.get("/v1/meals", params={"member_id": str(family.me), "from": start})
    assert len(wide.json()) == 2


async def test_list_foreign_member_404(client, family, other_account_member_id):
    r = await client.get(f"/v1/meals?member_id={other_account_member_id}")
    assert r.status_code == 404 and r.json()["error"]["code"] == "member_not_found"


async def test_delete_and_foreign_delete(client, family, sf_biscuit_product_id, login):
    made = await client.post("/v1/meals", json=_body(family.me, sf_biscuit_product_id, grams=10))
    meal_id = made.json()["id"]
    login(ACC_C)
    r = await client.delete(f"/v1/meals/{meal_id}")
    assert r.status_code == 404 and r.json()["error"]["code"] == "meal_not_found"
    login()
    assert (await client.delete(f"/v1/meals/{meal_id}")).status_code == 204
    assert (await client.delete(f"/v1/meals/{meal_id}")).status_code == 404
    assert (await client.get(f"/v1/meals?member_id={family.me}")).json() == []


async def test_grams_bounds(client, family, sf_biscuit_product_id):
    for grams in (0, -1, 5001):
        r = await client.post(
            "/v1/meals", json=_body(family.me, sf_biscuit_product_id, grams=grams)
        )
        assert r.status_code == 422
    r = await client.post(
        "/v1/meals", json=_body(family.me, sf_biscuit_product_id, servings=201)
    )  # 201 x 25 g > 5000 g
    assert r.status_code == 422


async def test_requires_auth(app, client):
    app.dependency_overrides.clear()
    r = await client.get(f"/v1/meals?member_id={uuid4()}")
    assert r.status_code == 401


async def test_concurrent_same_client_id_returns_the_winner(
    client, family, sf_biscuit_product_id, monkeypatch
):
    """The pre-check misses (a concurrent request inserted first): the unique key decides."""
    from app.features.meals import service

    body = _body(family.me, sf_biscuit_product_id, grams=30, client_id=str(uuid4()))
    first = await client.post("/v1/meals", json=body)
    real = service._by_client_id
    calls = []

    async def miss_once(session, account_id, client_id):
        calls.append(client_id)
        return None if len(calls) == 1 else await real(session, account_id, client_id)

    monkeypatch.setattr(service, "_by_client_id", miss_once)
    second = await client.post("/v1/meals", json=body)
    assert (first.status_code, second.status_code) == (201, 200)
    assert second.json()["id"] == first.json()["id"] and len(calls) == 2
