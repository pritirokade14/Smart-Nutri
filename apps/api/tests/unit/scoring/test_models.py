import math
from dataclasses import replace

import pytest

from app.scoring.models import MAX_SERVING_SIZE_G, Member, Nutrients, Product, Status


def test_salt_derived_from_sodium():
    assert Nutrients(sodium_mg=400).salt() == pytest.approx(1.0)


def test_salt_takes_higher_of_salt_and_sodium():  # Ruling R22
    assert Nutrients(salt_g=0.1, sodium_mg=900).salt() == pytest.approx(2.25)
    assert Nutrients(salt_g=1.5, sodium_mg=400).salt() == 1.5
    assert Nutrients(salt_g=0.5).salt() == 0.5


def test_energy_kj():
    assert Nutrients(energy_kcal=100).energy_kj() == pytest.approx(418.4)


def test_status_rank_order():
    assert [s.rank for s in (Status.OK, Status.CAUTION, Status.UNKNOWN, Status.AVOID)] == [
        0,
        1,
        2,
        3,
    ]


def test_per_serving(sf_biscuit):
    assert sf_biscuit.per_serving(2.0) == pytest.approx(0.5)
    assert replace(sf_biscuit, serving_size_g=None).per_serving(2.0) is None


def test_sanitized_drops_implausible_values():
    clean, dropped = Nutrients(sugars_g=250, energy_kcal=4000, protein_g=10).sanitized()
    assert clean.sugars_g is None and clean.energy_kcal is None and clean.protein_g == 10
    assert set(dropped) == {"sugars_g", "energy_kcal"}


def test_is_drink(cola, water, curd):
    assert cola.is_drink and water.is_drink and not curd.is_drink


@pytest.mark.parametrize("serving", [0, -10, math.nan, math.inf, -math.inf, MAX_SERVING_SIZE_G + 1])
def test_bad_serving_size_dropped(serving):
    clean, dropped = Product(name="x", serving_size_g=serving).sanitized()
    assert clean.serving_size_g is None and dropped == ("serving_size_g",)


@pytest.mark.parametrize("serving", [0.5, 30, MAX_SERVING_SIZE_G])
def test_plausible_serving_size_kept(serving):
    clean, dropped = Product(name="x", serving_size_g=serving).sanitized()
    assert clean.serving_size_g == serving and dropped == ()


def test_product_sanitized_also_drops_nutrients():
    p = Product(name="x", serving_size_g=0, per_100g=Nutrients(sugars_g=250, salt_g=1))
    clean, dropped = p.sanitized()
    assert dropped == ("sugars_g", "serving_size_g") and clean.per_100g.salt_g == 1


def test_sugars_above_carbs_drops_both():  # Ruling R23
    clean, dropped = Nutrients(carbs_g=10, sugars_g=40, fat_g=1).sanitized()
    assert clean.carbs_g is None and clean.sugars_g is None and clean.fat_g == 1
    assert dropped == ("carbs_g", "sugars_g")
    _, dropped = Nutrients(carbs_g=10, sugars_g=10.5).sanitized()  # tolerance 0.5
    assert dropped == ()


def test_sat_fat_above_fat_drops_both():
    clean, dropped = Nutrients(fat_g=2, sat_fat_g=5).sanitized()
    assert clean.fat_g is None and clean.sat_fat_g is None
    assert dropped == ("fat_g", "sat_fat_g")
    assert Nutrients(fat_g=2, sat_fat_g=2.5).sanitized()[1] == ()


def test_macros_over_105_drop_all_three():
    clean, dropped = Nutrients(protein_g=30, carbs_g=50, fat_g=30, sugars_g=5, salt_g=1).sanitized()
    assert dropped == ("protein_g", "carbs_g", "fat_g")
    assert clean.sugars_g == 5 and clean.salt_g == 1
    assert Nutrients(protein_g=30, carbs_g=45, fat_g=30).sanitized()[1] == ()


@pytest.mark.parametrize(
    "build",
    [
        lambda: Product(name="x", ingredients="sugar, milk"),
        lambda: Product(name="x", claims="sugar free"),
        lambda: Member(id="m", name="m", allergens="peanut"),
        lambda: Member(id="m", name="m", conditions="diabetes"),
    ],
)
def test_bare_str_for_tuple_field_rejected(build):
    with pytest.raises(TypeError):
        build()


def test_tuple_fields_still_accept_tuples():
    assert Product(name="x", ingredients=("milk",)).ingredients == ("milk",)
    assert Member(id="m", name="m", conditions=("diabetes",)).conditions == ("diabetes",)


def test_status_worst_uses_rank_not_alphabet():
    assert Status.worst([Status.CAUTION, Status.UNKNOWN]) == Status.UNKNOWN
    assert Status.worst([Status.OK, Status.AVOID, Status.UNKNOWN]) == Status.AVOID
    assert Status.worst([]) == Status.OK
    assert max([Status.CAUTION, Status.UNKNOWN]) == Status.UNKNOWN  # alphabetical, by accident
    assert max([Status.AVOID, Status.OK]) == Status.OK  # alphabetical: wrong, hence worst()
