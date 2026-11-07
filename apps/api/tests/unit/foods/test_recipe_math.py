"""recipe_math: sums with unknowns (Plan 12 Task 3; G8, G19)."""

from decimal import Decimal

from app import scoring
from app.features.foods.recipe_math import (
    NUTRIENT_KEYS,
    Amount,
    per_100_from,
    snapshot_per_100,
    sum_nutrients,
    to_nutrients,
)

D = Decimal


def per(**values) -> dict[str, Decimal | None]:
    return {k: (D(str(values[k])) if values.get(k) is not None else None) for k in NUTRIENT_KEYS}


def test_sum_known_parts_and_incomplete():
    a = Amount(D("200"), per(energy_kcal=100, fibre_g=2, sugars_g=1))
    b = Amount(D("50"), per(energy_kcal=300, fibre_g=None, sugars_g=4))
    sums = sum_nutrients([a, b])
    assert sums.totals["energy_kcal"] == D("350")  # 200 x 100 / 100 + 50 x 300 / 100
    assert sums.totals["sugars_g"] == D("4")  # 2 + 2
    assert sums.totals["fibre_g"] == D("4")  # only a's 4: the known part
    assert sums.incomplete == (
        "salt_g",
        "protein_g",
        "fat_g",
        "sat_fat_g",
        "carbs_g",
        "fibre_g",
    )
    assert "energy_kcal" not in sums.incomplete and "sugars_g" not in sums.incomplete


def test_all_unknown_is_none():
    sums = sum_nutrients([Amount(D("10"), per()), Amount(D("20"), per())])
    assert set(sums.totals.values()) == {None}  # never 0
    assert sums.incomplete == NUTRIENT_KEYS
    assert sum_nutrients([]).totals["energy_kcal"] is None


def test_strict_nulls_incomplete():
    sums = sum_nutrients(
        [
            Amount(D("100"), per(energy_kcal=100, fibre_g=2)),
            Amount(D("100"), per(energy_kcal=100, fibre_g=None)),
        ]
    )
    strict = per_100_from(sums, D("200"), strict=True)
    loose = per_100_from(sums, D("200"), strict=False)
    assert strict["energy_kcal"] == D("100")
    assert strict["fibre_g"] is None  # one ingredient does not know it
    assert loose["fibre_g"] == D("1")  # the known part, a lower bound, for the recipe view
    assert strict["protein_g"] is None and loose["protein_g"] is None  # nobody knows it


def test_snapshot_per_100_salt_from_sodium():
    n = scoring.Nutrients(energy_kcal=100.0, sodium_mg=400.0, fiber_g=3.0, sugars_g=None)
    snap = snapshot_per_100(n)
    assert snap["salt_g"] == D("1.0000")  # 400 mg x 2.5 / 1000
    assert snap["fibre_g"] == D("3.0") and snap["sugars_g"] is None
    higher = scoring.Nutrients(salt_g=2.0, sodium_mg=400.0)  # the higher value wins (R22)
    assert snapshot_per_100(higher)["salt_g"] == D("2.0")
    only_salt = scoring.Nutrients(salt_g=0.3)
    assert snapshot_per_100(only_salt)["salt_g"] == D("0.3")
    assert snapshot_per_100(scoring.Nutrients())["salt_g"] is None
    # An implausible value is dropped by the engine's sanitiser first.
    assert snapshot_per_100(scoring.Nutrients(energy_kcal=5000.0))["energy_kcal"] is None


def test_to_nutrients_round_trip():
    snap = per(
        energy_kcal=120.5, sugars_g=2.5, salt_g=0.5, protein_g=7, fat_g=3, carbs_g=15, fibre_g=4
    )
    n = to_nutrients(snap)
    assert n.salt_g == 0.5 and n.sodium_mg is None and n.fiber_g == 4.0
    assert n.sat_fat_g is None and n.fvl_percent is None
    again = snapshot_per_100(n)
    for key, value in snap.items():
        assert again[key] == (None if value is None else D(repr(float(value)))), key
