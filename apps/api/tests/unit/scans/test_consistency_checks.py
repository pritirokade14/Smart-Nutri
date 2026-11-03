"""Label accuracy v2, item 1: arithmetic consistency checks that WITHHOLD, not just warn.

A failed check keeps its warning and also puts the fields involved in `engine_withheld`, so
the engine never sees them and the confirm screen asks for a tick (`confirm_rules`).

Tolerances (data-quality constants in `normalize.py`, not health thresholds):
- Atwater: kcal within max(15% of kcal, 20 kcal) of 4p + 4c + 9f, widened by 2 kcal/g of
  fibre either way (carbs may or may not include fibre; fibre counts 2 kcal/g).
- salt within 20% of sodium x 2.5 / 1000.
- sat + trans fat <= fat + 0.5 g (the engine's cross-field tolerance).
- decimal-shift probe: x10 or /10 on one field makes the check pass.
"""

import pytest

from app.features.products.confirm_rules import CHECK_FIELDS, checked_fields, withheld_fields
from app.features.scans.normalize import (
    ENERGY_MISMATCH_MIN_KCAL,
    ENERGY_MISMATCH_RATIO,
    FIBRE_KCAL_PER_G,
    SALT_MISMATCH_RATIO,
    WARNING_CODES,
    to_draft,
)
from app.features.scans.schemas import NutrientsIn, NutritionExtraction

# 4*3 + 4*20 + 9*5 = 137 kcal (label says 140): consistent.
GOOD = {
    "energy_kcal": 140.0,
    "protein_g": 3.0,
    "carbs_g": 20.0,
    "sugars_g": 10.0,
    "fat_g": 5.0,
    "sat_fat_g": 2.0,
    "fiber_g": 1.0,
    "salt_g": 0.5,
    "sodium_mg": 200.0,
    "sodium_unit": "mg",
}


def n(**kw) -> NutrientsIn:
    return NutrientsIn(**(dict.fromkeys(NutrientsIn.model_fields) | GOOD | kw))


def ex(**kw) -> NutritionExtraction:
    data = {
        "product_name": "Test",
        "brand": None,
        "basis_detected": "per_100g",
        "per_100g": n(),
        "per_serving": None,
        "per_100_unit": "g",
        "serving_size_g": None,
        "serving_size_unit": None,
        "ingredients": ["wheat"],
        "allergen_statement": None,
        "may_contain_statement": None,
        "claims": [],
        "veg_mark": None,
        "category_guess": "general",
        "confidence": 0.9,
        "unreadable_fields": [],
        "upper_bound_fields": [],
    }
    return NutritionExtraction(**(data | kw))


ENERGY_FIELDS = ["energy_kcal", "protein_g", "carbs_g", "fat_g", "fiber_g"]


def test_tolerances_are_the_documented_constants():
    assert ENERGY_MISMATCH_RATIO == 0.15
    assert ENERGY_MISMATCH_MIN_KCAL == 20.0
    assert SALT_MISMATCH_RATIO == 0.2
    assert FIBRE_KCAL_PER_G == 2.0


def test_consistent_label_withholds_nothing():
    d = to_draft(ex())
    assert d.warnings == [] and d.engine_withheld == []


# --- (a) Atwater with fibre -------------------------------------------------------------


def test_energy_mismatch_withholds_every_field_involved():
    d = to_draft(ex(per_100g=n(energy_kcal=300.0)))
    assert "energy_mismatch" in d.warnings
    assert d.engine_withheld == ENERGY_FIELDS


def test_energy_mismatch_withholds_only_printed_fields():
    d = to_draft(ex(per_100g=n(energy_kcal=300.0, fiber_g=None)))
    assert d.engine_withheld == ["energy_kcal", "protein_g", "carbs_g", "fat_g"]


@pytest.mark.parametrize(
    "kcal",
    [
        # High-fibre label (fibre 20 g): 4*10 + 4*60 + 9*2 = 298.
        # Carbs include fibre, fibre at 2 kcal/g: 298 - 2*20 = 258.
        230.0,  # 258 - 15% of 230 (34.5) = 223.5 -> inside; old rule: 298 - 34.5 -> mismatch
        # Carbs exclude fibre: 298 + 2*20 = 338.
        380.0,  # 338 + 15% of 380 (57) = 395 -> inside; old rule: 298 + 57 = 355 -> mismatch
    ],
)
def test_atwater_allows_for_fibre_either_way(kcal):
    col = n(energy_kcal=kcal, protein_g=10.0, carbs_g=60.0, fat_g=2.0, sat_fat_g=0.5,
            sugars_g=5.0, fiber_g=20.0)  # fmt: skip
    d = to_draft(ex(per_100g=col))
    assert "energy_mismatch" not in d.warnings and d.engine_withheld == []


def test_atwater_fibre_window_has_limits():
    col = n(energy_kcal=150.0, protein_g=10.0, carbs_g=60.0, fat_g=2.0, sat_fat_g=0.5,
            sugars_g=5.0, fiber_g=20.0)  # fmt: skip
    assert "energy_mismatch" in to_draft(ex(per_100g=col)).warnings


# --- (b) decimal-shift probe ------------------------------------------------------------


def test_decimal_shift_names_the_one_field_that_fixes_atwater():
    # Fat printed 5.0, read as 50: 4*3 + 4*20 + 9*50 = 542 vs 140.
    d = to_draft(ex(per_100g=n(fat_g=50.0)))
    assert "energy_mismatch" in d.warnings
    assert "decimal_shift:per_100g.fat_g" in d.warnings
    assert d.engine_withheld == ENERGY_FIELDS


def test_decimal_shift_on_energy_itself():
    d = to_draft(ex(per_100g=n(energy_kcal=14.0)))
    assert "decimal_shift:per_100g.energy_kcal" in d.warnings


def test_no_decimal_shift_when_no_single_field_explains_it():
    d = to_draft(ex(per_100g=n(energy_kcal=400.0)))
    assert "energy_mismatch" in d.warnings
    assert not [w for w in d.warnings if w.startswith("decimal_shift:")]


def test_decimal_shift_names_the_printed_serving_column_when_derived():
    col = n(energy_kcal=42.0, protein_g=0.9, carbs_g=6.0, sugars_g=3.0, fat_g=15.0,
            sat_fat_g=0.6, fiber_g=0.3, salt_g=0.15, sodium_mg=60.0)  # fmt: skip
    d = to_draft(
        ex(basis_detected="per_serving", per_100g=None, per_serving=col, serving_size_g=30)
    )
    assert d.derived_from_serving
    assert "decimal_shift:per_serving.fat_g" in d.warnings


def test_salt_sodium_decimal_shift_names_both_fields():
    # Salt 0.5 read as 5.0: x10 on salt or /10 on sodium both fix it, so both are named.
    d = to_draft(ex(per_100g=n(salt_g=5.0)))
    assert "salt_sodium_mismatch" in d.warnings
    assert "decimal_shift:per_100g.salt_g" in d.warnings
    assert "decimal_shift:per_100g.sodium_mg" in d.warnings
    assert d.engine_withheld == ["salt_g", "sodium_mg"]


def test_salt_sodium_mismatch_withholds_both():
    d = to_draft(ex(per_100g=n(salt_g=1.5)))
    assert "salt_sodium_mismatch" in d.warnings
    assert not [w for w in d.warnings if w.startswith("decimal_shift:")]
    assert d.engine_withheld == ["salt_g", "sodium_mg"]


def test_unitless_sodium_that_fits_salt_in_g_is_not_a_mismatch():
    # "Sodium 0.2" with no unit and salt 0.5: 0.2 g = 200 mg agrees with the salt.
    d = to_draft(ex(per_100g=n(sodium_mg=0.2, sodium_unit=None)))
    assert "salt_sodium_mismatch" not in d.warnings
    assert d.engine_withheld == ["sodium_mg"]  # the unit is still unconfirmed


def test_unitless_sodium_that_fits_neither_unit_is_a_mismatch():
    d = to_draft(ex(per_100g=n(sodium_mg=7.0, sodium_unit=None)))
    assert "salt_sodium_mismatch" in d.warnings
    assert d.engine_withheld == ["salt_g", "sodium_mg"]


def test_kcal_kj_mismatch_withholds_energy():
    d = to_draft(ex(per_100g=n(energy_kj=1000.0)))  # 239 kcal vs 140 printed
    assert "kcal_kj_mismatch" in d.warnings
    assert d.engine_withheld == ["energy_kcal"]


# --- (c) sum of parts -------------------------------------------------------------------


def test_sat_plus_trans_above_total_fat_withholds_fat_fields():
    d = to_draft(ex(per_100g=n(fat_g=5.0, sat_fat_g=4.0, trans_fat_g=1.6)))
    assert "fat_parts_mismatch" in d.warnings
    assert {"fat_g", "sat_fat_g"} <= set(d.engine_withheld)


def test_sat_plus_trans_within_rounding_is_fine():
    d = to_draft(ex(per_100g=n(fat_g=5.0, sat_fat_g=4.0, trans_fat_g=1.4)))
    assert "fat_parts_mismatch" not in d.warnings and d.engine_withheld == []


def test_sugars_above_carbs_stays_an_implausible_value():
    """Already enforced by the engine (save rejects it), not a new withheld check."""
    d = to_draft(ex(per_100g=n(sugars_g=30.0)))
    assert "implausible_value:sugars_g" in d.warnings


# --- (d) the confirm screen asks for every withheld field ------------------------------


def test_check_fields_map_every_withholding_code():
    assert set(CHECK_FIELDS) == {
        "energy_mismatch",
        "kcal_kj_mismatch",
        "salt_sodium_mismatch",
        "fat_parts_mismatch",
    }
    assert checked_fields(["decimal_shift:per_100g.fat_g"]) == {"fat_g"}


@pytest.mark.parametrize(
    "col",
    [
        n(energy_kcal=300.0),
        n(salt_g=1.5),
        n(energy_kj=1000.0),
        n(fat_g=5.0, sat_fat_g=4.0, trans_fat_g=1.6),
    ],
)
def test_confirm_hints_cover_check_withheld_fields(col):
    d = to_draft(ex(per_100g=col))
    assert set(d.engine_withheld) <= withheld_fields(d)
    asked = set(d.confirm.columns.per_100g.confirm_fields)
    assert set(d.engine_withheld) <= asked


def test_basis_mismatch_still_asks_for_check_fields():
    """On a basis mismatch the explicit basis answers the basis doubt, not the arithmetic."""
    d = to_draft(ex(basis_detected="unknown", per_100g=n(energy_kcal=300.0)))
    assert "basis_mismatch" in d.warnings and "energy_mismatch" in d.warnings
    for column in (d.confirm.columns.per_100g, d.confirm.columns.per_serving):
        assert set(ENERGY_FIELDS) <= set(column.confirm_fields)


def test_every_warning_code_is_listed():
    assert {
        "energy_mismatch",
        "kcal_kj_mismatch",
        "salt_sodium_mismatch",
        "fat_parts_mismatch",
        "decimal_shift",
    } <= set(WARNING_CODES)
