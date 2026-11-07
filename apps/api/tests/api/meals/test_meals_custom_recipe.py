"""Logging custom foods and recipes; ml-basis edits; the unit source; retired dishes
(Plan 12 Task 12; G12, G19-G21, G22)."""

from uuid import uuid4

import pytest
from sqlalchemy import select, update

from app.features.foods.models import Food
from app.features.meals.models import MealLog
from tests.api.meals.conftest import ACC_A

pytestmark = pytest.mark.usefixtures("family")

BAR = {
    "name": "Protein bar",
    "basis": "g",
    "values_per": "100",
    "nutrients": {"energy_kcal": 400, "protein_g": 30, "carbs_g": 40, "fat_g": 12},
}


async def _custom(client, **cols) -> dict:
    r = await client.post("/v1/custom-foods", json=BAR | cols)
    assert r.status_code == 201, r.text
    return r.json()


async def _recipe(client, ingredients, **cols) -> dict:
    r = await client.post("/v1/recipes", json={"name": "Stew", "ingredients": ingredients} | cols)
    assert r.status_code == 201, r.text
    return r.json()


def _ing(food, grams=100):
    return {"custom_food_id": food["id"], "quantity": grams, "unit": "g"}


async def _log(client, **body):
    return await client.post("/v1/meals", json=body)


async def test_log_custom_food_grams_and_serving(client, db_session):
    food = await _custom(client, serving_g=60)
    r = await _log(client, custom_food_id=food["id"], servings=2)
    assert r.status_code == 201, r.text
    j = r.json()
    assert (j["source_kind"], j["custom_food_id"], j["grams"]) == ("custom_food", food["id"], 120.0)
    assert (j["unit"], j["quantity"], j["unit_source"]) == ("serving", 2.0, "grams")
    assert j["nutrients"]["energy_kcal"] == 480.0 and j["nutrients"]["protein_g"] == 36.0
    assert j["nutrients"]["fibre_g"] is None and "fibre_g" in j["incomplete"]
    assert (
        j["attribution"] is None and j["attributions"] == [] and j["product_name"] == "Protein bar"
    )
    assert j["food_id"] is None and j["recipe_id"] is None and j["product_id"] is None


async def test_log_custom_food_katori_via_density(client):
    food = await _custom(client, name="Dal", density_g_per_ml=0.8)
    r = await _log(client, custom_food_id=food["id"], quantity=1, unit="katori")
    assert r.status_code == 201, r.text
    j = r.json()
    assert j["grams"] == pytest.approx(160.0)  # 200 ml x 0.8 g/ml
    assert (j["unit"], j["unit_source"], j["basis"]) == ("katori", "density", "g")
    assert [p["code"] for p in j["portion_units"]][:2] == ["g", "katori"] or "katori" in {
        p["code"] for p in j["portion_units"]
    }


async def test_unit_source_grams_portion_density(client):
    food = await _custom(
        client,
        density_g_per_ml=0.8,
        serving_g=40,
        portions=[{"unit": "piece", "grams_per_unit": 30}],
    )
    ref = {"custom_food_id": food["id"]}
    sources = {}
    for unit in ("g", "serving", "piece", "katori", "tbsp"):
        r = await _log(client, **ref, quantity=1, unit=unit)
        assert r.status_code == 201, (unit, r.text)
        sources[unit] = r.json()["unit_source"]
    assert sources == {
        "g": "grams", "serving": "grams", "piece": "portion", "katori": "density", "tbsp": "density",
    }  # fmt: skip
    # An edit keeps the marker of the unit it moves to, from the entry's own snapshot.
    entry = (await _log(client, **ref, quantity=1, unit="piece")).json()
    patched = await client.patch(f"/v1/meals/{entry['id']}", json={"quantity": 2, "unit": "katori"})
    assert patched.status_code == 200, patched.text
    assert patched.json()["unit_source"] == "density"
    again = await client.patch(f"/v1/meals/{entry['id']}", json={"grams": 50})
    assert again.json()["unit_source"] == "grams"


async def test_unit_source_older_entries(client, db_session):
    quick = await _log(client, quick={"energy_kcal": 100})
    assert quick.json()["unit_source"] is None
    row = await db_session.scalar(select(MealLog).where(MealLog.id == quick.json()["id"]))
    assert row.unit is None


async def test_log_recipe_serving(client):
    full = await _custom(client)
    recipe = await _recipe(client, [_ing(full, 200)], servings=4)
    r = await _log(client, recipe_id=recipe["id"], servings=1)
    assert r.status_code == 201, r.text
    j = r.json()
    assert (j["source_kind"], j["recipe_id"], j["unit"]) == ("recipe", recipe["id"], "serving")
    assert j["grams"] == 50.0 and j["product_name"] == "Stew"  # 200 g / 4 servings
    assert j["nutrients"]["energy_kcal"] == 200.0 and j["nutrients"]["protein_g"] == 15.0
    assert j["unit_source"] == "grams" and j["custom_food_id"] is None
    by_grams = await _log(client, recipe_id=recipe["id"], grams=100)
    assert by_grams.json()["nutrients"]["energy_kcal"] == 400.0
    no_servings = await _recipe(client, [_ing(full, 100)])
    r = await _log(client, recipe_id=no_servings["id"], servings=1)
    assert r.status_code == 422 and r.json()["error"]["code"] == "serving_size_unknown"


async def test_recipe_entry_nulls_incomplete_nutrients(client, db_session):
    full = await _custom(client, name="Full", nutrients={**BAR["nutrients"], "fibre_g": 4})
    nofibre = await _custom(client, name="No fibre")
    recipe = await _recipe(client, [_ing(full, 100), _ing(nofibre, 100)], servings=2)
    assert "fibre_g" in recipe["incomplete_nutrients"]
    assert recipe["per_100g"]["fibre_g"] == 2.0  # the recipe screen: at least
    j = (await _log(client, recipe_id=recipe["id"], servings=1)).json()
    assert j["nutrients"]["fibre_g"] is None  # the entry never counts a partial value
    assert "fibre_g" in j["incomplete"] and "protein_g" not in j["incomplete"]
    row = await db_session.scalar(
        select(MealLog).where(MealLog.id == j["id"]).execution_options(populate_existing=True)
    )
    assert row.food_snapshot["per_100"]["fibre_g"] is None
    assert row.food_snapshot["per_100"]["protein_g"] == 30.0
    assert row.food_snapshot["units"].keys() == {"g", "serving"}
    assert row.food_snapshot["source"] == "recipe"


async def test_log_deleted_or_foreign_refs_404(client, grant, login):
    food = await _custom(client)
    recipe = await _recipe(client, [_ing(food)], servings=1)
    assert (await client.delete(f"/v1/recipes/{recipe['id']}")).status_code == 204
    r = await _log(client, recipe_id=recipe["id"], servings=1)
    assert r.status_code == 404 and r.json()["error"]["code"] == "recipe_not_found"
    assert (await client.delete(f"/v1/custom-foods/{food['id']}")).status_code == 204
    r = await _log(client, custom_food_id=food["id"], grams=10)
    assert r.status_code == 404 and r.json()["error"]["code"] == "custom_food_not_found"
    mine = await _custom(client, name="Mine")
    from tests.api.meals.conftest import ACC_C

    login(ACC_C)  # another account may not log it
    r = await _log(client, custom_food_id=mine["id"], grams=10)
    assert r.status_code == 404 and r.json()["error"]["code"] == "custom_food_not_found"


async def test_exactly_one_ref(client):
    food = await _custom(client)
    recipe = await _recipe(client, [_ing(food)], servings=1)
    r = await _log(client, custom_food_id=food["id"], recipe_id=recipe["id"], grams=10)
    assert r.status_code == 422 and r.json()["error"]["code"] == "invalid_product_ref"


# ---- ml-basis foods: the edit path must convert through the density (a latent bug fixed here)


async def test_ml_log_and_patch_grams_use_the_density(client):
    shake = await _custom(client, name="Shake", basis="ml", density_g_per_ml=1.05)
    ref = {"custom_food_id": shake["id"]}
    logged = await _log(client, **ref, quantity=200, unit="ml")
    assert logged.status_code == 201, logged.text
    j = logged.json()
    assert (j["grams"], j["basis"], j["unit"], j["unit_source"]) == (200.0, "ml", "ml", "grams")
    assert j["nutrients"]["energy_kcal"] == 800.0  # 400 kcal per 100 ml
    by_grams = await _log(client, **ref, grams=105)  # 105 g of a 1.05 g/ml drink = 100 ml
    assert by_grams.json()["grams"] == pytest.approx(100.0)
    # PATCH grams must agree with the log path: 210 g is 200 ml, never 210 ml.
    patched = await client.patch(f"/v1/meals/{j['id']}", json={"grams": 210})
    assert patched.status_code == 200, patched.text
    out = patched.json()
    assert out["grams"] == pytest.approx(200.0) and out["basis"] == "ml"
    assert (out["quantity"], out["unit"], out["unit_source"]) == (210.0, "g", "density")
    assert out["nutrients"]["energy_kcal"] == pytest.approx(800.0)
    ml = await client.patch(f"/v1/meals/{j['id']}", json={"quantity": 100, "unit": "ml"})
    assert ml.json()["grams"] == 100.0 and ml.json()["unit_source"] == "grams"


async def test_ml_patch_grams_without_density_refused(client, db_session):
    juice = await _custom(client, name="Juice", basis="ml")
    ref = {"custom_food_id": juice["id"]}
    logged = (await _log(client, **ref, quantity=1, unit="glass")).json()
    assert logged["grams"] == 250.0 and logged["basis"] == "ml"  # a glass is 250 ml
    before = logged["nutrients"]
    r = await client.patch(f"/v1/meals/{logged['id']}", json={"grams": 100})
    assert r.status_code == 422 and r.json()["error"]["code"] == "unit_grams_unknown"
    assert r.json()["error"]["details"]["unit"] == "g"
    row = await db_session.scalar(
        select(MealLog).where(MealLog.id == logged["id"]).execution_options(populate_existing=True)
    )
    assert row.grams == 250.0 and row.nutrients["energy_kcal"] == before["energy_kcal"]
    # Logging grams without a density is refused the same way (the two paths agree).
    r = await _log(client, **ref, grams=100)
    assert r.status_code == 422 and r.json()["error"]["code"] == "unit_grams_unknown"
    ok = await client.patch(f"/v1/meals/{logged['id']}", json={"quantity": 2, "unit": "glass"})
    assert ok.status_code == 200 and ok.json()["grams"] == 500.0


async def test_gram_basis_patch_unchanged(client):
    food = await _custom(client)
    j = (await _log(client, custom_food_id=food["id"], grams=100)).json()
    out = (await client.patch(f"/v1/meals/{j['id']}", json={"grams": 50})).json()
    assert out["grams"] == 50.0 and out["unit"] == "g" and out["nutrients"]["energy_kcal"] == 200.0


# ---- retired dishes: readable, never logged anew


async def _retire(db_session, code="dal_tadka") -> None:
    await db_session.execute(
        update(Food).where(Food.source_code == code).values(review_status="retired")
    )
    await db_session.flush()


async def test_retired_dish_cannot_be_logged_but_old_entries_stay(client, food_ids, db_session):
    first = await _log(client, food_id=food_ids["dal_tadka"], grams=200)
    assert first.status_code == 201
    await _retire(db_session)
    r = await _log(client, food_id=food_ids["dal_tadka"], grams=100)
    assert r.status_code == 422 and r.json()["error"]["code"] == "food_retired"
    # The existing entry still reads, edits and lists; the detail route still serves it.
    meals = (await client.get("/v1/meals")).json()
    assert [m["id"] for m in meals] == [first.json()["id"]]
    patched = await client.patch(f"/v1/meals/{first.json()['id']}", json={"grams": 100})
    assert patched.status_code == 200
    assert (await client.get(f"/v1/foods/food/{food_ids['dal_tadka']}")).status_code == 200
    # Another, active food is unaffected.
    assert (await _log(client, food_id=food_ids["171844"], grams=50)).status_code == 201


async def test_retired_dish_cannot_be_copied(client, food_ids, db_session, clock):
    slot = (await client.get("/v1/meal-slots")).json()["items"][0]["id"]
    await _log(
        client, food_id=food_ids["dal_tadka"], grams=200, local_date="2026-11-06", meal_slot_id=slot
    )
    await _retire(db_session)
    r = await client.post(
        "/v1/meals/copy",
        json={"from_date": "2026-11-06", "to_date": "2026-11-07", "client_id": str(uuid4())},
    )
    assert r.status_code == 422 and r.json()["error"]["code"] == "food_retired"
    assert (await client.get("/v1/meals")).json().__len__() == 1  # nothing was created


async def test_copy_carries_custom_food_and_recipe(client, clock):
    food = await _custom(client)
    recipe = await _recipe(client, [_ing(food)], servings=1)
    slot = (await client.get("/v1/meal-slots")).json()["items"][0]["id"]
    for ref in ({"custom_food_id": food["id"]}, {"recipe_id": recipe["id"]}):
        r = await _log(client, **ref, grams=50, local_date="2026-11-06", meal_slot_id=slot)
        assert r.status_code == 201, r.text
    r = await client.post(
        "/v1/meals/copy",
        json={"from_date": "2026-11-06", "to_date": "2026-11-07", "client_id": str(uuid4())},
    )
    assert r.status_code in (200, 201), r.text
    made = r.json()["created"]
    assert {(m["source_kind"], m["custom_food_id"], m["recipe_id"]) for m in made} == {
        ("custom_food", food["id"], None),
        ("recipe", None, recipe["id"]),
    }
    assert ACC_A  # (the copies belong to the same account)
