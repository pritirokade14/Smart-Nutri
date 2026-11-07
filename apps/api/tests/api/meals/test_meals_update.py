"""PATCH /v1/meals/{id} (Plan 11 Task 4; Ruling E10: null = unchanged)."""

from uuid import uuid4

import pytest
from sqlalchemy import text

from tests.api.meals.conftest import ACC_A, ACC_C

pytestmark = pytest.mark.usefixtures("family")

NUTRIENT_KEYS = ["energy_kcal", "sugars_g", "salt_g", "protein_g", "fat_g", "sat_fat_g", "carbs_g"]


async def _log(client, member, product, **kw):
    r = await client.post(
        "/v1/meals", json={"member_id": str(member), "product_id": str(product), **kw}
    )
    assert r.status_code == 201, r.text
    return r.json()


async def _patch(client, meal_id, **body):
    return await client.patch(f"/v1/meals/{meal_id}", json=body)


async def test_update_grams_recomputes_from_snapshot(
    client, family, sf_biscuit_product_id, db_session
):
    m = await _log(client, family.me, sf_biscuit_product_id, grams=50)
    # The product is edited after logging: the entry still recomputes from its own snapshot.
    await db_session.execute(
        text(
            "update products set per_100g = jsonb_set(per_100g, '{energy_kcal}', '999') where id = :p"
        ),
        {"p": sf_biscuit_product_id},
    )
    r = await _patch(client, m["id"], grams=100)
    assert r.status_code == 200, r.text
    j = r.json()
    assert j["grams"] == 100.0
    for key in NUTRIENT_KEYS:
        if m["nutrients"][key] is not None:
            assert j["nutrients"][key] == pytest.approx(2 * m["nutrients"][key], abs=0.11), key
    assert j["nutrients"]["energy_kcal"] == pytest.approx(
        2 * m["nutrients"]["energy_kcal"], abs=0.11
    )
    assert j["nutrients"]["energy_kcal"] < 500  # not the edited 999 per 100 g
    assert j["updated_at"] >= m["updated_at"]


async def test_update_legacy_row_uses_inverse(client, family, sf_biscuit_product_id, db_session):
    m = await _log(client, family.me, sf_biscuit_product_id, grams=40)
    await db_session.execute(
        text(
            "update meal_logs set food_snapshot = null, nutrients = nutrients - 'fibre_g' "
            "where id = :i"
        ),
        {"i": m["id"]},
    )

    async def stored():
        row = await db_session.execute(
            text("select nutrients from meal_logs where id = :i"), {"i": m["id"]}
        )
        return row.scalar_one()

    before = await stored()
    r = await _patch(client, m["id"], grams=80)
    assert r.status_code == 200, r.text
    after = await stored()
    for key in NUTRIENT_KEYS:
        if before[key] is None:
            assert after[key] is None, key
        else:
            assert after[key] == pytest.approx(2 * before[key], rel=1e-9), key  # exact inverse
    assert after["fibre_g"] is None and r.json()["nutrients"]["fibre_g"] is None


async def test_update_servings_needs_serving_size(client, family, db_session):
    from scripts.export_fixture_responses import fixture_product_record

    record = fixture_product_record("no_ingredients")  # no serving size
    db_session.add(record)
    await db_session.flush()
    m = await _log(client, family.me, record.id, grams=30)
    r = await _patch(client, m["id"], servings=1)
    assert r.status_code == 422 and r.json()["error"]["code"] == "serving_size_unknown"


async def test_update_servings(client, family, sf_biscuit_product_id):
    m = await _log(client, family.me, sf_biscuit_product_id, grams=10)
    r = await _patch(client, m["id"], servings=2)  # 25 g serving
    assert r.status_code == 200 and r.json()["grams"] == 50.0


async def test_move_slot(client, family, sf_biscuit_product_id):
    m = await _log(client, family.me, sf_biscuit_product_id, grams=30)
    slots = {i["label_key"]: i["id"] for i in (await client.get("/v1/meal-slots")).json()["items"]}
    target = slots["diary.slot.snack"]
    r = await _patch(client, m["id"], meal_slot_id=target)
    assert r.status_code == 200 and r.json()["meal_slot_id"] == target
    assert r.json()["grams"] == 30.0  # nothing else changed
    ghost = await _patch(client, m["id"], meal_slot_id=str(uuid4()))
    assert ghost.status_code == 404 and ghost.json()["error"]["code"] == "meal_slot_not_found"


async def test_update_eaten_at_moves_local_date(client, family, sf_biscuit_product_id, clock):
    m = await _log(client, family.me, sf_biscuit_product_id, grams=30)
    assert m["local_date"] == "2026-11-07"
    r = await _patch(client, m["id"], eaten_at="2026-11-05T10:00:00+00:00")
    assert r.status_code == 200
    assert r.json()["local_date"] == "2026-11-05"
    assert r.json()["eaten_at"].startswith("2026-11-05T10:00:00")


@pytest.mark.parametrize("eaten", ["2026-10-01T10:00:00+00:00", "2026-11-07T07:00:00+00:00"])
async def test_update_eaten_at_out_of_range_422(
    client, family, sf_biscuit_product_id, clock, eaten
):
    m = await _log(client, family.me, sf_biscuit_product_id, grams=30)
    r = await _patch(client, m["id"], eaten_at=eaten)
    assert r.status_code == 422 and r.json()["error"]["code"] == "eaten_at_out_of_range"


async def test_edit_never_touches_other_rows_or_days(
    client, family, sf_biscuit_product_id, db_session
):
    a = await _log(client, family.me, sf_biscuit_product_id, grams=30)
    await _log(client, family.me, sf_biscuit_product_id, grams=40)
    await _log(client, family.dad, sf_biscuit_product_id, grams=50)
    await db_session.execute(
        text(
            "insert into diary_days (member_id, local_date, account_id, status) "
            "values (:m, '2026-11-01', :a, 'none')"
        ),
        {"m": family.me, "a": ACC_A},
    )

    async def snapshot_rest():
        meals = (
            await db_session.execute(
                text("select * from meal_logs where id <> :i order by id"), {"i": a["id"]}
            )
        ).all()
        days = (await db_session.execute(text("select * from diary_days order by 1, 2"))).all()
        return [tuple(r) for r in meals], [tuple(r) for r in days]

    before = await snapshot_rest()
    assert (await _patch(client, a["id"], grams=90)).status_code == 200
    assert await snapshot_rest() == before


async def test_update_quick_values(client, family):
    m = (
        await client.post("/v1/meals", json={"quick": {"energy_kcal": 450, "name": "Lunch"}})
    ).json()
    r = await _patch(
        client, m["id"], quick={"energy_kcal": 300, "protein_g": 4, "name": "  Tea and toast "}
    )
    assert r.status_code == 200, r.text
    j = r.json()
    assert j["nutrients"]["energy_kcal"] == 300.0 and j["nutrients"]["protein_g"] == 4.0
    assert j["nutrients"]["fat_g"] is None and j["product_name"] == "Tea and toast"
    assert j["source_kind"] == "quick_add" and j["grams"] is None
    no_energy = await _patch(client, m["id"], quick={"protein_g": 4})
    assert no_energy.json()["error"]["code"] == "quick_add_energy_required"
    portion = await _patch(client, m["id"], grams=50)
    assert portion.status_code == 422 and portion.json()["error"]["code"] == "validation_error"


async def test_quick_patch_on_product_422(client, family, sf_biscuit_product_id):
    m = await _log(client, family.me, sf_biscuit_product_id, grams=30)
    r = await _patch(client, m["id"], quick={"energy_kcal": 100})
    assert r.status_code == 422 and r.json()["error"]["code"] == "validation_error"


async def test_null_fields_mean_unchanged(client, family, sf_biscuit_product_id):
    m = await _log(client, family.me, sf_biscuit_product_id, grams=30)
    r = await _patch(
        client, m["id"], grams=None, meal_slot_id=None, eaten_at=None, servings=50, quick=None
    )
    # 50 servings x 25 g = 1250 g: only the portion changed.
    assert r.status_code == 200, r.text
    j = r.json()
    assert j["grams"] == 1250.0
    assert (j["meal_slot_id"], j["eaten_at"], j["local_date"]) == (
        m["meal_slot_id"],
        m["eaten_at"],
        m["local_date"],
    )


async def test_empty_patch_422(client, family, sf_biscuit_product_id):
    m = await _log(client, family.me, sf_biscuit_product_id, grams=30)
    for body in ({}, {"grams": None, "servings": None, "meal_slot_id": None}):
        r = await client.patch(f"/v1/meals/{m['id']}", json=body)
        assert r.status_code == 422 and r.json()["error"]["code"] == "validation_error", body
    both = await _patch(client, m["id"], grams=10, servings=1)
    assert both.status_code == 422 and both.json()["error"]["code"] == "validation_error"


async def test_update_foreign_404(client, family, login):
    login(ACC_C)
    other = (await client.post("/v1/meals", json={"quick": {"energy_kcal": 100}})).json()
    login(ACC_A)
    r = await _patch(client, other["id"], grams=10)
    assert r.status_code == 404 and r.json()["error"]["code"] == "meal_not_found"
    r = await _patch(client, str(uuid4()), grams=10)
    assert r.status_code == 404


async def test_update_family_entry_422(client, family, sf_biscuit_product_id, app, monkeypatch):
    m = await _log(client, family.dad, sf_biscuit_product_id, grams=30)
    r = await _patch(client, m["id"], grams=40)
    assert r.status_code == 422 and r.json()["error"]["code"] == "diary_member_not_enabled"
    monkeypatch.setattr(app.state.settings, "diary_family_enabled", True)
    assert (await _patch(client, m["id"], grams=40)).status_code == 200


# ---- Plan 12 Task 5: quantity + unit, resolved only from the entry's own snapshot

from decimal import Decimal

from sqlalchemy import select

from app.features.foods.models import FoodPortion
from app.features.meals.models import MealLog


async def _log_food(client, food_ids, code="172437", **kw):
    body = {"food_id": food_ids[code], **(kw or {"quantity": 1, "unit": "katori"})}
    r = await client.post("/v1/meals", json=body)
    assert r.status_code == 201, r.text
    return r.json()


async def _db_row(db_session, meal_id) -> MealLog:
    return await db_session.scalar(
        select(MealLog).where(MealLog.id == meal_id).execution_options(populate_existing=True)
    )


async def test_patch_quantity_unit_from_snapshot(client, food_ids, db_session):
    m = await _log_food(client, food_ids)
    r = await _patch(client, m["id"], quantity=2, unit="katori_small")
    assert r.status_code == 200, r.text
    j = r.json()
    assert (j["grams"], j["quantity"], j["unit"]) == (163.3, 2.0, "katori_small")  # 2 x 81.65
    row = await _db_row(db_session, m["id"])
    assert row.nutrients["energy_kcal"] == float(Decimal(121) * Decimal("163.3") / 100)
    assert j["updated_at"] >= m["updated_at"]
    # Grams are always resolvable for a gram-basis food, and set the unit to g.
    r = await _patch(client, m["id"], quantity=50, unit="g")
    assert (r.json()["grams"], r.json()["unit"]) == (50.0, "g")
    r = await _patch(client, m["id"], grams=80)
    assert (r.json()["grams"], r.json()["quantity"], r.json()["unit"]) == (80.0, 80.0, "g")


async def test_patch_same_portion_identical_snapshot(client, food_ids, db_session):
    m = await _log_food(client, food_ids)
    before = await _db_row(db_session, m["id"])
    nutrients, snapshot = dict(before.nutrients), dict(before.food_snapshot)
    r = await _patch(client, m["id"], quantity=1, unit="katori")
    assert r.status_code == 200, r.text
    after = await _db_row(db_session, m["id"])
    assert after.nutrients == nutrients  # the round trip changes nothing
    assert after.food_snapshot == snapshot
    assert (after.grams, after.quantity, after.unit) == (142.0, Decimal(1), "katori")
    assert r.json()["nutrients"] == m["nutrients"]


async def test_override_change_keeps_past_entry(client, food_ids, db_session):
    roti = await _log_food(client, food_ids, "171844", quantity=1, unit="roti")  # global 68 g
    assert roti["grams"] == 68.0
    # The user now sets their own roti weight: the past entry does not move.
    db_session.add(
        FoodPortion(
            food_id=(await _db_row(db_session, roti["id"])).food_id,
            unit="roti",
            grams_per_unit=Decimal(35),
            source="user",
            account_id=ACC_A,
        )
    )
    await db_session.flush()
    listed = (await client.get("/v1/meals", params={"local_date": roti["local_date"]})).json()
    same = next(m for m in listed if m["id"] == roti["id"])
    assert same["grams"] == 68.0 and same["nutrients"] == roti["nutrients"]
    # A PATCH to the same unit still uses the snapshot's grams (68), not the new override (35).
    r = await _patch(client, roti["id"], quantity=2, unit="roti")
    assert r.json()["grams"] == 136.0
    # A NEW entry uses the override.
    new = await _log_food(client, food_ids, "171844", quantity=2, unit="roti")
    assert new["grams"] == 70.0


async def test_patch_unit_not_in_snapshot_422(client, food_ids, db_session):
    m = await _log_food(client, food_ids)
    for unit in ("roti", "piece", "serving"):
        r = await _patch(client, m["id"], quantity=1, unit=unit)
        assert r.status_code == 422 and r.json()["error"]["code"] == "unit_grams_unknown", unit
    # Even after the user sets a roti weight, an old entry only knows what resolved then.
    db_session.add(
        FoodPortion(
            food_id=(await _db_row(db_session, m["id"])).food_id,
            unit="roti",
            grams_per_unit=Decimal(35),
            source="user",
            account_id=ACC_A,
        )
    )
    await db_session.flush()
    r = await _patch(client, m["id"], quantity=1, unit="roti")
    assert r.status_code == 422 and r.json()["error"]["code"] == "unit_grams_unknown"
    r = await _patch(client, m["id"], quantity=1001, unit="katori")
    assert r.status_code == 422 and r.json()["error"]["code"] == "quantity_out_of_range"
    r = await _patch(client, m["id"], quantity=30, unit="katori_large")
    assert r.json()["error"]["code"] == "quantity_out_of_range"
    unchanged = await _db_row(db_session, m["id"])
    assert (unchanged.grams, unchanged.unit) == (142.0, "katori")


async def test_patch_quantity_validation(client, family, food_ids, sf_biscuit_product_id):
    m = await _log_food(client, food_ids)
    for body in (
        {"quantity": 1},
        {"unit": "katori"},
        {"quantity": 1, "unit": "katori", "grams": 5},
        {"quantity": 1, "unit": "katori", "servings": 1},
        {"quantity": 1, "unit": "mystery"},
    ):
        r = await _patch(client, m["id"], **body)
        assert r.status_code == 422 and r.json()["error"]["code"] == "validation_error", body
    quick = (await client.post("/v1/meals", json={"quick": {"energy_kcal": 100}})).json()
    r = await _patch(client, quick["id"], quantity=1, unit="g")
    assert r.status_code == 422 and r.json()["error"]["code"] == "validation_error"
    # A product entry logged before units existed (no units in its snapshot) still takes grams.
    p = await _log(client, family.me, sf_biscuit_product_id, grams=50)
    r = await _patch(client, p["id"], quantity=10, unit="g")
    assert r.status_code == 200 and r.json()["grams"] == 10.0
    r = await _patch(client, p["id"], quantity=2, unit="serving")  # 25 g serving, resolved then
    assert r.status_code == 200 and r.json()["grams"] == 50.0


async def test_patch_quantity_unit_on_a_legacy_row_without_snapshot(
    client, family, sf_biscuit_product_id, db_session
):
    m = await _log(client, family.me, sf_biscuit_product_id, grams=40)
    await db_session.execute(
        text("update meal_logs set food_snapshot = null where id = :i"), {"i": m["id"]}
    )
    r = await _patch(client, m["id"], quantity=10, unit="g")
    assert r.status_code == 200 and r.json()["grams"] == 10.0
    assert [u["code"] for u in r.json()["portion_units"]] == ["g"]
    r = await _patch(client, m["id"], quantity=1, unit="serving")  # nothing saved to convert by
    assert r.status_code == 422 and r.json()["error"]["code"] == "unit_grams_unknown"
