"""Recipes CRUD (Plan 12 Task 12; spec 5.9; G15, G19-G22)."""

from uuid import uuid4

import pytest

from tests.api.diary.test_hidden import _check
from tests.api.recipes.conftest import (
    ACC_A,
    ACC_B,
    G1_SETTINGS,
    OFF_BARCODE,
    bar,
    ing,
    make_custom,
)

URL = "/v1/recipes"


async def _two(client):
    full = await make_custom(
        client, "Full", energy_kcal=200, protein_g=10, carbs_g=20, fat_g=8, fibre_g=4
    )
    nofibre = await make_custom(client, "No fibre", energy_kcal=100, protein_g=5, carbs_g=10)
    return full, nofibre


def recipe(*ingredients, **cols) -> dict:
    return {"name": "Stew", "ingredients": list(ingredients)} | cols


async def test_create_get_list(client, consented):
    full, nofibre = await _two(client)
    r = await client.post(
        URL, json=recipe(ing(full, 100), ing(nofibre, 100), servings=2, name="  Stew  ")
    )
    assert r.status_code == 201, r.text
    out = r.json()
    assert out["name"] == "Stew" and out["servings"] == 2.0 and out["cooked_weight_g"] is None
    assert out["total_raw_g"] == 200.0 and out["basis_weight_g"] == 200.0
    # energy: (200 + 100) / 200 g x 100 = 150 per 100 g; fibre only from "Full": a lower bound.
    assert out["per_100g"]["energy_kcal"] == 150.0 and out["per_100g"]["fibre_g"] == 2.0
    assert out["per_serving"]["energy_kcal"] == 150.0 and out["per_serving"]["fibre_g"] == 2.0
    assert (
        "fibre_g" in out["incomplete_nutrients"]
        and "energy_kcal" not in out["incomplete_nutrients"]
    )
    assert out["per_100g"]["sat_fat_g"] is None  # no ingredient knows it: null, never 0
    assert [i["position"] for i in out["ingredients"]] == [0, 1]
    first = out["ingredients"][0]
    assert first["source_kind"] == "custom_food" and first["custom_food_id"] == full
    assert first["quantity"] == 100.0 and first["unit"] == "g" and first["grams"] == 100.0
    assert first["available"] is True and first["attribution"] is None
    assert out["attributions"] == [] and out["numbers_hidden"] == {"energy": False, "macros": False}
    assert (await client.get(f"{URL}/{out['id']}")).json() == out
    listed = (await client.get(URL)).json()
    assert listed["next_cursor"] is None
    assert [(i["id"], i["name"], i["servings"]) for i in listed["items"]] == [
        (out["id"], "Stew", 2.0)
    ]
    assert listed["items"][0]["incomplete_nutrients"] == out["incomplete_nutrients"]


async def test_per_serving_null_without_servings(client, consented):
    full, _ = await _two(client)
    out = (await client.post(URL, json=recipe(ing(full, 100)))).json()
    assert out["per_serving"] is None and out["servings"] is None


async def test_ingredient_limit_51(client, consented):
    full, _ = await _two(client)
    ok = await client.post(URL, json=recipe(*[ing(full, 10)] * 50))
    assert ok.status_code == 201, ok.text
    for items in ([ing(full, 10)] * 51, []):
        r = await client.post(URL, json=recipe(*items))
        assert r.status_code == 422 and r.json()["error"]["code"] == "recipe_ingredient_limit"


async def test_ingredient_ref_rules(client, consented, food_ids):
    full, _ = await _two(client)
    both = {"custom_food_id": full, "food_id": food_ids["171844"]}
    for ref in (both, {}):
        r = await client.post(URL, json=recipe({**ref, "quantity": 10, "unit": "g"}))
        assert r.status_code == 422 and r.json()["error"]["code"] == "invalid_product_ref"
    r = await client.post(
        URL, json=recipe({"custom_food_id": str(uuid4()), "quantity": 10, "unit": "g"})
    )
    assert r.status_code == 404 and r.json()["error"]["code"] == "custom_food_not_found"


async def test_unit_grams_unknown_has_position(client, consented):
    full, _ = await _two(client)
    r = await client.post(URL, json=recipe(ing(full, 50), ing(full, 2, "katori")))
    assert r.status_code == 422, r.text
    err = r.json()["error"]
    assert err["code"] == "unit_grams_unknown"
    assert err["details"]["position"] == 1 and err["details"]["unit"] == "katori"
    r = await client.post(URL, json=recipe(ing(full, 5000, "g"), ing(full, 5001, "g")))
    assert r.status_code == 422  # quantity above the unit's limit
    r = await client.post(URL, json=recipe(ing(full, 3, "serving"), ing(full, 99, "tbsp")))
    assert r.json()["error"]["details"]["position"] == 1  # serving ok (50 g), tbsp has no density


async def test_weight_invalid_reasons(client, consented):
    full, _ = await _two(client)
    milk = (
        await client.post(
            "/v1/custom-foods", json=bar(name="Milk", basis="ml", nutrients={"energy_kcal": 60})
        )
    ).json()["id"]
    # An ml ingredient with no density has no mass: the cooked weight is required.
    r = await client.post(URL, json=recipe(ing(full, 100), ing(milk, 200, "ml")))
    assert r.status_code == 422 and r.json()["error"]["code"] == "recipe_weight_invalid"
    assert r.json()["error"]["details"]["reason"] == "cooked_weight_required"
    ok = await client.post(
        URL, json=recipe(ing(full, 100), ing(milk, 200, "ml"), cooked_weight_g=250)
    )
    assert ok.status_code == 201 and ok.json()["total_raw_g"] is None
    assert ok.json()["basis_weight_g"] == 250.0
    # Cooked weight outside 0.2-3 x the raw total.
    for cooked in (19, 301):
        r = await client.post(URL, json=recipe(ing(full, 100), cooked_weight_g=cooked))
        assert r.status_code == 422, cooked
        assert r.json()["error"]["details"]["reason"] == "out_of_range"
    for cooked in (20, 300):
        assert (
            await client.post(URL, json=recipe(ing(full, 100), cooked_weight_g=cooked))
        ).status_code == 201


async def test_ml_ingredient_with_density_counts_toward_raw(client, consented):
    milk = (
        await client.post(
            "/v1/custom-foods",
            json=bar(name="Milk", basis="ml", density_g_per_ml=1.03, nutrients={"energy_kcal": 60}),
        )
    ).json()["id"]
    r = await client.post(URL, json=recipe(ing(milk, 200, "ml")))
    assert r.status_code == 201, r.text
    assert r.json()["total_raw_g"] == pytest.approx(206.0)


async def test_recipe_out_redacted(client, g1, consented):
    full, nofibre = await _two(client)
    created = await client.post(URL, json=recipe(ing(full, 100), ing(nofibre, 100), servings=2))
    rid = created.json()["id"]
    for display in ("hide_energy", "hide_all"):
        assert (
            await client.put(
                "/v1/targets/settings", json={**G1_SETTINGS, "numbers_display": display}
            )
        ).status_code == 200
        body = (await client.get(f"{URL}/{rid}")).json()
        _check("recipes_get", body, display)
        assert body["per_100g"]["energy_kcal"] is None
        assert body["incomplete_nutrients"] == created.json()["incomplete_nutrients"]  # stays
        if display == "hide_all":
            assert all(v is None for v in body["per_100g"].values())
            assert all(v is None for v in body["per_serving"].values())
        else:
            assert body["per_100g"]["protein_g"] is not None
        assert body["total_raw_g"] == 200.0  # weights are not nutrients
    posted = await client.post(URL, json=recipe(ing(full, 100)))
    assert posted.json()["per_100g"]["energy_kcal"] is None  # create redacts too


async def test_recipe_edit_keeps_past_entries(client, consented, slot_ids):
    full, nofibre = await _two(client)
    rid = (await client.post(URL, json=recipe(ing(full, 100), servings=1))).json()["id"]
    entry = await client.post(
        "/v1/meals", json={"recipe_id": rid, "servings": 1, "meal_slot_id": slot_ids["lunch"]}
    )
    assert entry.status_code == 201, entry.text
    before = entry.json()["nutrients"]
    put = await client.put(f"{URL}/{rid}", json=recipe(ing(nofibre, 100), servings=1))
    assert put.status_code == 200 and put.json()["per_100g"]["energy_kcal"] == 100.0
    again = (await client.get("/v1/meals")).json()
    assert [m["nutrients"] for m in again] == [before]  # the past entry is unchanged
    assert before["energy_kcal"] == 200.0


async def test_deleted_custom_ingredient_unavailable(client, consented):
    full, nofibre = await _two(client)
    rid = (await client.post(URL, json=recipe(ing(full, 100), ing(nofibre, 100)))).json()["id"]
    assert (await client.delete(f"/v1/custom-foods/{full}")).status_code == 204
    got = (await client.get(f"{URL}/{rid}")).json()
    first, second = got["ingredients"]
    assert first["available"] is False and first["custom_food_id"] is None
    assert first["name"] == "Full" and first["grams"] == 100.0  # the snapshot stays
    assert second["available"] is True
    assert got["per_100g"]["energy_kcal"] == 150.0  # the stored values still stand
    # A PUT that re-sends the ingredient without a ref must replace it.
    gone = {"quantity": 100, "unit": "g"}
    r = await client.put(f"{URL}/{rid}", json=recipe(gone, ing(nofibre, 100)))
    assert r.status_code == 422 and r.json()["error"]["code"] == "invalid_product_ref"
    ok = await client.put(f"{URL}/{rid}", json=recipe(ing(nofibre, 200)))
    assert ok.status_code == 200 and all(i["available"] for i in ok.json()["ingredients"])


async def test_off_ingredient_attribution_kept(client, consented, slot_ids):
    full, _ = await _two(client)
    r = await client.post(
        URL, json=recipe(ing(full, 100), {"barcode": OFF_BARCODE, "quantity": 50, "unit": "g"})
    )
    assert r.status_code == 201, r.text
    out = r.json()
    off_row = out["ingredients"][1]
    assert off_row["source_kind"] == "off" and off_row["barcode"] == OFF_BARCODE
    assert off_row["attribution"] == "attribution.off"
    assert out["attributions"] == ["attribution.off"]
    entry = await client.post(
        "/v1/meals", json={"recipe_id": out["id"], "grams": 100, "meal_slot_id": slot_ids["lunch"]}
    )
    assert entry.json()["attribution"] == "attribution.off"  # the ODbL credit follows the entry
    assert entry.json()["attributions"] == ["attribution.off"]


async def test_usda_food_ingredient(client, consented, food_ids):
    r = await client.post(
        URL, json=recipe({"food_id": food_ids["171844"], "quantity": 2, "unit": "roti"})
    )
    assert r.status_code == 201, r.text
    row = r.json()["ingredients"][0]
    assert row["source_kind"] == "food" and row["grams"] == 136.0
    assert r.json()["attributions"] == ["attribution.usda_fdc"]


async def test_retired_dish_refused_as_ingredient(client, consented, food_ids, db_session):
    from sqlalchemy import update

    from app.features.foods.models import Food

    await db_session.execute(
        update(Food).where(Food.source_code == "dal_tadka").values(review_status="retired")
    )
    r = await client.post(
        URL, json=recipe({"food_id": food_ids["dal_tadka"], "quantity": 100, "unit": "g"})
    )
    assert r.status_code == 422 and r.json()["error"]["code"] == "food_retired"


async def test_other_account_404(client, consented, grant, login):
    full, _ = await _two(client)
    rid = (await client.post(URL, json=recipe(ing(full, 100)))).json()["id"]
    await grant(ACC_B)
    login(ACC_B)
    assert (await client.get(URL)).json()["items"] == []
    for call in (
        client.get(f"{URL}/{rid}"),
        client.put(f"{URL}/{rid}", json=recipe(ing(full, 100))),
        client.delete(f"{URL}/{rid}"),
    ):
        r = await call
        assert r.status_code == 404 or r.json()["error"]["code"] == "custom_food_not_found"
    # B cannot build a recipe from A's custom food.
    r = await client.post(URL, json=recipe(ing(full, 100)))
    assert r.status_code == 404 and r.json()["error"]["code"] == "custom_food_not_found"
    login(ACC_A)
    assert (await client.get(f"{URL}/{rid}")).status_code == 200


async def test_client_id_retry(client, consented):
    full, _ = await _two(client)
    cid = str(uuid4())
    first = await client.post(URL, json=recipe(ing(full, 100), client_id=cid))
    again = await client.post(URL, json=recipe(ing(full, 50), client_id=cid, name="Changed"))
    assert (first.status_code, again.status_code) == (201, 200)
    assert again.json()["id"] == first.json()["id"] and again.json()["name"] == "Stew"
    assert len((await client.get(URL)).json()["items"]) == 1


async def test_delete_keeps_entries(client, consented, slot_ids):
    full, _ = await _two(client)
    rid = (await client.post(URL, json=recipe(ing(full, 100), servings=2))).json()["id"]
    entry = (
        await client.post(
            "/v1/meals",
            json={"recipe_id": rid, "servings": 1, "meal_slot_id": slot_ids["lunch"]},
        )
    ).json()
    assert (await client.delete(f"{URL}/{rid}")).status_code == 204
    assert (await client.delete(f"{URL}/{rid}")).status_code == 404
    kept = next(m for m in (await client.get("/v1/meals")).json() if m["id"] == entry["id"])
    assert kept["recipe_id"] is None and kept["product_name"] == "Stew"
    assert kept["nutrients"] == entry["nutrients"]


async def test_list_cursor_and_bounds(client, consented, clock):
    full, _ = await _two(client)
    for i in range(3):
        clock.set(f"2026-11-07T07:0{i}:00+00:00")
        assert (await client.post(URL, json=recipe(ing(full, 10), name=f"R{i}"))).status_code == 201
    page = (await client.get(URL, params={"limit": 2})).json()
    assert [i["name"] for i in page["items"]] == ["R2", "R1"] and page["next_cursor"]
    rest = (await client.get(URL, params={"limit": 2, "cursor": page["next_cursor"]})).json()
    assert [i["name"] for i in rest["items"]] == ["R0"] and rest["next_cursor"] is None
    for limit in (0, 101):
        assert (await client.get(URL, params={"limit": limit})).status_code == 422
