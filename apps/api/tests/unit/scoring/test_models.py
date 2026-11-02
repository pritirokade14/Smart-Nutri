from dataclasses import replace

import pytest

from app.scoring.models import Nutrients, Status


def test_salt_derived_from_sodium():
    assert Nutrients(sodium_mg=400).salt() == pytest.approx(1.0)


def test_salt_prefers_explicit_value():
    assert Nutrients(salt_g=0.5, sodium_mg=400).salt() == 0.5


def test_energy_kj():
    assert Nutrients(energy_kcal=100).energy_kj() == pytest.approx(418.4)


def test_status_rank_order():
    assert [s.rank for s in (Status.OK, Status.CAUTION, Status.UNKNOWN, Status.AVOID)] == [0, 1, 2, 3]


def test_per_serving(sf_biscuit):
    assert sf_biscuit.per_serving(2.0) == pytest.approx(0.5)
    assert replace(sf_biscuit, serving_size_g=None).per_serving(2.0) is None


def test_sanitized_drops_implausible_values():
    clean, dropped = Nutrients(sugars_g=250, energy_kcal=4000, protein_g=10).sanitized()
    assert clean.sugars_g is None and clean.energy_kcal is None and clean.protein_g == 10
    assert set(dropped) == {"sugars_g", "energy_kcal"}


def test_is_drink(cola, water, curd):
    assert cola.is_drink and water.is_drink and not curd.is_drink
