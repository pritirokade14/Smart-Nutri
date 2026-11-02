"""Fix round 2 (ruling R16): OFF serving_size formats, foreign-language guard, powder tags."""

import pytest

from app.features.products.off_mapping import off_to_product
from app.scoring import Category, Member, Status, analyze

DB = Member(id="d", name="x", age=50, conditions=("diabetes",))
KID = Member(id="k", name="x", age=8)
MILK = Member(id="m", name="x", age=30, allergens=("milk",))

DRINK = {
    "ingredients_text_en": "water, maltodextrin, salt",
    "categories_tags": ["en:beverages"],
    "nutriments": {
        "energy-kcal_100g": 30,
        "sugars_100g": 2,
        "carbohydrates_100g": 7,
        "fat_100g": 0,
        "saturated-fat_100g": 0,
        "salt_100g": 0.05,
        "proteins_100g": 0,
        "fiber_100g": 0,
    },
}
JUICE = {
    "ingredients_text_en": "water, sugar, mango pulp",
    "categories_tags": ["en:beverages", "en:juices-and-nectars"],
    "nutriments": {
        "energy-kcal_100g": 45,
        "sugars_100g": 11,
        "carbohydrates_100g": 11,
        "fat_100g": 0,
        "saturated-fat_100g": 0,
        "salt_100g": 0.02,
        "proteins_100g": 0,
        "fiber_100g": 0,
    },
}


def reasons(payload: dict, member: Member):
    p = off_to_product(payload, confidence=0.9)
    v = analyze(p, [member]).verdicts[0]
    return v.status, [(r.code, r.severity, dict(r.params)) for r in v.reasons]


def size(s: str) -> float | None:
    return off_to_product({"serving_size": s}, confidence=0.9).serving_size_g


def test_bottle_serving_size_gives_per_serving_child_caution():
    payload = {**DRINK, "serving_size": "1 bottle (500 ml)"}
    assert off_to_product(payload, confidence=0.9).serving_size_g == 500
    status, found = reasons(payload, KID)
    assert status == Status.CAUTION
    assert found == [
        (
            "child_sugar_moderate",
            Status.CAUTION,
            {"pct": 41.67, "limit_g": 24.0, "basis": "per_serving"},
        )
    ]


def test_bottle_serving_size_gives_diabetic_carbs_per_serving_high():
    status, found = reasons({**DRINK, "serving_size": "1 bottle (500 ml)"}, DB)
    assert status == Status.CAUTION
    assert (
        "carbs_per_serving_high",
        Status.CAUTION,
        {"carbs_g": 35.0, "basis": "per_serving"},
    ) in found


def test_pack_serving_size_gives_child_avoid_for_mango_juice():
    status, found = reasons({**JUICE, "serving_size": "1 pack (200 ml)"}, KID)
    assert status == Status.AVOID
    assert found == [
        (
            "child_sugar_high",
            Status.AVOID,
            {"pct": 91.67, "limit_g": 24.0, "basis": "per_serving"},
        )
    ]


@pytest.mark.parametrize(
    ("text", "expected"),
    [
        ("30 g", 30),
        ("30g", 30),
        ("30 G", 30),
        ("30 gm", 30),
        ("30 gms", 30),
        ("30 grams", 30),
        ("30 Grams", 30),
        ("30.5 g", 30.5),
        ("250ml", 250),
        ("250 ML", 250),
        ("1 pack (30 g)", 30),
        ("30 g (2 biscuits)", 30),
        ("1 bottle (300 ml)", 300),
        ("30 g (30 g)", 30),
    ],
)
def test_serving_size_accepts_exactly_one_explicit_amount(text, expected):
    assert size(text) == expected


@pytest.mark.parametrize(
    "text",
    [
        "2 x 15 g",
        "2x15g",
        "1 l",
        "1 bottle (1 l)",
        "1.5 litre",
        "30,5 g",
        "30 g (45 ml)",
        "30 g or 40 g",
        "1 biscuit",
        "1 oz",
        "",
        "g",
    ],
)
def test_serving_size_rejects_ambiguous_amounts(text):
    assert size(text) is None


def test_unit_quantity_still_wins_and_bad_quantity_falls_back_to_size():
    p = {"serving_quantity": 500, "serving_quantity_unit": "ml", "serving_size": "1 bottle"}
    assert off_to_product(p, confidence=0.9).serving_size_g == 500
    p = {"serving_quantity": "x", "serving_quantity_unit": "g", "serving_size": "25 g"}
    assert off_to_product(p, confidence=0.9).serving_size_g == 25


@pytest.mark.parametrize(
    "payload",
    [
        {
            "lang": "en",
            "ingredients_text": "sucre, lait entier en poudre, beurre de cacao, noisettes",
        },
        {"ingredients_lc": "en", "ingredients_text": "sucre, lait entier en poudre, noisettes"},
        {"ingredients_text_en": "zucker, vollmilchpulver, milch, eier"},
        {"ingredients_text_en": "harina de trigo, azúcar, leche, aceite, huevos"},
    ],
)
def test_foreign_words_make_ingredient_text_unreadable_even_when_labelled_english(payload):
    assert off_to_product(payload, confidence=0.9).ingredients == ()
    status, found = reasons(payload, MILK)
    assert status == Status.UNKNOWN
    assert ("allergen_unknown", Status.UNKNOWN, {"allergen": "milk"}) in found


def test_english_text_with_shared_words_is_still_read():
    p = off_to_product(
        {"ingredients_lc": "en", "ingredients_text": "sugar, butter, salt, cocoa, milk"},
        confidence=0.9,
    )
    assert p.ingredients == ("sugar", "butter", "salt", "cocoa", "milk")


def test_foreign_text_is_dropped_but_other_readable_text_is_kept():
    p = off_to_product(
        {"ingredients_text_en": "sugar, milk", "ingredients_text_mr": "sucre, lait"}, confidence=0.9
    )
    assert p.ingredients == ("sugar", "milk")


@pytest.mark.parametrize(
    "tags",
    [
        ["en:beverages", "en:dried-products-to-be-rehydrated", "en:dehydrated-beverages"],
        ["en:beverages", "en:cocoa-and-chocolate-powders"],
        ["en:beverages", "en:dehydrated-beverages"],
        ["en:beverages", "en:hot-beverages", "en:teas", "en:green-teas"],
        ["en:beverages", "en:hot-beverages", "en:teas", "en:black-teas"],
    ],
)
def test_more_powder_and_dry_tea_tags_are_general(tags):
    assert off_to_product({"categories_tags": tags}, confidence=0.9).category == Category.GENERAL


def test_green_tea_that_is_ready_to_drink_stays_a_beverage():
    tags = ["en:beverages", "en:teas", "en:green-teas", "en:iced-teas"]
    assert off_to_product({"categories_tags": tags}, confidence=0.9).category == Category.BEVERAGE
