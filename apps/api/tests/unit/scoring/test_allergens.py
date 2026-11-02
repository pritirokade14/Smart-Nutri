from dataclasses import replace

from app.scoring.allergens import allergen_reasons, detect_allergens
from app.scoring.models import AllergenState, Status


def test_biscuit_contains_milk_and_gluten_may_contain_soy(sf_biscuit, cfg):
    d = detect_allergens(sf_biscuit, cfg)
    assert d["milk"] == AllergenState.CONTAINS and d["gluten"] == AllergenState.CONTAINS
    assert d["soy"] == AllergenState.MAY_CONTAIN  # bare "ins 322"


def test_may_contain_statement(curd, cfg):
    p = replace(curd, may_contain_statement="May contain traces of nuts and peanuts")
    d = detect_allergens(p, cfg)
    assert d["peanut"] == AllergenState.MAY_CONTAIN and d["tree_nut"] == AllergenState.MAY_CONTAIN


def test_coconut_milk_is_not_milk(curd, cfg):
    assert "milk" not in detect_allergens(replace(curd, ingredients=("coconut milk", "sugar")), cfg)


def test_hindi_peanut(curd, cfg):
    assert detect_allergens(replace(curd, ingredients=("मूंगफली", "नमक")), cfg)["peanut"] == AllergenState.CONTAINS


def test_custom_allergen_matched_literally(curd, cfg, peanut_allergic):
    p = replace(curd, ingredients=("kiwi pulp", "sugar"))
    m = replace(peanut_allergic, allergens=("kiwi",))
    assert [r.code for r in allergen_reasons(p, m, cfg)] == ["allergen_contains"]


def test_unknown_ingredients_never_ok(no_ingredients, cfg, peanut_allergic):
    rs = allergen_reasons(no_ingredients, peanut_allergic, cfg)
    assert [(r.code, r.severity) for r in rs] == [("allergen_unknown", Status.UNKNOWN)]


def test_low_confidence_is_unknown(namkeen, cfg, milk_allergic_child):
    rs = allergen_reasons(replace(namkeen, extraction_confidence=0.5), milk_allergic_child, cfg)
    assert rs[0].code == "allergen_unknown"


def test_peanut_allergy_on_namkeen(namkeen, cfg, peanut_allergic):
    assert allergen_reasons(namkeen, peanut_allergic, cfg)[0].severity == Status.AVOID


def test_member_allergen_key_case_insensitive(namkeen, cfg, peanut_allergic):
    m = replace(peanut_allergic, allergens=("Peanut",))
    assert allergen_reasons(namkeen, m, cfg)[0].params == {"allergen": "peanut"}


def test_may_contain_statement_without_ingredients(no_ingredients, cfg, peanut_allergic):
    p = replace(no_ingredients, may_contain_statement="may contain peanuts")
    assert [r.code for r in allergen_reasons(p, peanut_allergic, cfg)] == ["allergen_may_contain"]
