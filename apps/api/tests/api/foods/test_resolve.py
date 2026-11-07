"""load_food, ref_from_ids and the unit table (Plan 12 Task 2). Real test DB, fake OFF."""

from decimal import Decimal
from uuid import uuid4

import pytest

from app.core.errors import ApiError
from app.features.foods.models import FoodPortion
from app.features.foods.resolve import FoodRef, load_food, ref_from_ids, unit_table
from app.features.foods.units import resolve_units
from app.features.products.models import Product
from tests.api.foods.conftest import ACC_A, ACC_B, make_food, portion

D = Decimal


async def test_unit_table_has_the_17_rows(db_session):
    table = await unit_table(db_session)
    assert len(table) == 17 and table["katori"].ml == D("200") and table["g"].grams == D("1")
    assert list(table) == sorted(table, key=lambda c: table[c].sort)


async def test_load_food_seed_row(db_session, settings, fake_off, accounts, dal):
    db_session.add(portion(dal.id, "roti", 40))
    await db_session.flush()
    loaded = await load_food(
        db_session, fake_off, FoodRef("food", str(dal.id)), account_id=ACC_A, settings=settings
    )
    assert loaded.name == "Lentils, cooked" and loaded.basis == "g"
    assert loaded.units.density_g_per_ml == D("0.71")
    assert loaded.units.global_portions == {"roti": D("40")}
    assert loaded.per_100.energy_kcal == 116.0 and loaded.per_100.sat_fat_g is None
    assert (loaded.attribution, loaded.attributions) == (
        "attribution.usda_fdc",
        ("attribution.usda_fdc",),
    )
    assert loaded.licence == "CC0 1.0" and loaded.food_id == dal.id and loaded.dish is None
    table = await unit_table(db_session)
    codes = [r.code for r in resolve_units(loaded.units, table)]
    assert "katori" in codes and "roti" in codes and "piece" not in codes


async def test_load_dish_keeps_both_credits(db_session, settings, fake_off, accounts):
    dish = make_food(
        "dal_tadka",
        "Dal tadka",
        source="smartnutri_recipe",
        recipe={
            "ingredients": [{"fdc_id": "1", "name": "Toor dal", "grams": 50}],
            "cooked_weight_g": 350,
            "servings": None,
        },
    )
    db_session.add(dish)
    await db_session.flush()
    loaded = await load_food(
        db_session, fake_off, FoodRef("food", str(dish.id)), account_id=ACC_A, settings=settings
    )
    assert loaded.attribution == "attribution.smartnutri_recipe"
    assert loaded.attributions == ("attribution.smartnutri_recipe", "attribution.usda_fdc")
    assert loaded.dish == {
        "ingredients": [{"name": "Toor dal", "grams": 50}],
        "cooked_weight_g": 350,
        "servings": None,
    }


async def test_load_food_user_portion_scoped_to_account(
    db_session, settings, fake_off, accounts, dal
):
    db_session.add_all(
        [
            portion(dal.id, "roti", 68),
            portion(dal.id, "roti", 35, account_id=ACC_A),
            portion(dal.id, "roti", 90, account_id=ACC_B),
        ]
    )
    await db_session.flush()
    ref = FoodRef("food", str(dal.id))
    a = await load_food(db_session, fake_off, ref, account_id=ACC_A, settings=settings)
    b = await load_food(db_session, fake_off, ref, account_id=ACC_B, settings=settings)
    assert (a.units.user_portions, a.units.global_portions) == (
        {"roti": D("35")},
        {"roti": D("68")},
    )
    assert b.units.user_portions == {"roti": D("90")}  # never A's value


async def test_load_product_units_serving_and_override(db_session, settings, fake_off, accounts):
    product = Product(
        name="Parle biscuit",
        category="general",
        source="label",
        verification_status="verified",
        per_100g={"energy_kcal": 450, "sugars_g": 20},
        serving_size_g=30,
    )
    db_session.add(product)
    await db_session.flush()
    db_session.add(
        FoodPortion(
            product_id=product.id,
            unit="piece",
            grams_per_unit=D("6"),
            source="user",
            account_id=ACC_A,
        )
    )
    await db_session.flush()
    ref = FoodRef("product", str(product.id))
    loaded = await load_food(db_session, fake_off, ref, account_id=ACC_A, settings=settings)
    assert loaded.units.serving_g == D("30") and loaded.units.user_portions == {"piece": D("6")}
    assert loaded.product_id == product.id and loaded.food_id is None
    other = await load_food(db_session, fake_off, ref, account_id=ACC_B, settings=settings)
    assert other.units.user_portions == {}
    codes = [r.code for r in resolve_units(loaded.units, await unit_table(db_session))]
    assert codes == ["g", "serving", "piece"]


async def test_load_off_product_by_barcode(db_session, settings, fake_off, accounts):
    from tests.api.meals.conftest import OFF_BARCODE

    loaded = await load_food(
        db_session, fake_off, FoodRef("off", OFF_BARCODE), account_id=ACC_A, settings=settings
    )
    assert loaded.off_barcode == OFF_BARCODE and loaded.product_id is None
    assert loaded.attributions == ("attribution.off",) and loaded.units.basis == "g"


async def test_unknown_food_404(db_session, settings, fake_off, accounts):
    for bad in (str(uuid4()), "not-a-uuid"):
        with pytest.raises(ApiError) as exc:
            await load_food(
                db_session, fake_off, FoodRef("food", bad), account_id=ACC_A, settings=settings
            )
        assert (exc.value.code, exc.value.status) == ("food_not_found", 404)
    with pytest.raises(ApiError) as exc:
        await load_food(
            db_session, fake_off, FoodRef("product", str(uuid4())), account_id=ACC_A,
            settings=settings,
        )  # fmt: skip
    assert exc.value.code == "product_not_found"


def test_ref_from_ids_exactly_one():
    fid, pid = uuid4(), uuid4()
    assert ref_from_ids(food_id=fid, product_id=None, barcode=None) == FoodRef("food", str(fid))
    assert ref_from_ids(food_id=None, product_id=pid, barcode=None) == FoodRef("product", str(pid))
    assert ref_from_ids(food_id=None, product_id=None, barcode="890") == FoodRef("off", "890")
    for kwargs in (
        {"food_id": None, "product_id": None, "barcode": None},
        {"food_id": fid, "product_id": pid, "barcode": None},
        {"food_id": fid, "product_id": None, "barcode": "890"},
    ):
        with pytest.raises(ApiError) as exc:
            ref_from_ids(**kwargs)
        assert (exc.value.code, exc.value.status) == ("invalid_product_ref", 422)


# ---- Plan 12 slice 4 (Task 10): custom foods and recipes


def make_custom(account_id, **cols):
    from app.features.custom_foods.models import CustomFood

    values = {
        "account_id": account_id,
        "name": "Protein bar",
        "basis": "g",
        "per_100": {"energy_kcal": 400.0, "protein_g": 30.0, "carbs_g": 40.0, "fat_g": 12.0},
        "entered": {},
        "serving_g": D("60"),
    } | cols
    return CustomFood(**values)


async def test_load_custom_food_units(db_session, settings, fake_off, accounts):
    from app.features.foods.models import FoodPortion

    drink = make_custom(
        ACC_A, name="Protein shake", basis="ml", density_g_per_ml=D("1.05"), serving_g=D("300")
    )
    db_session.add(drink)
    await db_session.flush()
    db_session.add(
        FoodPortion(
            custom_food_id=drink.id, unit="piece", grams_per_unit=D("33"),
            source="user", account_id=ACC_A,
        )
    )  # fmt: skip
    await db_session.flush()
    loaded = await load_food(
        db_session, fake_off, FoodRef("custom_food", str(drink.id)), account_id=ACC_A,
        settings=settings,
    )  # fmt: skip
    assert (loaded.name, loaded.basis) == ("Protein shake", "ml")
    assert loaded.units.density_g_per_ml == D("1.05") and loaded.units.serving_g == D("300")
    assert loaded.units.user_portions == {"piece": D("33")} and loaded.units.global_portions == {}
    assert loaded.custom_food_id == drink.id
    assert (loaded.food_id, loaded.product_id, loaded.off_barcode) == (None, None, None)
    assert loaded.attribution is None and loaded.attributions == ()
    assert loaded.per_100.protein_g == 30.0 and loaded.per_100.sat_fat_g is None
    table = await unit_table(db_session)
    codes = [r.code for r in resolve_units(loaded.units, table)]
    assert {"g", "ml", "serving", "piece", "katori"} <= set(codes)


async def test_custom_food_other_account_404(db_session, settings, fake_off, accounts):
    mine = make_custom(ACC_A)
    db_session.add(mine)
    await db_session.flush()
    for bad in (str(mine.id), str(uuid4()), "nope"):
        with pytest.raises(ApiError) as exc:
            await load_food(
                db_session, fake_off, FoodRef("custom_food", bad), account_id=ACC_B,
                settings=settings,
            )  # fmt: skip
        assert (exc.value.code, exc.value.status) == ("custom_food_not_found", 404)


async def _recipe(db_session, account_id, **cols):
    from app.features.recipes.models import Recipe

    values = {
        "account_id": account_id,
        "name": "Dal rice",
        "servings": D("2"),
        "cooked_weight_g": None,
        "total_raw_g": D("300"),
        "per_100g": {
            "energy_kcal": 120.0, "protein_g": 5.0, "fat_g": 2.0, "carbs_g": 20.0,
            "fibre_g": 1.5, "sugars_g": None, "salt_g": None, "sat_fat_g": None,
        },
        "incomplete_nutrients": ["fibre_g", "sugars_g", "salt_g", "sat_fat_g"],
    } | cols  # fmt: skip
    recipe = Recipe(**values)
    db_session.add(recipe)
    await db_session.flush()
    return recipe


async def test_load_recipe_strict_per_100(db_session, settings, fake_off, accounts):
    from app.features.recipes.models import RecipeIngredient

    recipe = await _recipe(db_session, ACC_A)
    for pos, attribution in enumerate(("attribution.usda_fdc", "attribution.off", None)):
        db_session.add(
            RecipeIngredient(
                recipe_id=recipe.id, account_id=ACC_A, position=pos, source_kind="off",
                off_barcode=f"89{pos}", name="x", quantity=D("1"), unit="g", grams=D("100"),
                basis="g", per_100={}, attribution=attribution,
            )
        )  # fmt: skip
    await db_session.flush()
    loaded = await load_food(
        db_session, fake_off, FoodRef("recipe", str(recipe.id)), account_id=ACC_A,
        settings=settings,
    )  # fmt: skip
    assert (loaded.name, loaded.basis) == ("Dal rice", "g")
    # An incomplete nutrient is unknown, never the partial sum; complete ones stay.
    assert loaded.per_100.energy_kcal == 120.0 and loaded.per_100.protein_g == 5.0
    assert loaded.per_100.fiber_g is None and loaded.per_100.sugars_g is None
    assert loaded.units.serving_g == D("150") and loaded.units.density_g_per_ml is None
    assert loaded.recipe_id == recipe.id and loaded.incomplete == (
        "fibre_g", "sugars_g", "salt_g", "sat_fat_g",
    )  # fmt: skip
    assert loaded.attributions == ("attribution.usda_fdc", "attribution.off")
    assert loaded.attribution == "attribution.off"  # ODbL credit wins when any ingredient is OFF
    codes = [r.code for r in resolve_units(loaded.units, await unit_table(db_session))]
    assert codes == ["g", "serving"]


async def test_load_recipe_cooked_weight_is_the_basis(db_session, settings, fake_off, accounts):
    recipe = await _recipe(db_session, ACC_A, cooked_weight_g=D("250"))
    loaded = await load_food(
        db_session, fake_off, FoodRef("recipe", str(recipe.id)), account_id=ACC_A,
        settings=settings,
    )  # fmt: skip
    assert loaded.units.serving_g == D("125")  # 250 g cooked / 2 servings


async def test_load_recipe_other_account_404(db_session, settings, fake_off, accounts):
    recipe = await _recipe(db_session, ACC_A)
    for bad in (str(recipe.id), str(uuid4()), "nope"):
        with pytest.raises(ApiError) as exc:
            await load_food(
                db_session, fake_off, FoodRef("recipe", bad), account_id=ACC_B, settings=settings
            )
        assert (exc.value.code, exc.value.status) == ("recipe_not_found", 404)


def test_ref_from_ids_custom_food_and_recipe():
    cid, rid, fid = uuid4(), uuid4(), uuid4()
    kw = {"food_id": None, "product_id": None, "barcode": None}
    assert ref_from_ids(**kw, custom_food_id=cid) == FoodRef("custom_food", str(cid))
    assert ref_from_ids(**kw, recipe_id=rid) == FoodRef("recipe", str(rid))
    for extra in ({"custom_food_id": cid, "recipe_id": rid}, {"custom_food_id": cid}):
        with pytest.raises(ApiError) as exc:
            ref_from_ids(**(kw | {"food_id": fid}), **extra)
        assert exc.value.code == "invalid_product_ref"
