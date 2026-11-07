"""foods_get and foods_units_list (Plan 12 Task 4; G11, G14, G15)."""

from uuid import uuid4

import pytest

from tests.api.foods.conftest import ACC_A, G1_SETTINGS, OFF_BARCODE

NUTRIENT_KEYS = {
    "energy_kcal", "sugars_g", "salt_g", "protein_g", "fat_g", "sat_fat_g", "carbs_g", "fibre_g",
}  # fmt: skip


def _codes(detail) -> list[str]:
    return [u["code"] for u in detail["units"]]


async def _get(client, kind, ident, **params):
    r = await client.get(f"/v1/foods/{kind}/{ident}", params=params)
    assert r.status_code == 200, r.text
    return r.json()


async def test_units_list(client, consented):
    r = await client.get("/v1/foods/units")
    assert r.status_code == 200
    units = r.json()
    assert [u["code"] for u in units][:3] == ["g", "ml", "serving"] and len(units) == 17
    katori = next(u for u in units if u["code"] == "katori")
    assert katori == {"code": "katori", "kind": "volume", "ml": 200.0, "grams": None}
    assert next(u for u in units if u["code"] == "g")["grams"] == 1.0


async def test_detail_lists_only_resolving_units(client, consented, food_ids):
    roti = await _get(client, "food", food_ids["171844"])  # packaged roti, 68 g a piece
    assert _codes(roti) == ["g", "roti"]
    by = {u["code"]: u for u in roti["units"]}
    assert by["roti"] == {
        "code": "roti", "kind": "count", "ml": None, "grams_per_unit": 68.0,
        "source": "portion_global", "user_override": False,
    }  # fmt: skip
    dal_tadka = await _get(client, "food", food_ids["dal_tadka"])
    assert _codes(dal_tadka) == ["g"]  # no density, no portion, no serving: only grams
    pigeon = await _get(client, "food", food_ids["172437"])  # cooked, density 0.71
    assert "katori" in _codes(pigeon) and "roti" not in _codes(pigeon)
    katori = next(u for u in pigeon["units"] if u["code"] == "katori")
    assert katori["grams_per_unit"] == 142.0 and katori["source"] == "density"
    # Never a unit with nothing to convert it by, for any seeded food.
    for ident in list(food_ids.values())[:40]:
        detail = await _get(client, "food", ident)
        for u in detail["units"]:
            assert u["grams_per_unit"] > 0
            assert u["code"] != "serving" or detail["serving_g"] is not None


async def test_default_unit(client, consented, food_ids):
    assert (await _get(client, "food", food_ids["171844"]))["default_unit"] == "roti"
    assert (await _get(client, "food", food_ids["172437"]))["default_unit"] == "katori"
    assert (await _get(client, "food", food_ids["dal_tadka"]))["default_unit"] == "g"
    egg = await _get(client, "food", food_ids["egg_bhurji"])  # the whole batch is 1 serving
    assert egg["default_unit"] == "serving" and egg["serving_g"] == 150.0
    eggs = await _get(client, "food", food_ids["171287"])  # raw egg: sizes
    assert eggs["default_unit"] == "piece_small"  # the first count unit offered
    assert {"piece_large", "piece_medium", "piece_small"} <= set(_codes(eggs))


async def test_settable_units(client, consented, food_ids):
    dal_tadka = await _get(client, "food", food_ids["dal_tadka"])
    settable = dal_tadka["settable_units"]
    assert {"katori", "roti", "piece", "tbsp"} <= set(settable)
    assert "g" not in settable and "serving" not in settable
    assert not set(settable) & set(_codes(dal_tadka))
    pigeon = await _get(client, "food", food_ids["172437"])
    assert "katori" not in pigeon["settable_units"] and "roti" in pigeon["settable_units"]


async def test_dish_shows_ingredients_and_review_pending(client, consented, food_ids):
    d = await _get(client, "food", food_ids["dal_tadka"])
    assert d["dish"]["cooked_weight_g"] == 350 and d["dish"]["servings"] is None
    first = d["dish"]["ingredients"][0]
    assert first["name"].startswith("Pigeon peas") and first["grams"] == 50
    assert len(d["dish"]["ingredients"]) == 9
    assert d["review_pending"] is True and d["basis"] == "g"
    assert d["attribution"] == "attribution.smartnutri_recipe"
    assert d["attributions"] == ["attribution.smartnutri_recipe", "attribution.usda_fdc"]
    assert d["per_100"]["sugars_g"] is None  # unknown on an ingredient: null, never 0
    assert d["per_100"]["sat_fat_g"] is None and d["per_100"]["energy_kcal"] > 0
    fdc = await _get(client, "food", food_ids["172437"])
    assert fdc["dish"] is None and fdc["licence"] == "CC0 1.0" and fdc["review_pending"] is True


async def test_food_detail_redacted(client, g1, food_ids):
    ident = food_ids["172437"]
    shown = await _get(client, "food", ident)
    assert shown["per_100"]["energy_kcal"] == 121.0
    assert shown["numbers_hidden"] == {"energy": False, "macros": False}
    for display, energy_hidden, macros_hidden in (
        ("hide_energy", True, False),
        ("hide_all", True, True),
    ):
        r = await client.put(
            "/v1/targets/settings", json={**G1_SETTINGS, "numbers_display": display}
        )
        assert r.status_code == 200, r.text
        d = await _get(client, "food", ident)
        assert d["numbers_hidden"] == {"energy": energy_hidden, "macros": macros_hidden}
        assert d["per_100"]["energy_kcal"] is None
        if macros_hidden:
            assert set(d["per_100"]) == NUTRIENT_KEYS
            assert all(v is None for v in d["per_100"].values())
        else:
            assert d["per_100"]["protein_g"] is not None
        assert "katori" in _codes(d)  # the units stay (grams are not hidden)
        assert d["units"][0]["grams_per_unit"] > 0


async def test_unknown_food_404(client, consented, seeded):
    for ident in (str(uuid4()), "nope"):
        r = await client.get(f"/v1/foods/food/{ident}")
        assert r.status_code == 404 and r.json()["error"]["code"] == "food_not_found", ident
    r = await client.get(f"/v1/foods/product/{uuid4()}")
    assert r.status_code == 404 and r.json()["error"]["code"] == "product_not_found"
    r = await client.get("/v1/foods/recipe/1")  # a recipe kind since slice 4
    assert r.status_code == 404 and r.json()["error"]["code"] == "recipe_not_found"
    r = await client.get(f"/v1/foods/custom_food/{uuid4()}")
    assert r.status_code == 404 and r.json()["error"]["code"] == "custom_food_not_found"
    assert (await client.get("/v1/foods/nope/1")).status_code == 422


async def test_non_primary_member_422(client, consented, add_member, food_ids):
    other = await add_member(ACC_A, name="Dad", relation="parent")
    r = await client.get(
        f"/v1/foods/food/{food_ids['172437']}", params={"member_id": str(other.id)}
    )
    assert r.status_code == 422 and r.json()["error"]["code"] == "diary_member_not_enabled"
    r = await client.get(f"/v1/foods/food/{food_ids['172437']}", params={"member_id": str(uuid4())})
    assert r.status_code == 404  # a foreign member


async def test_off_product_detail(client, consented):
    d = await _get(client, "off", OFF_BARCODE)
    assert d["kind"] == "off" and d["name"] == "OFF Namkeen" and d["basis"] == "g"
    assert d["attribution"] == "attribution.off" and d["attributions"] == ["attribution.off"]
    assert d["review_pending"] is False and d["dish"] is None and d["licence"] is None
    assert _codes(d)[0] == "g"


# ---- Plan 12 slice 4: custom foods and recipes


async def _custom(client, **cols):
    body = {
        "name": "Shake", "basis": "ml", "values_per": "100", "density_g_per_ml": 1.05,
        "serving_g": 300, "nutrients": {"energy_kcal": 60, "protein_g": 4},
        "portions": [{"unit": "piece", "grams_per_unit": 33}],
    } | cols  # fmt: skip
    r = await client.post("/v1/custom-foods", json=body)
    assert r.status_code == 201, r.text
    return r.json()


async def test_custom_food_detail_units(client, consented):
    food = await _custom(client)
    d = await _get(client, "custom_food", food["id"])
    assert (d["kind"], d["name"], d["basis"], d["serving_g"]) == (
        "custom_food",
        "Shake",
        "ml",
        300.0,
    )
    assert d["attribution"] is None and d["attributions"] == [] and d["review_pending"] is False
    assert d["recipe_incomplete"] == [] and d["dish"] is None and d["licence"] is None
    by = {u["code"]: u for u in d["units"]}
    assert by["ml"] == {
        "code": "ml", "kind": "volume", "ml": 1.0, "grams_per_unit": 1.0,
        "source": "volume_basis", "user_override": False,
    }  # fmt: skip
    assert by["katori"]["grams_per_unit"] == 200.0 and by["katori"]["source"] == "volume_basis"
    assert by["g"]["source"] == "mass" and by["g"]["grams_per_unit"] == pytest.approx(1 / 1.05)
    assert by["serving"]["grams_per_unit"] == 300.0
    assert by["piece"]["source"] == "portion_user" and by["piece"]["user_override"] is True
    assert "piece" not in d["settable_units"] and "roti" in d["settable_units"]
    assert d["per_100"]["energy_kcal"] == 60.0 and d["per_100"]["fibre_g"] is None
    # The account may set its own grams for a unit, and clear it.
    r = await client.put(
        f"/v1/foods/custom_food/{food['id']}/portions/roti", json={"grams_per_unit": 25}
    )
    assert r.status_code == 200
    assert {u["code"]: u for u in r.json()["units"]}["roti"]["grams_per_unit"] == 25.0
    assert (
        await client.delete(f"/v1/foods/custom_food/{food['id']}/portions/roti")
    ).status_code == 204
    d = await _get(client, "custom_food", food["id"])
    assert "roti" not in {u["code"] for u in d["units"]}


async def test_custom_food_detail_redacted(client, g1):
    food = await _custom(client)
    await client.put("/v1/targets/settings", json={**G1_SETTINGS, "numbers_display": "hide_all"})
    d = await _get(client, "custom_food", food["id"])
    assert all(v is None for v in d["per_100"].values()) and d["numbers_hidden"]["macros"] is True
    assert d["units"]  # the units stay
    # The custom food's own route is not redacted: it is the label the user typed (G15).
    mine = (await client.get("/v1/custom-foods")).json()["items"][0]
    assert mine["per_100"]["energy_kcal"] == 60.0


async def test_recipe_detail_strict_and_incomplete(client, consented):
    full = await _custom(
        client, name="Full", basis="g", density_g_per_ml=None, portions=[],
        nutrients={"energy_kcal": 200, "protein_g": 10, "fibre_g": 4},
    )  # fmt: skip
    nofibre = await _custom(
        client, name="No fibre", basis="g", density_g_per_ml=None, portions=[],
        nutrients={"energy_kcal": 100, "protein_g": 5},
    )  # fmt: skip
    recipe = await client.post(
        "/v1/recipes",
        json={
            "name": "Mix",
            "servings": 2,
            "ingredients": [
                {"custom_food_id": full["id"], "quantity": 100, "unit": "g"},
                {"custom_food_id": nofibre["id"], "quantity": 100, "unit": "g"},
            ],
        },
    )
    rid = recipe.json()["id"]
    assert recipe.json()["per_100g"]["fibre_g"] == 2.0  # the recipe screen: at least
    d = await _get(client, "recipe", rid)
    assert (d["kind"], d["basis"], d["serving_g"]) == ("recipe", "g", 100.0)
    assert d["per_100"]["fibre_g"] is None  # strict: never the partial sum
    assert d["per_100"]["energy_kcal"] == 150.0 and d["per_100"]["protein_g"] == 7.5
    assert d["recipe_incomplete"] == recipe.json()["incomplete_nutrients"]
    assert "fibre_g" in d["recipe_incomplete"]
    assert [u["code"] for u in d["units"]] == ["g", "serving"] and d["default_unit"] == "serving"
    assert d["settable_units"] == [] and d["review_pending"] is False
    r = await client.put(f"/v1/foods/recipe/{rid}/portions/roti", json={"grams_per_unit": 25})
    assert r.status_code == 422 and r.json()["error"]["code"] == "unit_not_supported"
    assert (await client.delete(f"/v1/foods/recipe/{rid}/portions/roti")).status_code == 204


async def test_custom_and_recipe_detail_other_account_404(client, consented, grant, login):
    from tests.api.foods.conftest import ACC_B

    food = await _custom(client)
    recipe = await client.post(
        "/v1/recipes",
        json={
            "name": "R", "servings": 1,
            "ingredients": [{"custom_food_id": food["id"], "quantity": 100, "unit": "ml"}],
        },
    )  # fmt: skip
    assert recipe.status_code == 201, recipe.text
    await grant(ACC_B)
    login(ACC_B)
    for kind, ident, code in (
        ("custom_food", food["id"], "custom_food_not_found"),
        ("recipe", recipe.json()["id"], "recipe_not_found"),
    ):
        r = await client.get(f"/v1/foods/{kind}/{ident}")
        assert r.status_code == 404 and r.json()["error"]["code"] == code
