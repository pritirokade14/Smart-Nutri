"""EF1: OFF categories -> the Nutri-Score 2023 groups (fats/oils/nuts/seeds, beverages, water).

Tag sets are the real `categories_tags` of Indian products in the E2 experiment
(.research/data/off_raw); the expected group is the official 2023 scope.
"""

import pytest

from app.features.products.off_mapping import off_to_product
from app.scoring import Category, analyze


def mapped(*tags: str):
    return off_to_product({"categories_tags": list(tags)}, confidence=0.9)


@pytest.mark.parametrize(
    "tags",
    [
        # 8901512144201 peanut butter
        (
            "en:plant-based-foods",
            "en:legumes-and-their-products",
            "en:nuts-and-their-products",
            "en:legume-butters",
            "en:nut-butters",
            "en:peanut-butters",
        ),
        # 8904296902104 peanut butter tagged only as a legume butter
        ("en:plant-based-foods", "en:legume-butters", "en:peanut-butters"),
        # 8904063240170 salted peanuts
        (
            "en:plant-based-foods",
            "en:legumes",
            "en:nuts-and-their-products",
            "en:nuts",
            "en:peanuts",
            "en:roasted-nuts",
            "en:roasted-peanuts",
        ),
        # 8903363004697 cashews
        ("en:plant-based-foods", "en:nuts-and-their-products", "en:nuts", "en:cashew-nuts"),
        ("en:plant-based-foods", "en:seeds", "en:sunflower-seeds"),
        ("en:plant-based-foods", "en:seeds", "en:pumpkin-seeds"),
        ("en:plant-based-foods", "en:seeds", "en:flax-seeds"),
        ("en:plant-based-foods", "en:seeds", "en:chia-seeds"),
        ("en:plant-based-foods", "en:spreads", "en:oilseed-purees", "en:tahini"),
        # 8906036674173 cream
        ("en:dairies", "en:creams"),
        # oils, butter, ghee were already FAT
        ("en:fats", "en:vegetable-oils", "en:mustard-oils"),
        ("en:dairies", "en:fats", "en:animal-fats", "en:butters", "en:ghee"),
    ],
)
def test_fats_oils_nuts_and_seeds_are_fat(tags):
    assert mapped(*tags).category == Category.FAT


@pytest.mark.parametrize(
    "tags",
    [
        # OFF's taxonomy puts cereal grains and pulses under en:seeds; they are not oilseeds.
        (
            "en:plant-based-foods",
            "en:cereals-and-potatoes",
            "en:seeds",
            "en:cereal-grains",
            "en:rolled-oats",
            "en:oat",
        ),  # 8902710100600 rolled oats
        (
            "en:plant-based-foods",
            "en:seeds",
            "en:cereal-grains",
            "en:rices",
            "en:basmati-rices",
        ),  # 8901537074231
        (
            "en:plant-based-foods",
            "en:legumes",
            "en:seeds",
            "en:legume-seeds",
            "en:pulses",
            "en:lentils",
        ),  # 8903023005996 masoor dal
        ("en:plant-based-foods", "en:seeds", "en:textured-soy-protein"),  # 8906032018919
        # A nut bar (chikki) is a sweet snack, not nuts (no en:nuts tag).
        (
            "en:snacks",
            "en:sweet-snacks",
            "en:nuts-and-their-products",
            "en:nut-bars",
            "en:peanut-bars",
        ),  # 8906036302199
        ("en:plant-based-foods", "en:nuts-and-their-products", "en:nuts", "en:chestnuts"),
    ],
)
def test_cereals_pulses_nut_bars_and_chestnuts_are_not_fat(tags):
    assert mapped(*tags).category == Category.GENERAL


def test_almond_drink_is_a_beverage_not_a_nut():  # 8904258701547
    p = mapped(
        "en:beverages",
        "en:plant-based-beverages",
        "en:nuts-and-their-products",
        "en:nut-based-drinks",
        "en:almond-based-drinks",
        "en:plant-based-milks",
    )
    assert p.category == Category.BEVERAGE


@pytest.mark.parametrize(
    "tags",
    [
        ("en:dairies", "en:milks-liquid-and-powder", "en:milks"),  # 8906016410029
        (
            "en:dairies",
            "en:milks-liquid-and-powder",
            "en:milks",
            "en:pasteurised-milks",
            "en:toned-milks",
        ),
    ],
)
def test_liquid_milk_is_a_nutriscore_beverage_but_stays_general(tags):
    p = mapped(*tags)
    assert p.category == Category.GENERAL and p.is_drink is False
    assert p.nutriscore_beverage is True


@pytest.mark.parametrize(
    "tags",
    [
        ("en:dairies", "en:milks-liquid-and-powder", "en:milk-powders"),
        ("en:dairies", "en:milks", "en:condensed-milks", "en:sweetened-condensed-milks"),
        ("en:dairies", "en:milks", "en:evaporated-milks"),
        ("en:beverages", "en:milks", "en:instant-beverages"),
        ("en:dairies", "en:yogurts"),
        ("en:fats", "en:creams", "en:milks"),  # cream tagged as milk: fat table wins
    ],
)
def test_powders_condensed_milk_and_other_dairy_are_not_nutriscore_beverages(tags):
    assert mapped(*tags).nutriscore_beverage is False


def test_full_cream_milk_gets_the_official_2023_beverage_grade():  # 8906016410029: OFF E 10
    payload = {
        "categories_tags": ["en:dairies", "en:milks-liquid-and-powder", "en:milks"],
        "nutriments": {
            "energy-kj_100g": 366.5,
            "sugars_100g": 5.3,
            "saturated-fat_100g": 4.1,
            "fat_100g": 6,
            "salt_100g": 0.1,
            "proteins_100g": 3.2,
        },
    }
    ns = analyze(off_to_product(payload, confidence=0.9), []).report.nutriscore
    assert (ns.grade, ns.points) == ("E", 10)


@pytest.mark.parametrize(
    "tags",
    [
        # 8901396381808 soda water (water + CO2 + stabiliser)
        (
            "en:beverages",
            "en:non-alcoholic-beverages",
            "en:waters",
            "en:carbonated-drinks",
            "en:soft-drinks",
            "en:sodas",
            "en:carbonated-waters",
        ),
        # 8901764011252 cola tagged en:waters by OFF
        (
            "en:beverages",
            "en:carbonated-drinks",
            "en:soft-drinks",
            "en:waters",
            "en:sodas",
            "en:carbonated-waters",
            "en:colas",
            "en:sweetened-beverages",
        ),
        ("en:beverages", "en:waters", "en:flavoured-waters"),
        ("en:beverages", "en:waters", "en:flavored-waters"),
    ],
)
def test_sodas_and_flavoured_waters_are_beverages_not_water(tags):
    assert mapped(*tags).category == Category.BEVERAGE


@pytest.mark.parametrize(
    "tags",
    [
        ("en:beverages", "en:waters"),  # 8901764082405 packaged drinking water
        ("en:beverages", "en:waters", "en:spring-waters", "en:mineral-waters"),
        ("en:beverages", "en:waters", "en:carbonated-waters", "en:mineral-waters"),
    ],
)
def test_plain_waters_stay_water(tags):
    assert mapped(*tags).category == Category.WATER
