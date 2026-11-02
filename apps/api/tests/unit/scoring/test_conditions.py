from dataclasses import replace

from app.scoring.claims import check_claims
from app.scoring.conditions import condition_reasons
from app.scoring.models import Member, Nutrients, Status
from app.scoring.nutriscore import compute_nutriscore


def _reasons(product, member, cfg):
    return condition_reasons(product, member, compute_nutriscore(product), check_claims(product, cfg), cfg)


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
    p = replace(curd, per_100g=Nutrients(energy_kcal=100, protein_g=10, sugars_g=1, fat_g=1, sat_fat_g=0.5, salt_g=0.1))
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
        assert "sugar_moderate" in _codes(cola, _m(age=30, conditions=(c,)), cfg)


def test_sodium_only_hypertension(namkeen, cfg):
    p = replace(namkeen, per_100g=Nutrients(sodium_mg=1000))
    assert "salt_high" in _codes(p, _m(age=40, conditions=("hypertension",)), cfg)


def test_child_missing_salt(cola, cfg):
    p = replace(cola, per_100g=Nutrients(sugars_g=1))
    r = [x for x in _reasons(p, _m(age=8), cfg) if x.code == "nutrient_missing"]
    assert [x.params for x in r] == [{"nutrient": "salt", "rule": "child"}]
    assert r[0].severity == Status.UNKNOWN


def test_child_salt_high_params(namkeen, cfg):
    r = next(x for x in _reasons(namkeen, _m(age=8), cfg) if x.code == "salt_high")
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
