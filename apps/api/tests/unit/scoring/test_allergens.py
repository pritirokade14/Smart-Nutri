from dataclasses import replace

import pytest

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


def _codes(p, m, cfg):
    return [r.code for r in allergen_reasons(p, m, cfg)]


@pytest.mark.parametrize(
    "ings",
    [
        ("coconut", "milk solids"),
        ("almond", "milk"),
        ("roasted peanut", "butter"),
        ("sugar", "cocoa", "butter"),
    ],
)
def test_exclude_phrase_does_not_span_items(curd, cfg, milk_allergic_child, ings):
    assert _codes(replace(curd, ingredients=ings), milk_allergic_child, cfg) == ["allergen_contains"]


@pytest.mark.parametrize(
    "key,statement",
    [
        ("gluten", "Contains: Gluten"),
        ("tree_nut", "CONTAINS: TREE NUTS"),
        ("crustacean", "Contains: Crustaceans"),
        ("crustacean", "Contains: Shellfish"),
        ("sulphite", "Contains: Sulphur dioxide"),
    ],
)
def test_allergen_statement_canonical_names(oats, cfg, peanut_allergic, key, statement):
    p = replace(oats, ingredients=("starch",), allergen_statement=statement)
    m = replace(peanut_allergic, allergens=(key,))
    assert _codes(p, m, cfg) == ["allergen_contains"]


def test_may_contain_gluten_statement(oats, cfg, peanut_allergic):
    p = replace(oats, ingredients=("starch",), may_contain_statement="May contain gluten")
    m = replace(peanut_allergic, allergens=("gluten",))
    assert _codes(p, m, cfg) == ["allergen_may_contain"]


@pytest.mark.parametrize("ings", [("  ",), ("",), ("", " ")])
def test_blank_ingredients_are_unknown(curd, cfg, peanut_allergic, ings):
    assert _codes(replace(curd, ingredients=ings), peanut_allergic, cfg) == ["allergen_unknown"]


@pytest.mark.parametrize(
    "key,ings",
    [
        ("tree nut", ("cashew",)),
        ("tree-nut", ("cashew",)),
        ("Tree Nuts", ("cashew",)),
        ("dairy", ("milk solids",)),
        ("shellfish", ("prawn",)),
        ("wheat", ("maida",)),
        ("groundnut", ("peanuts",)),
    ],
)
def test_member_key_variants(curd, cfg, peanut_allergic, key, ings):
    m = replace(peanut_allergic, allergens=(key,))
    assert _codes(replace(curd, ingredients=ings), m, cfg) == ["allergen_contains"]


@pytest.mark.parametrize("key,statement", [("tree_nut", "Contains: nuts"), ("soy", "Contains: lecithin")])
def test_possible_term_in_allergen_statement_is_may_contain(oats, cfg, peanut_allergic, key, statement):
    p = replace(oats, ingredients=("starch",), allergen_statement=statement)
    m = replace(peanut_allergic, allergens=(key,))
    assert _codes(p, m, cfg) == ["allergen_may_contain"]


@pytest.mark.parametrize("ings", [("albumen", "sugar"), ("अंडे", "नमक")])
def test_egg_albumen_and_hindi_plural(curd, cfg, peanut_allergic, ings):
    m = replace(peanut_allergic, allergens=("egg",))
    assert _codes(replace(curd, ingredients=ings), m, cfg) == ["allergen_contains"]


def test_may_contain_statement_without_ingredients(no_ingredients, cfg, peanut_allergic):
    p = replace(no_ingredients, may_contain_statement="may contain peanuts")
    assert [r.code for r in allergen_reasons(p, peanut_allergic, cfg)] == ["allergen_may_contain"]
