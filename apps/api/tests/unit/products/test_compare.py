import pytest

from app import scoring
from app.features.products.compare import compare
from app.scoring.nutriscore import compute_nutriscore
from tests.fixtures.loader import load_product


@pytest.fixture
def namkeen():
    return load_product("namkeen")


@pytest.fixture
def oats():
    return load_product("oats")


def _side(p):
    return (p, compute_nutriscore(p))


def test_compare_pure(namkeen, oats):
    b = compare(_side(namkeen), _side(oats))
    assert (b["sugars_g"], b["protein_g"], b["grade"], b["salt_g"]) == ("b", "a", "b", "b")


def test_compare_all_keys_and_direction(namkeen, oats):
    b = compare(_side(oats), _side(namkeen))
    assert b == {
        "energy_kcal": "a",  # 389 < 550
        "sugars_g": "a",
        "salt_g": "a",
        "sat_fat_g": "a",
        "protein_g": "b",  # 15 > 13
        "fiber_g": "a",  # 10.6 > 5
        "grade": "a",
    }


def test_same_and_unknown(oats):
    blank = scoring.Product(name="Blank", per_100g=scoring.Nutrients(energy_kcal=389))
    b = compare(_side(oats), _side(blank))
    assert b["energy_kcal"] == "same"
    assert {b[k] for k in ("sugars_g", "salt_g", "sat_fat_g", "protein_g", "fiber_g")} == {
        "unknown"
    }
    assert b["grade"] == "unknown"  # blank has no grade


def test_implausible_values_are_unknown(oats):
    absurd = scoring.Product(name="X", per_100g=scoring.Nutrients(sugars_g=250, salt_g=0.0))
    b = compare(_side(oats), _side(absurd))
    assert b["sugars_g"] == "unknown"  # 250 g/100 g is dropped by the engine's sanitiser
    assert b["salt_g"] == "b"


def test_salt_uses_sodium_when_salt_missing():
    a = scoring.Product(name="A", per_100g=scoring.Nutrients(sodium_mg=400))  # 1.0 g salt
    b = scoring.Product(name="B", per_100g=scoring.Nutrients(salt_g=0.5))
    assert compare(_side(a), _side(b))["salt_g"] == "b"
