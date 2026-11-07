"""foods_portion_put / foods_portion_delete (Plan 12 Task 4; G11)."""

import pytest
from sqlalchemy import func, select

from app.features.foods.models import FoodPortion
from tests.api.foods.conftest import ACC_A, ACC_B, OFF_BARCODE


def _url(kind, ident, unit):
    return f"/v1/foods/{kind}/{ident}/portions/{unit}"


async def _units(client, ident):
    r = await client.get(f"/v1/foods/food/{ident}")
    assert r.status_code == 200, r.text
    return {u["code"]: u for u in r.json()["units"]}


async def test_put_override_then_detail_marks_user_override(client, consented, food_ids):
    ident = food_ids["171844"]
    r = await client.put(_url("food", ident, "roti"), json={"grams_per_unit": 35})
    assert r.status_code == 200, r.text
    roti = {u["code"]: u for u in r.json()["units"]}["roti"]
    assert roti["grams_per_unit"] == 35.0 and roti["user_override"] is True
    assert roti["source"] == "portion_user"
    again = (await _units(client, ident))["roti"]
    assert again["grams_per_unit"] == 35.0 and again["user_override"] is True
    # A unit that did not resolve now does (the user's own value), and stops being settable.
    r = await client.put(_url("food", ident, "katori"), json={"grams_per_unit": 120.5})
    assert r.status_code == 200
    assert (await _units(client, ident))["katori"]["grams_per_unit"] == 120.5
    assert "katori" not in r.json()["settable_units"]
    # Replacing the value keeps one row.
    await client.put(_url("food", ident, "roti"), json={"grams_per_unit": 40})
    assert (await _units(client, ident))["roti"]["grams_per_unit"] == 40.0


async def test_override_scoped_to_account(client, consented, grant, login, db_session, food_ids):
    ident = food_ids["171844"]
    await client.put(_url("food", ident, "roti"), json={"grams_per_unit": 35})
    await grant(ACC_B)
    login(ACC_B)
    roti = (await _units(client, ident))["roti"]
    assert roti["grams_per_unit"] == 68.0 and roti["user_override"] is False  # never A's value
    await client.put(_url("food", ident, "roti"), json={"grams_per_unit": 90})
    login(ACC_A)
    assert (await _units(client, ident))["roti"]["grams_per_unit"] == 35.0
    rows = await db_session.scalars(select(FoodPortion).where(FoodPortion.account_id.is_not(None)))
    assert sorted(r.account_id.hex for r in rows) == sorted([ACC_A.hex, ACC_B.hex])


@pytest.mark.parametrize("unit", ["g", "serving", "ladle", "idli"])
async def test_put_mass_or_serving_refused(client, consented, food_ids, unit):
    r = await client.put(_url("food", food_ids["171844"], unit), json={"grams_per_unit": 30})
    assert r.status_code == 422 and r.json()["error"]["code"] == "unit_not_supported", unit


@pytest.mark.parametrize("grams", [0, -1, 2001])
async def test_put_bounds(client, consented, food_ids, grams):
    r = await client.put(_url("food", food_ids["171844"], "roti"), json={"grams_per_unit": grams})
    assert r.status_code == 422 and r.json()["error"]["code"] == "validation_error"
    assert (await client.put(_url("food", food_ids["171844"], "roti"), json={})).status_code == 422
    boundary = await client.put(
        _url("food", food_ids["171844"], "roti"), json={"grams_per_unit": 2000}
    )
    assert boundary.status_code == 200


async def test_delete_restores_global(client, consented, food_ids, db_session):
    ident = food_ids["171844"]
    await client.put(_url("food", ident, "roti"), json={"grams_per_unit": 35})
    assert (await client.delete(_url("food", ident, "roti"))).status_code == 204
    roti = (await _units(client, ident))["roti"]
    assert roti["grams_per_unit"] == 68.0 and roti["user_override"] is False
    # Idempotent: nothing to remove is fine; an unknown reference is fine too.
    assert (await client.delete(_url("food", ident, "roti"))).status_code == 204
    assert (await client.delete(_url("food", "not-a-uuid", "roti"))).status_code == 204
    n = await db_session.scalar(
        select(func.count()).select_from(FoodPortion).where(FoodPortion.account_id.is_(None))
    )
    assert n == 19  # the global rows are never touched


async def test_delete_never_removes_another_accounts_override(
    client, consented, grant, login, food_ids
):
    ident = food_ids["171844"]
    await grant(ACC_B)
    login(ACC_B)
    await client.put(_url("food", ident, "roti"), json={"grams_per_unit": 90})
    login(ACC_A)
    assert (await client.delete(_url("food", ident, "roti"))).status_code == 204
    login(ACC_B)
    assert (await _units(client, ident))["roti"]["grams_per_unit"] == 90.0


async def test_product_override_by_barcode(client, consented, db_session):
    r = await client.put(_url("off", OFF_BARCODE, "piece"), json={"grams_per_unit": 6})
    assert r.status_code == 200, r.text
    d = r.json()
    piece = {u["code"]: u for u in d["units"]}["piece"]
    assert piece["grams_per_unit"] == 6.0 and piece["user_override"] is True
    assert d["kind"] == "off" and d["attribution"] == "attribution.off"
    row = await db_session.scalar(select(FoodPortion).where(FoodPortion.off_barcode == OFF_BARCODE))
    assert row.account_id == ACC_A and row.source == "user" and row.food_id is None
    again = await client.get(f"/v1/foods/off/{OFF_BARCODE}")
    assert {u["code"]: u for u in again.json()["units"]}["piece"]["grams_per_unit"] == 6.0
    assert (await client.delete(_url("off", OFF_BARCODE, "piece"))).status_code == 204
    after = await client.get(f"/v1/foods/off/{OFF_BARCODE}")
    assert "piece" not in [u["code"] for u in after.json()["units"]]


async def test_override_of_an_own_product(client, consented, db_session):
    from app.features.products.models import Product

    product = Product(
        name="Parle biscuit", category="general", source="label",
        verification_status="verified", per_100g={"energy_kcal": 450}, serving_size_g=30,
    )  # fmt: skip
    db_session.add(product)
    await db_session.flush()
    r = await client.put(_url("product", product.id, "piece"), json={"grams_per_unit": 8})
    assert r.status_code == 200, r.text
    assert [u["code"] for u in r.json()["units"]] == ["g", "serving", "piece"]
    row = await db_session.scalar(select(FoodPortion).where(FoodPortion.product_id == product.id))
    assert row.account_id == ACC_A
    assert (
        await client.put(_url("product", product.id, "g"), json={"grams_per_unit": 8})
    ).status_code == 422


async def test_unknown_food_404_on_put(client, consented, seeded):
    r = await client.put(
        "/v1/foods/food/00000000-0000-0000-0000-000000000000/portions/roti",
        json={"grams_per_unit": 30},
    )
    assert r.status_code == 404 and r.json()["error"]["code"] == "food_not_found"


async def test_rate_limited(client, consented, food_ids, app, monkeypatch):
    monkeypatch.setattr(app.state.settings, "rate_limit_diary_writes_per_day", 2)
    url = _url("food", food_ids["171844"], "roti")
    assert (await client.put(url, json={"grams_per_unit": 30})).status_code == 200
    assert (await client.put(url, json={"grams_per_unit": 31})).status_code == 200
    r = await client.put(url, json={"grams_per_unit": 32})
    assert r.status_code == 429 and r.json()["error"]["code"] == "rate_limited"
    assert "retry-after" in {k.lower() for k in r.headers}
