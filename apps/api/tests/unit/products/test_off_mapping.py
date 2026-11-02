import json
from pathlib import Path

import pytest

from app.features.products.off_mapping import (
    ProductInfo,
    off_to_info,
    off_to_product,
    split_ingredients,
)
from app.scoring import AllergenState, Category, Member, Status, analyze

FIXTURES = Path(__file__).resolve().parents[2] / "fixtures" / "off"


def load(name: str) -> dict:
    return json.loads((FIXTURES / f"map_{name}.json").read_text(encoding="utf-8"))


def prod(name: str, confidence: float = 0.9):
    return off_to_product(load(name), confidence=confidence)


def test_maps_biscuit():
    p = prod("biscuit")
    assert p.per_100g.sugars_g == 2.0 and p.per_100g.energy_kcal == 450 and p.serving_size_g == 25
    assert "maltodextrin" in p.ingredients and p.claims == ("sugar free",)
    assert p.extraction_confidence == 0.9
    assert p.per_100g.salt_g == 0.9 and p.per_100g.sodium_mg == pytest.approx(360)
    assert p.name == "Sugar Free Biscuit" and p.category == Category.GENERAL
    # ingredients_text_en preferred over ingredients_text; parenthesised INS list kept whole
    assert "raising agent (ins 500(ii))" in p.ingredients
    assert "ignored non-en text" not in p.ingredients


def test_confidence_is_passed_through_not_hardcoded():
    assert prod("biscuit", 0.5).extraction_confidence == 0.5


def test_veg_mark_never_guessed_from_labels():
    # The biscuit payload carries en:vegetarian; OFF labels are not an FSSAI dot.
    assert prod("biscuit").veg_mark is None


def test_per_serving_only_stays_none():
    n = prod("per_serving_only").per_100g
    assert n.sugars_g is None and n.energy_kcal is None
    assert n.protein_g is None and n.salt_g is None and n.sodium_mg is None


def test_per_serving_only_gives_unknown_for_allergic_member():
    member = Member(id="m", name="m", age=30, allergens=("milk",))
    v = analyze(prod("per_serving_only"), [member]).verdicts[0]
    assert v.status == Status.UNKNOWN
    assert [(r.code, r.severity, dict(r.params)) for r in v.reasons] == [
        ("allergen_unknown", Status.UNKNOWN, {"allergen": "milk"})
    ]


def test_energy_from_kj():
    assert prod("kj_only").per_100g.energy_kcal == pytest.approx(1882.8 / 4.184)


def test_energy_from_energy_100g_is_kj():
    assert prod("energy_100g_only").per_100g.energy_kcal == pytest.approx(450.0)


def test_kcal_preferred_over_kj_when_both_present():
    assert prod("kcal_and_kj").per_100g.energy_kcal == 400


def test_beverage_category_and_sodium():
    p = prod("beverage")
    assert p.category == Category.BEVERAGE and p.per_100g.sodium_mg == pytest.approx(10.0)
    assert p.serving_size_g == 300


def test_water_cheese_fat_categories():
    assert prod("water").category == Category.WATER  # waters beat beverages
    assert prod("cheese").category == Category.CHEESE
    assert prod("fat").category == Category.FAT


def test_sodium_only_converts_g_to_mg_and_does_not_invent_salt():
    n = prod("sodium_only").per_100g
    assert n.sodium_mg == pytest.approx(1200) and n.salt_g is None
    assert n.salt() == pytest.approx(3.0)  # engine derives it


def test_split_ingredients_respects_parentheses():
    assert split_ingredients(
        "wheat flour (maida), sugar, raising agent (ins 500(ii), ins 503), salt"
    ) == ("wheat flour (maida)", "sugar", "raising agent (ins 500(ii), ins 503)", "salt")


def test_split_ingredients_semicolons_empties_and_none():
    assert split_ingredients(" a; b ,, ,c ") == ("a", "b", "c")
    assert split_ingredients(None) == () and split_ingredients("") == ()
    assert split_ingredients("a, b)), c") == ("a", "b))", "c")


def test_allergen_and_trace_statements():
    p = prod("biscuit")
    assert p.allergen_statement == "Contains: gluten, milk"
    assert p.may_contain_statement == "May contain: soybeans"


def test_no_allergen_tags_gives_none():
    p = prod("kj_only")
    assert p.allergen_statement is None and p.may_contain_statement is None


def test_no_ingredients():
    assert prod("no_ingredients").ingredients == ()


def test_hindi_only_ingredients_are_used_and_matched():
    p = prod("hindi_only")
    assert p.ingredients == ("मूंगफली", "गेहूं का आटा", "नमक")
    result = analyze(p, [Member(id="m", name="m", allergens=("peanut",))])
    assert result.verdicts[0].status == Status.AVOID


def test_string_and_garbage_numbers():
    p = prod("string_numbers")
    n = p.per_100g
    assert n.energy_kcal == 250 and n.protein_g == 12.5
    assert n.sugars_g is None and n.fat_g is None and n.fiber_g is None
    assert n.salt_g is None and n.carbs_g is None and n.sat_fat_g is None  # NaN, inf, bool
    assert p.serving_size_g == 30.5


def test_absurd_values_pass_through_to_engine_sanitiser():
    n = prod("absurd").per_100g
    assert n.sugars_g == -5 and n.fat_g == 250 and n.energy_kcal == 5000
    assert n.sodium_mg == pytest.approx(900000)
    _, dropped = prod("absurd").sanitized()
    assert set(dropped) >= {"sugars_g", "fat_g", "energy_kcal", "sodium_mg"}


def test_claims_only_exact_known_tags():
    payload = {
        "labels_tags": [
            "en:low-fat",
            "en:high-protein",
            "en:low-salt",
            "en:no-added-sugar",
            "en:sugar-free",
            "en:low-sugar",
            "en:source-of-protein",
            "en:diabetic-friendly",
            "en:low-sodium",
            "en:no-added-sugars",
            "en:low-fat",
        ]
    }
    assert off_to_product(payload, confidence=0.9).claims == (
        "low fat",
        "high protein",
        "low salt",
        "no added sugar",
        "sugar free",
        "low sugar",
        "source of protein",
    )


@pytest.mark.parametrize(
    ("tag", "allergen"),
    [
        ("en:nuts", "tree_nut"),
        ("en:peanuts", "peanut"),
        ("en:milk", "milk"),
        ("en:gluten", "gluten"),
        ("en:soybeans", "soy"),
        ("en:sesame-seeds", "sesame"),
        ("en:eggs", "egg"),
        ("en:fish", "fish"),
        ("en:crustaceans", "crustacean"),
        ("en:mustard", "mustard"),
        ("en:sulphur-dioxide-and-sulphites", "sulphite"),
    ],
)
def test_every_allergen_tag_is_recognised_by_the_engine_as_contains(tag, allergen):
    p = off_to_product({"allergens_tags": [tag]}, confidence=0.9)
    report = analyze(p, []).report
    assert report.allergens.get(allergen) == AllergenState.CONTAINS


@pytest.mark.parametrize(
    ("tag", "allergen"),
    [("en:nuts", "tree_nut"), ("en:peanuts", "peanut"), ("en:soybeans", "soy")],
)
def test_traces_are_may_contain(tag, allergen):
    p = off_to_product({"traces_tags": [tag]}, confidence=0.9)
    assert analyze(p, []).report.allergens.get(allergen) == AllergenState.MAY_CONTAIN


def test_nuts_is_tree_nut_and_not_peanut_and_peanuts_is_peanut_only():
    nuts = analyze(off_to_product({"allergens_tags": ["en:nuts"]}, confidence=0.9), []).report
    assert nuts.allergens.get("tree_nut") == AllergenState.CONTAINS
    assert nuts.allergens.get("peanut") != AllergenState.CONTAINS
    pn = analyze(off_to_product({"allergens_tags": ["en:peanuts"]}, confidence=0.9), []).report
    assert pn.allergens.get("peanut") == AllergenState.CONTAINS
    assert "tree_nut" not in pn.allergens


def test_allergen_zoo_statement_dedupes_and_passes_unknown_tags_through():
    p = prod("allergen_tags")
    assert p.may_contain_statement == "May contain: tree nuts, nuts, peanuts, milk, celery"
    assert p.allergen_statement == (
        "Contains: tree nuts, nuts, peanuts, soybeans, sesame seeds, eggs, fish, crustaceans, "
        "mustard, sulphur dioxide, sulphites, milk, gluten"
    )


def test_milk_allergic_member_avoids_biscuit():
    result = analyze(prod("biscuit"), [Member(id="m", name="m", allergens=("milk",))])
    assert result.verdicts[0].status == Status.AVOID


def test_low_confidence_allergic_member_is_not_ok():
    p = prod("biscuit", 0.5)
    v = analyze(p, [Member(id="m", name="m", age=30, allergens=("peanut",))]).verdicts[0]
    assert v.status == Status.UNKNOWN
    assert [(r.code, r.severity, dict(r.params)) for r in v.reasons] == [
        ("allergen_unknown", Status.UNKNOWN, {"allergen": "peanut"})
    ]


def test_off_to_info():
    assert off_to_info(load("biscuit")) == ProductInfo(
        barcode="8901000000011",
        name="Sugar Free Biscuit",
        brand="Acme Foods",
        image_url="https://images.example/front.jpg",
    )


def test_off_to_info_missing_fields_and_bare_product():
    info = off_to_info({"code": "123", "product_name": "  ", "image_url": "https://x/y.jpg"})
    assert info == ProductInfo("123", None, None, "https://x/y.jpg")
    assert off_to_product({}, confidence=0.9).name == ""
