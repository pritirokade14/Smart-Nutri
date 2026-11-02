from dataclasses import replace

import pytest

from app.scoring.claims import check_claims
from app.scoring.conditions import condition_reasons
from app.scoring.models import Category, Member, Nutrients, Status
from app.scoring.nutriscore import compute_nutriscore


def _reasons(product, member, cfg):
    return condition_reasons(
        product, member, compute_nutriscore(product), check_claims(product, cfg), cfg
    )


def _codes(product, member, cfg):
    return {r.code for r in _reasons(product, member, cfg)}


def _pairs(product, member, cfg):
    return {(r.code, r.severity) for r in _reasons(product, member, cfg)}


def test_diabetic_and_sugar_free_biscuit(sf_biscuit, diabetic_adult, cfg):
    assert _codes(sf_biscuit, diabetic_adult, cfg) == {"misleading_sugar_claim", "hidden_sugars"}


def test_diabetic_and_curd_ok(curd, diabetic_adult, cfg):
    assert _codes(curd, diabetic_adult, cfg) == set()


def test_bp_parent_and_namkeen(namkeen, bp_parent, cfg):
    assert _codes(namkeen, bp_parent, cfg) == {"salt_high"}


def test_weight_loss_and_oats(oats, weight_loss_adult, cfg):
    assert _codes(oats, weight_loss_adult, cfg) == set()


def test_weight_loss_good_protein(curd, weight_loss_adult, cfg):
    p = replace(
        curd,
        per_100g=Nutrients(
            energy_kcal=100, protein_g=10, sugars_g=1, fat_g=1, sat_fat_g=0.5, salt_g=0.1
        ),
    )
    assert _codes(p, weight_loss_adult, cfg) == {"good_protein_density"}


def test_child_cola(cola, milk_allergic_child, cfg):
    assert {"child_sugar_high", "child_caffeine"} <= _codes(cola, milk_allergic_child, cfg)
    r = next(x for x in _reasons(cola, milk_allergic_child, cfg) if x.code == "child_sugar_high")
    assert r.params["limit_g"] == 24


def test_infant_cola(cola, infant, cfg):
    assert {"infant_added_sugar"} <= _codes(cola, infant, cfg)


def test_no_age_skips_child_rules(cola, no_age, cfg):
    assert _codes(cola, no_age, cfg) == set()


def test_missing_sugar_for_diabetic_is_unknown(curd, diabetic_adult, cfg):
    p = replace(curd, per_100g=replace(curd.per_100g, sugars_g=None))
    assert ("nutrient_missing", Status.UNKNOWN) in _pairs(p, diabetic_adult, cfg)


def test_age_group_boundaries(cola, cfg):
    assert "child_sugar_high" not in _codes(cola, Member(id="x", name="x", age=13), cfg)
    assert "child_sugar_high" in _codes(cola, Member(id="x", name="x", age=12), cfg)
    assert "infant_added_sugar" not in _codes(cola, Member(id="x", name="x", age=2), cfg)
    assert "child_caffeine" in _codes(cola, Member(id="x", name="x", age=2), cfg)


def _m(age=None, conditions=(), goal=None):
    return Member(id="x", name="x", age=age, conditions=conditions, goal=goal)


def test_infant_caffeine_zero_sugar(cola, cfg):
    p = replace(
        cola,
        per_100g=Nutrients(energy_kcal=0, sugars_g=0, salt_g=0),
        ingredients=("water", "aspartame", "caffeine"),
    )
    assert "infant_caffeine" in _codes(p, _m(age=1), cfg)
    assert "infant_caffeine" in _codes(replace(p, ingredients=("coffee",)), _m(age=1), cfg)


def test_infant_unknown_ingredients(cola, cfg):
    p = replace(cola, ingredients=(), per_100g=Nutrients(sugars_g=40, salt_g=3))
    r = [x for x in _reasons(p, _m(age=1), cfg) if x.code == "ingredients_missing"]
    assert len(r) == 1 and r[0].severity == Status.UNKNOWN and r[0].params == {"rule": "infant"}
    low = replace(cola, extraction_confidence=0.1)
    assert ("ingredients_missing", Status.UNKNOWN) in _pairs(low, _m(age=1), cfg)


def test_child_unknown_ingredients(cola, cfg):
    p = replace(cola, ingredients=())
    r = [x for x in _reasons(p, _m(age=8), cfg) if x.code == "ingredients_missing"]
    assert len(r) == 1 and r[0].params == {"rule": "child"}


def test_condition_normalisation(curd, cfg):
    p = replace(curd, per_100g=Nutrients(sugars_g=None, salt_g=None, carbs_g=1))
    for cond, rule in (
        ("Diabetes", "blood_sugar"),
        (" DIABETES", "blood_sugar"),
        ("Hypertension", "hypertension"),
    ):
        rules = [r.params["rule"] for r in _reasons(p, _m(age=40, conditions=(cond,)), cfg)]
        assert rule in rules, cond
    w = replace(curd, per_100g=Nutrients(energy_kcal=None, protein_g=1))
    for goal in ("Weight Loss", "weight loss", "weight-loss"):
        rules = [r.params["rule"] for r in _reasons(w, _m(age=40, goal=goal), cfg)]
        assert "weight_loss" in rules, goal


def test_prediabetes_and_pcos(cola, cfg):
    for c in ("prediabetes", "pcos"):
        assert "sugar_high" in _codes(cola, _m(age=30, conditions=(c,)), cfg)


def test_sodium_only_hypertension(namkeen, cfg):
    p = replace(namkeen, per_100g=Nutrients(sodium_mg=1000))
    assert "salt_high" in _codes(p, _m(age=40, conditions=("hypertension",)), cfg)


def test_child_missing_salt(cola, cfg):
    p = replace(cola, per_100g=Nutrients(sugars_g=1))
    r = [x for x in _reasons(p, _m(age=8), cfg) if x.code == "nutrient_missing"]
    assert [x.params for x in r] == [{"nutrient": "salt", "rule": "child"}]
    assert r[0].severity == Status.UNKNOWN


def test_child_salt_high_params(namkeen, cfg):  # C10: own code, not hypertension's salt_high
    rs = _reasons(namkeen, _m(age=8), cfg)
    assert "salt_high" not in {x.code for x in rs}
    r = next(x for x in rs if x.code == "child_salt_high")
    assert r.severity == Status.CAUTION and r.params == {"salt_g": 2.5}


def test_carbs_basis(sf_biscuit, cfg):
    d = _m(age=40, conditions=("diabetes",))
    p = replace(sf_biscuit, serving_size_g=None, per_100g=replace(sf_biscuit.per_100g, carbs_g=72))
    r = next(x for x in _reasons(p, d, cfg) if x.code == "carbs_per_serving_high")
    assert r.params == {"carbs_g": 72.0, "basis": "per_100g"}
    p = replace(sf_biscuit, serving_size_g=50)
    r = next(x for x in _reasons(p, d, cfg) if x.code == "carbs_per_serving_high")
    assert r.params == {"carbs_g": 36.0, "basis": "per_serving"}


def test_child_band_edges(cola, cfg):
    p = replace(cola, serving_size_g=100, per_100g=Nutrients(sugars_g=10, salt_g=0))
    for age, limit in {2: 19, 6: 19, 7: 24, 10: 24, 11: 30, 12: 30}.items():
        r = next(x for x in _reasons(p, _m(age=age), cfg) if x.code.startswith("child_sugar"))
        assert r.params["limit_g"] == limit, age


def test_child_no_serving_uses_per_100g(cola, cfg):
    p = replace(cola, serving_size_g=None, per_100g=Nutrients(sugars_g=10.6, salt_g=0))
    r = next(x for x in _reasons(p, _m(age=8), cfg) if x.code.startswith("child_sugar"))
    assert r.params["pct"] == round(10.6 / 24 * 100, 2)


def test_infant_honey_and_salt(cola, cfg):
    p = replace(cola, ingredients=("Honey",))
    assert {"infant_added_sugar", "infant_honey"} <= _codes(p, _m(age=1), cfg)
    p = replace(cola, ingredients=("Iodised Salt",))
    assert "infant_added_salt" in _codes(p, _m(age=1), cfg)


# --- C5: condition aliases + condition_unrecognised (Ruling R24) ---


@pytest.mark.parametrize(
    "raw",
    [
        "Type 2 Diabetes",
        "type-1 diabetes",
        "T2DM",
        "t1dm",
        "Diabetic",
        "sugar",
        "Gestational Diabetes",
        "Pre-Diabetes",
        "prediabetic",
        "Borderline Diabetes",
        "PCOD",
    ],
)
def test_blood_sugar_aliases(cola, cfg, raw):
    pairs = _pairs(cola, _m(age=40, conditions=(raw,)), cfg)
    assert ("sugar_high", Status.AVOID) in pairs, raw
    assert "condition_unrecognised" not in {c for c, _ in pairs}


@pytest.mark.parametrize("raw", ["High BP", "high blood pressure", "BP", "Blood Pressure"])
def test_hypertension_aliases(namkeen, cfg, raw):
    assert ("salt_high", Status.AVOID) in _pairs(namkeen, _m(age=60, conditions=(raw,)), cfg), raw


@pytest.mark.parametrize("raw", ["lose weight", "Obesity", "overweight", "weight-loss"])
def test_weight_loss_aliases_as_goal_and_condition(namkeen, cfg, raw):
    assert "energy_dense" in _codes(namkeen, _m(age=40, goal=raw), cfg), raw
    assert "energy_dense" in _codes(namkeen, _m(age=40, conditions=(raw,)), cfg), raw


def test_unrecognised_condition_is_unknown(curd, cfg):
    rs = _reasons(curd, _m(age=40, conditions=("Kidney Stones", " ", "xyz")), cfg)
    got = [(r.code, r.severity, dict(r.params)) for r in rs if r.code == "condition_unrecognised"]
    assert got == [
        ("condition_unrecognised", Status.UNKNOWN, {"condition": "Kidney Stones"}),
        ("condition_unrecognised", Status.UNKNOWN, {"condition": "xyz"}),
    ]


def test_unrecognised_goal_is_ignored(curd, cfg):  # Ruling R34
    for goal in ("muscle gain", "Bulk Up"):
        assert "condition_unrecognised" not in _codes(curd, _m(age=40, goal=goal), cfg), goal
    rs = _reasons(curd, _m(age=40, conditions=("xyz",), goal="muscle gain"), cfg)
    assert [dict(r.params) for r in rs if r.code == "condition_unrecognised"] == [
        {"condition": "xyz"}
    ]


# --- C6: low extraction confidence -> nutrient_missing (Ruling R25) ---


def test_low_confidence_diabetic_is_unknown(curd, cfg):
    p = replace(curd, per_100g=replace(curd.per_100g, sugars_g=3), extraction_confidence=0.2)
    rs = _reasons(p, _m(age=40, conditions=("diabetes",)), cfg)
    missing = [dict(r.params) for r in rs if r.code == "nutrient_missing"]
    assert {"nutrient": "sugars_g", "rule": "blood_sugar", "reason": "low_confidence"} in missing
    assert all(r.severity == Status.UNKNOWN for r in rs if r.code == "nutrient_missing")


def test_low_confidence_hypertension_is_unknown(namkeen, cfg):
    p = replace(namkeen, per_100g=Nutrients(salt_g=0.2), extraction_confidence=0.2)
    rs = _reasons(p, _m(age=60, conditions=("hypertension",)), cfg)
    assert [dict(r.params) for r in rs if r.code == "nutrient_missing"] == [
        {"nutrient": "salt", "rule": "hypertension", "reason": "low_confidence"}
    ]


def test_confidence_at_threshold_is_trusted(curd, cfg):
    p = replace(curd, extraction_confidence=0.7)
    assert _codes(p, _m(age=40, conditions=("diabetes",)), cfg) == set()


# --- C7: drink sugar bands for blood_sugar (Ruling R26) ---


def test_blood_sugar_uses_drink_bands(cola, curd, cfg):
    d = _m(age=40, conditions=("diabetes",))
    drink = replace(cola, ingredients=("water",), per_100g=Nutrients(sugars_g=12, carbs_g=12))
    assert ("sugar_high", Status.AVOID) in _pairs(drink, d, cfg)
    drink3 = replace(drink, per_100g=Nutrients(sugars_g=3, carbs_g=3))
    assert ("sugar_moderate", Status.CAUTION) in _pairs(drink3, d, cfg)
    food3 = replace(curd, per_100g=replace(curd.per_100g, sugars_g=3))
    assert "sugar_moderate" not in _codes(food3, d, cfg)


def test_diabetic_drink_bands_r31(cola, cfg):  # Ruling R31: drink avoid 5.0, caution 2.5
    d = _m(age=40, conditions=("diabetes",))
    juice = replace(
        cola,
        ingredients=("orange juice",),
        serving_size_g=200,
        per_100g=Nutrients(sugars_g=10, carbs_g=10),
    )
    assert ("sugar_high", Status.AVOID) in _pairs(juice, d, cfg)
    drink3 = replace(juice, per_100g=Nutrients(sugars_g=3, carbs_g=3))
    pairs = _pairs(drink3, d, cfg)
    assert ("sugar_moderate", Status.CAUTION) in pairs and "sugar_high" not in {c for c, _ in pairs}
    edge = replace(juice, per_100g=Nutrients(sugars_g=5.0, carbs_g=5.0))
    assert "sugar_high" not in _codes(edge, d, cfg)


# --- C8: infant nutrient rules (Ruling R27) ---


def _plain(cola, **n):
    return replace(cola, category=Category.GENERAL, ingredients=("rice",), per_100g=Nutrients(**n))


def test_infant_high_sugar_unknown_ingredients(cola, cfg):  # Ruling R32
    p = replace(_plain(cola, sugars_g=40, salt_g=0), ingredients=())
    rs = _reasons(p, _m(age=1), cfg)
    r = next(x for x in rs if x.code == "infant_sugar_high")
    assert r.severity == Status.AVOID and r.params == {"sugars_g": 40.0}
    assert ("ingredients_missing", Status.UNKNOWN) in {(x.code, x.severity) for x in rs}


def test_infant_sugar_numeric_rule_skipped_when_ingredients_known(cola, cfg):  # Ruling R32
    formula = replace(
        _plain(cola, sugars_g=7, salt_g=0.1),
        ingredients=("skimmed milk powder", "lactose", "vegetable oil"),
    )
    codes = _codes(formula, _m(age=1), cfg)
    assert "infant_sugar_high" not in codes and "infant_added_sugar" not in codes
    assert "nutrient_missing" not in codes
    sweet = _plain(cola, sugars_g=40, salt_g=0)  # known ingredients ("rice"), no sugar term
    assert "infant_sugar_high" not in _codes(sweet, _m(age=1), cfg)


def test_infant_high_salt_without_salt_term(cola, cfg):
    rs = _reasons(_plain(cola, sugars_g=0, salt_g=3), _m(age=1), cfg)
    r = next(x for x in rs if x.code == "infant_salt_high")
    assert r.severity == Status.AVOID and r.params == {"salt_g": 3.0}


def test_infant_plain_milk_sugar_not_flagged(cola, cfg):
    codes = _codes(_plain(cola, sugars_g=4.7, salt_g=0.1), _m(age=1), cfg)
    assert "infant_sugar_high" not in codes and "infant_salt_high" not in codes


def test_infant_missing_nutrients_unknown(cola, cfg):
    # Known ingredients: only salt is needed numerically (Ruling R32).
    rs = _reasons(_plain(cola), _m(age=1), cfg)
    assert [r.params["nutrient"] for r in rs if r.code == "nutrient_missing"] == ["salt"]
    # Unknown ingredients: sugar is needed too.
    rs = _reasons(replace(_plain(cola), ingredients=()), _m(age=1), cfg)
    assert sorted(r.params["nutrient"] for r in rs if r.code == "nutrient_missing") == [
        "salt",
        "sugars_g",
    ]
    assert all(r.params["rule"] == "infant" for r in rs if r.code == "nutrient_missing")


# --- C9: child per-100 g floor ---


def test_child_small_serving_of_very_sweet_food_is_caution(cola, cfg):
    toffee = replace(_plain(cola, sugars_g=70, salt_g=0.1), serving_size_g=4)
    r = next(x for x in _reasons(toffee, _m(age=5), cfg) if x.code.startswith("child_sugar"))
    assert (r.code, r.severity) == ("child_sugar_moderate", Status.CAUTION)
    assert r.params == {"pct": round(70 / 19 * 100, 2), "limit_g": 19, "basis": "per_100g"}


def test_child_sugar_params_have_basis(cola, cfg):
    r = next(x for x in _reasons(cola, _m(age=8), cfg) if x.code == "child_sugar_high")
    assert r.params["basis"] == "per_serving"
    p = replace(cola, serving_size_g=None)
    r = next(x for x in _reasons(p, _m(age=8), cfg) if x.code.startswith("child_sugar"))
    assert r.params["basis"] == "per_100g"


# --- C11: added sugars for blood_sugar (Ruling R28) ---


def test_added_sugar_term_is_caution_for_diabetic(curd, cfg):
    p = replace(curd, ingredients=(*curd.ingredients, "sugar"))
    rs = _reasons(p, _m(age=40, conditions=("diabetes",)), cfg)
    r = next(x for x in rs if x.code == "added_sugars")
    assert r.severity == Status.CAUTION and r.params == {"ingredients": ["sugar"]}


def test_contradicted_no_refined_sugar_is_misleading(curd, cfg):
    p = replace(curd, ingredients=(*curd.ingredients, "cane sugar"), claims=("No Refined Sugar",))
    rs = _reasons(p, _m(age=40, conditions=("diabetes",)), cfg)
    assert ("misleading_sugar_claim", Status.AVOID) in {(r.code, r.severity) for r in rs}
