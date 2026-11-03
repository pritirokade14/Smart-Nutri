from dataclasses import replace

import pytest

from app.scoring import nutriscore as ns
from app.scoring.models import Category, Nutrients, Product
from app.scoring.nutriscore import compute_nutriscore


def test_curd_is_B(curd):  # N=0+1+1+0=2, protein 3.5 -> 1 => 1
    r = compute_nutriscore(curd)
    assert (r.grade, r.points, r.partial) == ("B", 1, True)


def test_sf_biscuit_is_D(sf_biscuit):  # 5+0+6+4=15 -> protein ignored; fibre 2 -> 0
    r = compute_nutriscore(sf_biscuit)
    assert (r.grade, r.points) == ("D", 15)


def test_namkeen_is_E(namkeen):  # 6+0+9+12=27; fibre 5 -> 2 => 25
    r = compute_nutriscore(namkeen)
    assert (r.grade, r.points) == ("E", 25)


def test_oats_is_A(oats):  # 4+0+1+0=5; protein 13 -> 5, fibre 10.6 -> 5 => -5
    r = compute_nutriscore(oats)
    assert (r.grade, r.points) == ("A", -5)


def test_cola_beverage_is_E(cola):
    # Official 2023 beverage sugar table: 10.6 g exceeds 9 thresholds -> 9 (brief said 8).
    # 176 kJ -> 3 ; 3 + 9 = 12 -> E (>=10)
    r = compute_nutriscore(cola)
    assert (r.grade, r.points) == ("E", 12)


def test_water_is_A(water):
    assert compute_nutriscore(water).grade == "A"


def test_sweetened_zero_kcal_water_scored_as_beverage(water):  # Ruling R35
    # 0 kJ, 0 sugars, sweetener +4 => 4 -> beverage band C (<= 6)
    r = compute_nutriscore(replace(water, contains_sweeteners=True))
    assert (r.grade, r.points) == ("C", 4)


def test_flavoured_water_with_sugar_scored_as_beverage(water):  # C12
    # 40 kcal = 167 kJ -> 3; 10 g sugars -> 8 (beverage table) => 11 -> E
    p = replace(water, per_100g=replace(water.per_100g, energy_kcal=40, sugars_g=10))
    r = compute_nutriscore(p)
    assert (r.grade, r.points) == ("E", 11)
    assert (
        compute_nutriscore(replace(water, per_100g=replace(water.per_100g, energy_kcal=5))).grade
        != "A"
    )
    assert (
        compute_nutriscore(replace(water, per_100g=replace(water.per_100g, sugars_g=1))).grade
        != "A"
    )


def test_missing_sat_fat_is_insufficient(curd):
    r = compute_nutriscore(replace(curd, per_100g=replace(curd.per_100g, sat_fat_g=None)))
    assert (r.grade, r.reason) == (None, "insufficient_data")


def test_cheese_flagged_approximated(curd):
    assert compute_nutriscore(replace(curd, category=Category.CHEESE)).approximated is True


def test_cheese_keeps_protein_despite_high_negative_points(namkeen):
    # negative 27; fibre 5 -> 2; protein 15 exceeds 6 thresholds -> 6 (cheese exempt from rule)
    r = compute_nutriscore(replace(namkeen, category=Category.CHEESE))
    assert r.points == 27 - 2 - 6


# --- EF1: official 2023 fats, oils, nuts and seeds table -------------------------------------
# Expected points are Open Food Facts' own 2023 component points for the real Indian products
# named (E2 disagreements, .research/data/off_raw). OFF's Nutriscore.pm is the open reference
# implementation of the Santé publique France 2023 specification.
def _fat(**values: float | None) -> Product:
    return Product(name="x", category=Category.FAT, per_100g=Nutrients(**values))


def test_sunflower_oil_uses_the_fat_table():  # OFF 8901709011552, OFF 2023 C 4
    # 12 g sat -> 444 kJ from saturates -> 3; sat/fat 12 % -> 1; sugars 0; salt 0 => 4
    r = compute_nutriscore(_fat(energy_kcal=900, fat_g=100, sat_fat_g=12, sugars_g=0, salt_g=0))
    assert (r.grade, r.points, r.approximated) == ("C", 4, False)


def test_saturated_fat_ratio_threshold_is_inclusive():  # OFF 8901248270212, OFF C 6
    # 16 g sat -> 592 kJ -> 4; ratio exactly 16 % -> 2 (official ">= 16") => 6
    r = compute_nutriscore(_fat(energy_kcal=900, fat_g=100, sat_fat_g=16, sugars_g=0, salt_g=0))
    assert (r.grade, r.points) == ("C", 6)


def test_groundnut_oil_is_D():  # OFF 8906035030918, OFF D 13
    # 30 g sat -> 1110 kJ -> 9; ratio 30 % -> 4 => 13
    r = compute_nutriscore(_fat(energy_kcal=900, fat_g=100, sat_fat_g=30, sugars_g=0, salt_g=0))
    assert (r.grade, r.points) == ("D", 13)


def test_peanut_butter_counts_protein_below_7_negative_points():  # OFF 8901512144201, OFF A -6
    # 9.4 g sat -> 347.8 kJ -> 2; sugars 4.7 -> 1; ratio 17.7 % -> 2; salt 0.01 -> 0 => N 5 < 7
    # protein 28.6 -> 7; fibre 6.8 -> 4 => -6 -> A (fat band A <= -6)
    r = compute_nutriscore(
        _fat(
            energy_kcal=639,
            fat_g=53,
            sat_fat_g=9.4,
            sugars_g=4.7,
            salt_g=0.01,
            protein_g=28.6,
            fiber_g=6.8,
            fvl_percent=0,
        )
    )
    assert (r.grade, r.points, r.partial) == ("A", -6, False)


def test_salted_peanuts_drop_protein_at_7_negative_points():  # OFF 8904063240170, OFF C 4
    # 7.3 g sat -> 270.1 kJ -> 2; sugars 0.5 -> 0; ratio 14.8 % -> 1; salt 1.26 -> 6 => N 9 >= 7
    # protein not counted; fibre 7.61 -> 5 => 4 -> C
    r = compute_nutriscore(
        _fat(
            energy_kcal=622.5,
            fat_g=49.3,
            sat_fat_g=7.3,
            sugars_g=0.5,
            salt_g=1.26,
            protein_g=26.7,
            fiber_g=7.61,
        )
    )
    assert (r.grade, r.points) == ("C", 4)


@pytest.mark.parametrize(
    ("points", "grade"),
    [(-6, "A"), (-5, "B"), (2, "B"), (3, "C"), (10, "C"), (11, "D"), (18, "D"), (19, "E")],
)
def test_fat_grade_bands(points, grade):
    assert ns._grade(points, ns.GRADE_BANDS_FAT) == grade


def test_fat_with_zero_total_fat_has_zero_ratio():
    r = compute_nutriscore(_fat(energy_kcal=10, fat_g=0, sat_fat_g=0, sugars_g=0, salt_g=0))
    assert (r.grade, r.points) == ("B", 0)


def test_fat_without_total_fat_is_insufficient():
    r = compute_nutriscore(_fat(energy_kcal=900, sat_fat_g=12, sugars_g=0, salt_g=0))
    assert (r.grade, r.reason) == (None, "insufficient_data")


def test_fat_table_does_not_need_total_energy():
    # The fat table scores energy from saturates, not total energy (official 2023).
    r = compute_nutriscore(_fat(fat_g=100, sat_fat_g=12, sugars_g=0, salt_g=0))
    assert (r.grade, r.points) == ("C", 4)


# --- EF1: beverage classification (official 2023: milk is a beverage) -------------------------
def test_milk_flagged_for_nutriscore_uses_beverage_tables():  # OFF 8906016410029, OFF E 10
    # 87.6 kcal = 366.5 kJ -> 9; sugars 5.3 -> 4; sat 4.1 -> 4; salt 0.1 -> 0 => 17
    # protein 3.2 (beverage table, always counted) -> 7 => 10 -> E (beverage band)
    milk = Product(
        name="full cream milk",
        category=Category.GENERAL,
        nutriscore_beverage=True,
        per_100g=Nutrients(
            energy_kcal=87.6, sugars_g=5.3, sat_fat_g=4.1, salt_g=0.1, protein_g=3.2, fat_g=6
        ),
    )
    r = compute_nutriscore(milk)
    assert (r.grade, r.points) == ("E", 10)
    # Without the flag the same values are scored as a general food (C).
    assert compute_nutriscore(replace(milk, nutriscore_beverage=False)).grade == "C"


def test_nutriscore_beverage_flag_never_moves_fat_or_cheese(curd):
    for category in (Category.FAT, Category.CHEESE):
        flagged = replace(curd, category=category, nutriscore_beverage=True)
        plain = replace(flagged, nutriscore_beverage=False)
        assert compute_nutriscore(flagged) == compute_nutriscore(plain)
