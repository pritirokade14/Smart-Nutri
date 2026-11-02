from dataclasses import replace

from app.scoring.models import Category
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


def test_missing_sat_fat_is_insufficient(curd):
    r = compute_nutriscore(replace(curd, per_100g=replace(curd.per_100g, sat_fat_g=None)))
    assert (r.grade, r.reason) == (None, "insufficient_data")


def test_cheese_flagged_approximated(curd):
    assert compute_nutriscore(replace(curd, category=Category.CHEESE)).approximated is True


def test_cheese_keeps_protein_despite_high_negative_points(namkeen):
    # negative 27; fibre 5 -> 2; protein 15 exceeds 6 thresholds -> 6 (cheese exempt from rule)
    r = compute_nutriscore(replace(namkeen, category=Category.CHEESE))
    assert r.points == 27 - 2 - 6
