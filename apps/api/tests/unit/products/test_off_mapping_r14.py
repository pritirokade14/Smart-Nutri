"""Fix round 1 (ruling R14): readable text only, language union, nuts, drinks, serving, sweeteners."""

import pytest

from app.features.products.off_mapping import off_to_product
from app.scoring import Category, Diet, Member, Nutrients, Status, analyze


def verdict(payload: dict, member: Member, confidence: float = 0.9):
    p = off_to_product(payload, confidence=confidence)
    v = analyze(p, [member]).verdicts[0]
    return v.status, [(r.code, r.severity, dict(r.params)) for r in v.reasons]


MILK = Member(id="milk", name="m", age=30, allergens=("milk",))
PEANUT = Member(id="pn", name="m", age=30, allergens=("peanut",))
TREE_NUT = Member(id="tn", name="m", age=30, allergens=("tree nut",))
FRENCH = {
    "product_name": "Chocolat",
    "lang": "fr",
    "ingredients_lc": "fr",
    "ingredients_text": "sucre, lait entier en poudre, beurre de cacao",
    "nutriments": {},
}


def test_unreadable_language_ingredients_are_dropped():
    assert off_to_product(FRENCH, confidence=0.9).ingredients == ()
    assert off_to_product({"ingredients_text": "sugar, milk"}, confidence=0.9).ingredients == ()


@pytest.mark.parametrize(
    ("member", "code", "params"),
    [
        (MILK, "allergen_unknown", {"allergen": "milk"}),
        (Member(id="vegan", name="m", age=30, diet=Diet.VEGAN), "diet_unknown", {"diet": "vegan"}),
        (Member(id="jain", name="m", age=30, diet=Diet.JAIN), "diet_unknown", {"diet": "jain"}),
        (Member(id="infant", name="m", age=1), "ingredients_missing", {"rule": "infant"}),
    ],
)
def test_french_only_ingredients_give_unknown_not_ok(member, code, params):
    status, reasons = verdict(FRENCH, member)
    assert status == Status.UNKNOWN
    assert (code, Status.UNKNOWN, params) in reasons


def test_readable_main_language_text_is_used_when_lc_matches():
    p = off_to_product({"ingredients_text": "sugar, milk", "ingredients_lc": "en"}, confidence=0.9)
    assert p.ingredients == ("sugar", "milk")
    p = off_to_product({"ingredients_text": "दूध, चीनी", "lang": "hi"}, confidence=0.9)
    assert p.ingredients == ("दूध", "चीनी")


def test_union_of_languages_keeps_hindi_allergens_hidden_by_partial_english():
    payload = {
        "ingredients_lc": "hi",
        "ingredients_text": "मूंगफली, बेसन, नमक",
        "ingredients_text_hi": "मूंगफली, बेसन, नमक",
        "ingredients_text_en": "gram flour, salt",
        "nutriments": {},
    }
    p = off_to_product(payload, confidence=0.9)
    assert p.ingredients == ("मूंगफली", "बेसन", "नमक", "gram flour", "salt")
    status, reasons = verdict(payload, PEANUT)
    assert status == Status.AVOID
    assert ("allergen_contains", Status.AVOID, {"allergen": "peanut"}) in reasons


def test_union_dedupes_and_reads_marathi():
    p = off_to_product(
        {"ingredients_text_en": "salt, sugar", "ingredients_text_mr": "मीठ, salt"}, confidence=0.9
    )
    assert p.ingredients == ("salt", "sugar", "मीठ")


def test_nuts_tag_is_tree_nut_contains_and_peanut_may_contain():
    payload = {"ingredients_text_en": "salt", "allergens_tags": ["en:nuts"]}
    assert off_to_product(payload, confidence=0.9).allergen_statement == "Contains: tree nuts, nuts"
    status, reasons = verdict(payload, TREE_NUT)
    assert status == Status.AVOID
    assert ("allergen_contains", Status.AVOID, {"allergen": "tree_nut"}) in reasons
    status, reasons = verdict(payload, PEANUT)
    assert status == Status.AVOID
    assert ("allergen_may_contain", Status.AVOID, {"allergen": "peanut"}) in reasons
    assert all(c != "allergen_contains" for c, _, _ in reasons)


def test_nuts_in_traces_is_may_contain_for_both():
    payload = {"ingredients_text_en": "salt", "traces_tags": ["en:nuts"]}
    for member, key in ((TREE_NUT, "tree_nut"), (PEANUT, "peanut")):
        status, reasons = verdict(payload, member)
        assert status == Status.AVOID
        assert ("allergen_may_contain", Status.AVOID, {"allergen": key}) in reasons


@pytest.mark.parametrize(
    "extra",
    [
        {},
        {"serving_quantity": 1},
        {"serving_quantity": "1", "serving_quantity_unit": "oz"},
        {"serving_quantity": 1, "serving_quantity_unit": ""},
    ],
)
def test_serving_without_g_or_ml_unit_is_ignored(extra):
    base = {
        "ingredients_text_en": "sugar",
        "nutriments": {"sugars_100g": 20, "salt_100g": 0.1, "energy-kcal_100g": 400},
    }
    child = Member(id="child", name="c", age=8)
    status, reasons = verdict({**base, **extra}, child)
    assert off_to_product({**base, **extra}, confidence=0.9).serving_size_g is None
    sugar = {"pct": 83.33, "limit_g": 24.0, "basis": "per_100g"}
    assert ("child_sugar_high", Status.AVOID, sugar) in reasons
    assert status == Status.AVOID


def test_serving_size_string_with_explicit_unit():
    def mk(s):
        return off_to_product({"serving_size": s}, confidence=0.9).serving_size_g

    assert mk("30 g") == 30 and mk("250ml") == 250 and mk("1 biscuit") is None
    assert mk("2 x 15 g") is None and mk("") is None


def pt(*tags: str) -> Category:
    return off_to_product({"categories_tags": list(tags)}, confidence=0.9).category


@pytest.mark.parametrize(
    "tags",
    [
        ["en:beverages", "en:beverage-preparations", "en:instant-beverages"],
        ["en:beverages", "en:chocolate-powders"],
        ["en:beverages", "en:malted-drinks"],
        ["en:beverages", "en:hot-beverages", "en:teas", "en:tea-bags"],
        ["en:beverages", "en:coffees", "en:ground-coffees"],
        ["en:beverages", "en:instant-coffees"],
    ],
)
def test_powder_and_dry_drink_mixes_are_general(tags):
    assert pt(*tags) == Category.GENERAL


def test_plain_teas_and_coffees_tags_alone_are_not_drinks_but_ready_to_drink_are():
    assert pt("en:teas") == Category.GENERAL and pt("en:coffees") == Category.GENERAL
    assert pt("en:iced-teas") == Category.BEVERAGE
    assert pt("en:coffee-drinks") == Category.BEVERAGE


@pytest.mark.parametrize(
    "tag",
    [
        "en:dairy-drinks",
        "en:flavoured-milks",
        "en:fermented-milk-drinks",
        "en:buttermilks",
        "en:lassi",
        "en:plant-based-milks",
        "en:plant-based-beverages",
    ],
)
def test_dairy_and_plant_drinks_are_beverages(tag):
    assert pt("en:dairies", tag) == Category.BEVERAGE


def test_plain_milk_stays_general_and_waters_cheese_fat_unchanged():
    assert pt("en:dairies", "en:milks") == Category.GENERAL
    assert pt("en:beverages", "en:waters") == Category.WATER
    assert pt("en:cheeses") == Category.CHEESE and pt("en:fats") == Category.FAT


def test_sweetener_additives_set_contains_sweeteners_and_change_nutriscore():
    cola = {
        "ingredients_text_en": "carbonated water, aspartame",
        "categories_tags": ["en:beverages", "en:sodas"],
        "additives_tags": ["en:e338", "en:e951"],
        "nutriments": {
            "energy-kcal_100g": 0.4,
            "sugars_100g": 0,
            "saturated-fat_100g": 0,
            "salt_100g": 0.02,
            "fat_100g": 0,
            "proteins_100g": 0,
            "fiber_100g": 0,
            "fruits-vegetables-legumes-estimate-from-ingredients_100g": 0,
        },
    }
    with_s = off_to_product(cola, confidence=0.9)
    without = off_to_product({**cola, "additives_tags": ["en:e338"]}, confidence=0.9)
    assert with_s.contains_sweeteners is True and without.contains_sweeteners is False
    assert analyze(with_s, []).report.nutriscore != analyze(without, []).report.nutriscore


@pytest.mark.parametrize("tag", ["en:e950", "en:e955", "en:e960a", "en:e962", "en:e968"])
def test_intense_sweetener_tags(tag):
    assert off_to_product({"additives_tags": [tag]}, confidence=0.9).contains_sweeteners


@pytest.mark.parametrize("tag", ["en:e330", "en:e9500", "en:sorbitol", "en:e420"])
def test_non_sweetener_tags_are_ignored(tag):
    assert not off_to_product({"additives_tags": [tag]}, confidence=0.9).contains_sweeteners


def test_nutrition_data_per_serving_nulls_all_per_100g():
    payload = {
        "nutrition_data_per": "serving",
        "nutriments": {
            "energy-kcal_100g": 450,
            "sugars_100g": 2,
            "salt_100g": 0.9,
            "sodium_100g": 0.3,
        },
    }
    assert off_to_product(payload, confidence=0.9).per_100g == Nutrients()
    payload["nutrition_data_per"] = "100g"
    assert off_to_product(payload, confidence=0.9).per_100g.sugars_g == 2


@pytest.mark.parametrize(
    ("tag", "text"),
    [
        ("fr:lait", "milk"),
        ("de:milch", "milk"),
        ("es:leche", "milk"),
        ("fr:gluten", "gluten"),
        ("de:gluten", "gluten"),
        ("fr:arachides", "peanuts"),
        ("de:erdnüsse", "peanuts"),
        ("fr:fruits-a-coque", "tree nuts, nuts"),
        ("de:schalenfrüchte", "tree nuts, nuts"),
        ("fr:soja", "soybeans"),
        ("de:soja", "soybeans"),
        ("fr:oeufs", "eggs"),
        ("de:eier", "eggs"),
        ("fr:sesame", "sesame seeds"),
        ("de:sesam", "sesame seeds"),
        ("en:lupin", "lupin"),
        ("en:celery", "celery"),
        ("en:molluscs", "molluscs"),
        ("fr:unknown-thing", "unknown thing"),
    ],
)
def test_non_english_and_extra_allergen_tags(tag, text):
    p = off_to_product({"allergens_tags": [tag]}, confidence=0.9)
    assert p.allergen_statement == f"Contains: {text}"


def test_french_milk_tag_makes_milk_allergic_member_avoid():
    status, reasons = verdict({"ingredients_text_en": "salt", "allergens_tags": ["fr:lait"]}, MILK)
    assert status == Status.AVOID
    assert ("allergen_contains", Status.AVOID, {"allergen": "milk"}) in reasons
