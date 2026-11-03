"""Label accuracy v2, item 2: the per-100 g and per-serving columns must agree.

When both columns and a plausible serving size are printed, each engine field must satisfy
per_serving ~= per_100g x serving / 100 within
max(COLUMN_RATIO_TOLERANCE x the larger value, the field's rounding unit). A field that fails
gets `column_mismatch:<field>` and is withheld (either column may be the wrong one).
"""

import pytest

from app.features.scans.normalize import (
    COLUMN_RATIO_TOLERANCE,
    COLUMN_ROUNDING_UNITS,
    WARNING_CODES,
    to_draft,
)
from app.features.scans.schemas import NutrientsIn, NutritionExtraction

P100 = {
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
# The same food per 30 g serving.
PS = {k: (v * 0.3 if isinstance(v, float) else v) for k, v in P100.items()}


def n(base: dict, **kw) -> NutrientsIn:
    return NutrientsIn(**(dict.fromkeys(NutrientsIn.model_fields) | base | kw))


def ex(**kw) -> NutritionExtraction:
    data = {
        "product_name": "Test",
        "brand": None,
        "basis_detected": "both",
        "per_100g": n(P100),
        "per_serving": n(PS),
        "per_100_unit": "g",
        "serving_size_g": 30.0,
        "serving_size_unit": "g",
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


def mismatches(d) -> list[str]:
    return [w for w in d.warnings if w.startswith("column_mismatch:")]


def test_tolerances_are_the_documented_constants():
    assert COLUMN_RATIO_TOLERANCE == 0.10
    assert COLUMN_ROUNDING_UNITS == {"energy_kcal": 5.0, "sodium_mg": 10.0, "default": 0.5}
    assert "column_mismatch" in WARNING_CODES


def test_agreeing_columns_pass():
    d = to_draft(ex())
    assert d.warnings == [] and d.engine_withheld == []


@pytest.mark.parametrize(
    ("field", "printed"),
    [
        ("energy_kcal", 47.0),  # 42 expected: within the 5 kcal rounding unit
        ("protein_g", 1.0),  # 0.9 printed as a whole number
        ("fiber_g", 0.0),  # 0.3 printed as 0 ("0 g if under 0.5 g")
        ("sodium_mg", 70.0),  # 60 expected, rounded to 10 mg
        ("carbs_g", 6.6),  # 6.0 expected: 10%
    ],
)
def test_label_rounding_is_tolerated(field, printed):
    d = to_draft(ex(per_serving=n(PS, **{field: printed})))
    assert mismatches(d) == [] and d.engine_withheld == []


def test_one_field_in_the_wrong_row_is_withheld():
    d = to_draft(ex(per_serving=n(PS, sugars_g=6.0)))  # 3.0 expected
    assert mismatches(d) == ["column_mismatch:sugars_g"]
    assert d.engine_withheld == ["sugars_g"]
    for column in (d.confirm.columns.per_100g,):
        assert "sugars_g" in column.confirm_fields


def test_misread_serving_size_fails_every_field():
    # The per-serving column is for 30 g. (A smaller misread, e.g. 50 g, fails only the fields
    # large enough to clear the 0.5 g rounding unit.)
    d = to_draft(ex(serving_size_g=200.0))
    assert len(mismatches(d)) == 9
    assert set(d.engine_withheld) == {
        "energy_kcal", "protein_g", "carbs_g", "sugars_g", "fat_g", "sat_fat_g",
        "fiber_g", "salt_g", "sodium_mg",
    }  # fmt: skip


def test_per_serving_save_also_asks_for_the_field():
    d = to_draft(ex(per_serving=n(PS, fat_g=0.5)))
    assert "column_mismatch:fat_g" in d.warnings
    assert "fat_g" in d.confirm.columns.per_serving.confirm_fields
    assert "fat_g" in d.confirm.columns.per_100g.confirm_fields


def test_fields_missing_from_either_column_are_skipped():
    d = to_draft(ex(per_serving=n(PS, fiber_g=None, sugars_g=None)))
    assert mismatches(d) == []


def test_upper_bound_cells_are_skipped():
    d = to_draft(ex(per_serving=n(PS, protein_g=0.5), upper_bound_fields=["per_serving.protein_g"]))
    assert mismatches(d) == []


def test_unitless_sodium_is_skipped():
    d = to_draft(ex(per_serving=n(PS, sodium_mg=0.06, sodium_unit=None)))
    assert mismatches(d) == []


def test_no_check_without_a_serving_size():
    d = to_draft(ex(serving_size_g=None, per_serving=n(PS, sugars_g=9.0)))
    assert mismatches(d) == []


def test_no_check_when_the_per_100g_column_is_derived():
    d = to_draft(ex(basis_detected="per_serving", per_100g=None))
    assert d.derived_from_serving and mismatches(d) == []


def test_basis_mismatch_still_asks_for_mismatched_fields():
    d = to_draft(ex(basis_detected="unknown", per_serving=n(PS, sugars_g=6.0)))
    assert "basis_mismatch" in d.warnings
    for column in (d.confirm.columns.per_100g, d.confirm.columns.per_serving):
        assert "sugars_g" in column.confirm_fields
