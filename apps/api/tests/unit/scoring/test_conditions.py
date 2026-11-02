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
