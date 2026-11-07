"""Logging generic foods and household units (Plan 12 Task 5; G10-G13)."""

from decimal import Decimal
from uuid import uuid4

import pytest
from sqlalchemy import func, select

from app.features.foods.models import FoodPortion
from app.features.meals.models import MealLog
from tests.api.meals.conftest import ACC_A, OFF_BARCODE

pytestmark = pytest.mark.usefixtures("family")

D = Decimal


async def _post(client, **body):
    return await client.post("/v1/meals", json=body)


async def _row(db_session, meal_id) -> MealLog:
    return await db_session.scalar(
        select(MealLog).where(MealLog.id == meal_id).execution_options(populate_existing=True)
    )


async def _count(db_session) -> int:
    return await db_session.scalar(select(func.count()).select_from(MealLog))


async def test_log_food_katori(client, food_ids, db_session):
    r = await _post(client, food_id=food_ids["172437"], quantity=1, unit="katori")
    assert r.status_code == 201, r.text
    j = r.json()
    assert (j["grams"], j["quantity"], j["unit"], j["basis"]) == (142.0, 1.0, "katori", "g")
    assert j["source_kind"] == "food" and j["food_id"] == food_ids["172437"]
    assert j["product_id"] is None and j["barcode"] is None and j["grade"] is None
    assert j["product_name"].startswith("Pigeon peas")
    row = await _row(db_session, j["id"])
    # The row stores per_100 x grams / 100, UNROUNDED; MealOut rounds to 1 dp.
    assert row.nutrients["energy_kcal"] == float(D("121") * D("142.0") / 100) == 171.82
    assert j["nutrients"]["energy_kcal"] == 171.8
    assert row.nutrients["sugars_g"] is None and "sugars_g" in j["incomplete"]
    assert (row.quantity, row.unit, row.food_id) == (D("1"), "katori", row.food_id)
    snap = row.food_snapshot
    assert snap["basis"] == "g" and snap["source"] == "usda_fdc" and snap["licence"] == "CC0 1.0"
    assert snap["units"]["katori"] == 142.0 and snap["units"]["katori_small"] == 81.65
    assert snap["per_100"]["energy_kcal"] == 121.0
    assert snap["attributions"] == ["attribution.usda_fdc"]
    assert {u["code"]: u["grams_per_unit"] for u in j["portion_units"]}["katori_large"] == 255.6
    assert [u["code"] for u in j["portion_units"]][:2] == ["g", "ml"]  # the table's order


async def test_log_food_count_unit_unknown_422(client, food_ids, db_session):
    for unit in ("roti", "piece", "serving", "tbsp_nope"):
        r = await _post(client, food_id=food_ids["172437"], quantity=2, unit=unit)
        if unit == "tbsp_nope":
            assert r.status_code == 422 and r.json()["error"]["code"] == "validation_error"
            continue
        # The unit never converts, so it is refused (grams are never the quantity).
        if unit == "serving":
            assert r.json()["error"]["code"] == "unit_grams_unknown"
        assert r.status_code == 422 and r.json()["error"]["code"] == "unit_grams_unknown", unit
    # A dish with no density, no portion: katori, tbsp and roti do not resolve.
    for unit in ("katori", "tbsp", "roti"):
        r = await _post(client, food_id=food_ids["dal_tadka"], quantity=1, unit=unit)
        assert r.status_code == 422 and r.json()["error"]["code"] == "unit_grams_unknown", unit
    assert await _count(db_session) == 0  # nothing was stored


async def test_log_food_quantity_out_of_range(client, food_ids, db_session):
    for quantity, unit in ((1001, "katori"), (30, "katori_large"), (5001, "g")):
        r = await _post(client, food_id=food_ids["172437"], quantity=quantity, unit=unit)
        assert r.status_code == 422, (quantity, unit)
        assert r.json()["error"]["code"] in ("quantity_out_of_range", "validation_error")
    assert (await _post(client, food_id=food_ids["172437"], quantity=1001, unit="katori")).json()[
        "error"
    ]["code"] == "quantity_out_of_range"
    assert (
        await _post(client, food_id=food_ids["172437"], quantity=30, unit="katori_large")
    ).json()["error"]["code"] == "quantity_out_of_range"  # 30 x 360 ml x 0.71 > 5000
    for bad in (0, -1):
        r = await _post(client, food_id=food_ids["172437"], quantity=bad, unit="g")
        assert r.status_code == 422 and r.json()["error"]["code"] == "validation_error"
    assert await _count(db_session) == 0
    ok = await _post(client, food_id=food_ids["172437"], quantity=5000, unit="g")
    assert ok.status_code == 201 and ok.json()["grams"] == 5000.0


async def test_log_product_with_user_piece_override(
    client, sf_biscuit_product_id, db_session, seeded
):
    db_session.add(
        FoodPortion(
            product_id=sf_biscuit_product_id,
            unit="piece",
            grams_per_unit=D("8"),
            source="user",
            account_id=ACC_A,
        )
    )
    await db_session.flush()
    r = await _post(client, product_id=str(sf_biscuit_product_id), quantity=2, unit="piece")
    assert r.status_code == 201, r.text
    j = r.json()
    assert (j["grams"], j["quantity"], j["unit"]) == (16.0, 2.0, "piece")
    assert j["source_kind"] == "product" and j["grade"] is not None
    row = await _row(db_session, j["id"])
    assert (
        row.food_snapshot["units"]["piece"] == 8.0 and row.food_snapshot["units"]["serving"] == 25
    )
    # Without the override the unit does not resolve.
    await db_session.execute(FoodPortion.__table__.delete())
    r = await _post(client, product_id=str(sf_biscuit_product_id), quantity=2, unit="piece")
    assert r.status_code == 422 and r.json()["error"]["code"] == "unit_grams_unknown"


async def test_grams_form_stores_unit_g(client, food_ids, sf_biscuit_product_id, db_session):
    r = await _post(client, food_id=food_ids["172437"], grams=150)
    assert r.status_code == 201, r.text
    j = r.json()
    assert (j["grams"], j["quantity"], j["unit"]) == (150.0, 150.0, "g")
    # The servings form stores unit `serving`.
    r = await _post(client, product_id=str(sf_biscuit_product_id), servings=2)
    j = r.json()
    assert (j["grams"], j["quantity"], j["unit"]) == (50.0, 2.0, "serving")
    dish = await _post(client, food_id=food_ids["egg_bhurji"], servings=1)
    assert dish.status_code == 201, dish.text
    assert (dish.json()["grams"], dish.json()["unit"]) == (150.0, "serving")
    # A food with no serving weight keeps the legacy refusal.
    r = await _post(client, food_id=food_ids["172437"], servings=1)
    assert r.status_code == 422 and r.json()["error"]["code"] == "serving_size_unknown"
    r = await _post(client, food_id=food_ids["172437"], servings=1, grams=10)
    assert r.json()["error"]["code"] == "portion_required"
    r = await _post(client, food_id=food_ids["172437"])
    assert r.json()["error"]["code"] == "portion_required"
    r = await _post(client, food_id=food_ids["172437"], grams=10, quantity=1, unit="katori")
    assert r.json()["error"]["code"] == "portion_required"
    r = await _post(client, food_id=food_ids["172437"], quantity=1)
    assert r.status_code == 422 and r.json()["error"]["code"] == "validation_error"
    r = await _post(client, food_id=food_ids["172437"], unit="katori", grams=5)
    assert r.status_code == 422 and r.json()["error"]["code"] == "validation_error"
    legacy = await _post(client, product_id=str(sf_biscuit_product_id), grams=30)
    assert (legacy.json()["quantity"], legacy.json()["unit"]) == (30.0, "g")


async def test_food_entry_attribution_usda(client, food_ids):
    r = await _post(client, food_id=food_ids["172437"], grams=100)
    j = r.json()
    assert j["attributions"] == ["attribution.usda_fdc"]
    assert j["attribution"] is None  # the existing field keeps its meaning: Open Food Facts only
    dish = (await _post(client, food_id=food_ids["dal_tadka"], grams=100)).json()
    assert dish["attributions"] == ["attribution.smartnutri_recipe", "attribution.usda_fdc"]
    off = (await _post(client, barcode=OFF_BARCODE, grams=30)).json()
    assert off["attribution"] == "attribution.off" and off["attributions"] == ["attribution.off"]
    assert (await _post(client, quick={"energy_kcal": 100})).json()["attributions"] == []


async def test_dish_entry_incomplete_from_null_sugar(client, food_ids, db_session):
    r = await _post(client, food_id=food_ids["dal_tadka"], grams=100)
    assert r.status_code == 201, r.text
    j = r.json()
    assert "sugars_g" in j["incomplete"] and "sat_fat_g" in j["incomplete"]
    assert j["nutrients"]["sugars_g"] is None and j["nutrients"]["sat_fat_g"] is None
    assert j["nutrients"]["energy_kcal"] > 0  # never 0 for what is unknown
    row = await _row(db_session, j["id"])
    assert row.nutrients["sugars_g"] is None and row.food_snapshot["per_100"]["sugars_g"] is None
    assert row.food_snapshot["source"] == "smartnutri_recipe"


async def test_two_refs_invalid_product_ref(client, food_ids, sf_biscuit_product_id):
    for body in (
        {"food_id": food_ids["172437"], "product_id": str(sf_biscuit_product_id), "grams": 10},
        {"food_id": food_ids["172437"], "barcode": OFF_BARCODE, "grams": 10},
        {"food_id": food_ids["172437"], "quick": {"energy_kcal": 5}, "grams": 10},
        {"grams": 10},
    ):
        r = await _post(client, **body)
        assert r.status_code == 422 and r.json()["error"]["code"] == "invalid_product_ref", body
    r = await _post(client, food_id=food_ids["172437"], quick={"energy_kcal": 5})
    assert r.json()["error"]["code"] == "invalid_product_ref"
    r = await _post(client, quick={"energy_kcal": 5}, quantity=1, unit="g")
    assert r.status_code == 422 and r.json()["error"]["code"] == "validation_error"


async def test_unknown_food_404(client, seeded):
    r = await _post(client, food_id=str(uuid4()), grams=10)
    assert r.status_code == 404 and r.json()["error"]["code"] == "food_not_found"


async def test_offline_retry_client_id_returns_same_row(client, food_ids, db_session):
    cid = str(uuid4())
    body = {"food_id": food_ids["172437"], "quantity": 1, "unit": "katori", "client_id": cid}
    first = await _post(client, **body)
    again = await _post(client, **body)
    assert (first.status_code, again.status_code) == (201, 200)
    assert first.json()["id"] == again.json()["id"] and again.json()["unit"] == "katori"
    assert await _count(db_session) == 1


async def test_hidden_numbers_still_redact_food_entries(client, food_ids, db_session):
    from app.features.members import service as members_service
    from app.features.targets.models import DiaryGoalSettings

    member = await members_service.get_or_create_primary(db_session, ACC_A)
    db_session.add(
        DiaryGoalSettings(
            member_id=member.id,
            account_id=ACC_A,
            direction="maintain",
            activity_level="light",
            numbers_display="hide_all",
        )
    )
    await db_session.flush()
    j = (await _post(client, food_id=food_ids["172437"], quantity=1, unit="katori")).json()
    assert set(j["nutrients"].values()) == {None}
    assert j["grams"] == 142.0 and j["quantity"] == 1.0 and j["unit"] == "katori"
