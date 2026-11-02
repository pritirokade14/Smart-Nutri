"""Plan 4 Task 3: extraction -> ProductDraft (pure, health-critical)."""

import math

import pytest

from app.features.scans.normalize import ProductDraft, to_draft
from app.features.scans.schemas import NutrientsIn, NutritionExtraction


def n(**kw) -> NutrientsIn:
    return NutrientsIn(**(dict.fromkeys(NutrientsIn.model_fields) | kw))


def ex(**kw) -> NutritionExtraction:
    data = {
        "product_name": None,
        "brand": None,
        "basis_detected": "per_100g",
        "per_100g": n(),
        "per_serving": None,
        "serving_size_g": None,
        "ingredients": [],
        "allergen_statement": None,
        "may_contain_statement": None,
        "claims": [],
        "veg_mark": None,
        "category_guess": "general",
        "confidence": 0.9,
        "unreadable_fields": [],
    }
    return NutritionExtraction(**(data | kw))


# --- Plan tests ------------------------------------------------------------------------


def test_per_serving_converted_with_serving_size():
    d = to_draft(
        ex(
            basis_detected="per_serving",
            per_100g=None,
            per_serving=n(sugars_g=5.0, energy_kcal=120),
            serving_size_g=25,
        )
    )
    assert d.per_100g.sugars_g == 20.0 and d.per_100g.energy_kcal == 480 and d.derived_from_serving


def test_per_serving_without_serving_size_stays_missing():
    d = to_draft(ex(per_100g=None, per_serving=n(sugars_g=5.0), serving_size_g=None))
    assert d.per_100g.sugars_g is None and "per_100g_missing" in d.warnings


def test_implausible_value_kept_and_flagged():
    d = to_draft(ex(per_100g=n(sugars_g=250)))
    assert d.per_100g.sugars_g == 250 and "implausible_value:sugars_g" in d.warnings


def test_energy_mismatch():
    d = to_draft(ex(per_100g=n(energy_kcal=100, protein_g=10, carbs_g=60, fat_g=20)))
    assert "energy_mismatch" in d.warnings


def test_kj_only():
    assert to_draft(ex(per_100g=n(energy_kj=418.4))).per_100g.energy_kcal == pytest.approx(100)


def test_missing_values_never_filled():
    d = to_draft(ex(per_100g=n(energy_kcal=400)))
    assert d.per_100g.protein_g is None and d.per_100g.fat_g is None


def test_devanagari_ingredients_untouched():
    assert to_draft(ex(ingredients=[" मूंगफली ", "", "नमक"])).ingredients == ["मूंगफली", "नमक"]


def test_low_confidence_warning():
    assert "low_confidence" in to_draft(ex(confidence=0.5)).warnings


# --- Exact-value tests for the whole contract ------------------------------------------


def test_clean_label_has_no_warnings_and_exact_fields():
    d = to_draft(
        ex(
            product_name="  Peanut Chikki ",
            brand=" Lonavala Co ",
            per_100g=n(
                energy_kcal=500, protein_g=15, carbs_g=60, sugars_g=40, fat_g=22, salt_g=0.5
            ),
            serving_size_g=30,
            ingredients=["peanuts", "jaggery"],
            allergen_statement="Contains peanuts",
            may_contain_statement="May contain sesame",
            claims=[" No added sugar ", ""],
            veg_mark="veg",
            category_guess="general",
            confidence=0.92,
        )
    )
    assert isinstance(d, ProductDraft)
    assert d.name == "Peanut Chikki" and d.brand == "Lonavala Co"
    assert d.category == "general" and d.serving_size_g == 30
    assert d.per_100g.model_dump() == {
        "energy_kcal": 500,
        "protein_g": 15,
        "carbs_g": 60,
        "sugars_g": 40,
        "fat_g": 22,
        "sat_fat_g": None,
        "fiber_g": None,
        "salt_g": 0.5,
        "sodium_mg": None,
        "added_sugars_g": None,
        "trans_fat_g": None,
    }
    assert d.ingredients == ["peanuts", "jaggery"]
    assert d.allergen_statement == "Contains peanuts"
    assert d.may_contain_statement == "May contain sesame"
    assert d.claims == ["No added sugar"]
    assert d.veg_mark == "veg" and d.confidence == 0.92
    assert d.derived_from_serving is False and d.warnings == []


def test_blank_name_brand_and_statements_are_none():
    d = to_draft(ex(product_name="  ", brand="", allergen_statement=" ", may_contain_statement=""))
    assert d.name is None and d.brand is None
    assert d.allergen_statement is None and d.may_contain_statement is None


def test_printed_kcal_preferred_over_kj():
    d = to_draft(ex(per_100g=n(energy_kcal=120, energy_kj=2000)))
    assert d.per_100g.energy_kcal == 120


def test_kj_converted_exactly():
    d = to_draft(ex(per_100g=n(energy_kj=2092)))
    assert d.per_100g.energy_kcal == pytest.approx(500.0)


def test_salt_and_sodium_both_kept_as_printed():
    d = to_draft(ex(per_100g=n(salt_g=1.0, sodium_mg=400)))
    assert d.per_100g.salt_g == 1.0 and d.per_100g.sodium_mg == 400
    assert "salt_sodium_mismatch" not in d.warnings


def test_salt_sodium_mismatch():
    d = to_draft(ex(per_100g=n(salt_g=1.0, sodium_mg=1000)))  # 1000 mg Na = 2.5 g salt
    assert d.per_100g.salt_g == 1.0 and d.per_100g.sodium_mg == 1000
    assert "salt_sodium_mismatch" in d.warnings


def test_salt_sodium_check_needs_both():
    assert "salt_sodium_mismatch" not in to_draft(ex(per_100g=n(sodium_mg=1000))).warnings


def test_energy_consistent_has_no_mismatch():
    # 4*10 + 4*60 + 9*20 = 460
    d = to_draft(ex(per_100g=n(energy_kcal=470, protein_g=10, carbs_g=60, fat_g=20)))
    assert "energy_mismatch" not in d.warnings


def test_energy_mismatch_uses_20_kcal_floor():
    # 4*2 + 4*5 + 9*0 = 28; |40 - 28| = 12 <= max(6, 20)
    d = to_draft(ex(per_100g=n(energy_kcal=40, protein_g=2, carbs_g=5, fat_g=0)))
    assert "energy_mismatch" not in d.warnings


def test_energy_check_skipped_when_a_macro_missing():
    d = to_draft(ex(per_100g=n(energy_kcal=100, protein_g=10, carbs_g=60)))
    assert "energy_mismatch" not in d.warnings


def test_added_sugars_and_trans_fat_kept_for_display():
    d = to_draft(ex(per_100g=n(sugars_g=10, added_sugars_g=6, fat_g=5, trans_fat_g=0.1)))
    assert d.per_100g.added_sugars_g == 6 and d.per_100g.trans_fat_g == 0.1
    assert d.warnings == []


def test_added_sugars_above_total_sugars_flagged():
    d = to_draft(ex(per_100g=n(sugars_g=10, added_sugars_g=30)))
    assert d.per_100g.added_sugars_g == 30
    assert d.warnings == ["implausible_value:added_sugars_g"]


def test_trans_fat_above_total_fat_flagged():
    d = to_draft(ex(per_100g=n(fat_g=1, trans_fat_g=5)))
    assert d.warnings == ["implausible_value:trans_fat_g"]


def test_trans_fat_out_of_bounds_flagged():
    assert to_draft(ex(per_100g=n(trans_fat_g=120))).warnings == ["implausible_value:trans_fat_g"]


def test_negative_value_kept_and_flagged():
    d = to_draft(ex(per_100g=n(protein_g=-3)))
    assert d.per_100g.protein_g == -3 and d.warnings == ["implausible_value:protein_g"]


def test_cross_field_engine_drops_are_flagged():
    # The engine drops both sugars and carbs when sugars > carbs (+ tolerance).
    d = to_draft(ex(per_100g=n(sugars_g=40, carbs_g=20)))
    assert d.per_100g.sugars_g == 40 and d.per_100g.carbs_g == 20
    assert d.warnings == ["implausible_value:carbs_g", "implausible_value:sugars_g"]


def test_implausible_energy_flagged():
    d = to_draft(ex(per_100g=n(energy_kcal=4000)))
    assert d.per_100g.energy_kcal == 4000 and d.warnings == ["implausible_value:energy_kcal"]


def test_implausible_kj_flagged_as_energy_kcal():
    d = to_draft(ex(per_100g=n(energy_kj=41840)))
    assert d.per_100g.energy_kcal == pytest.approx(10000)
    assert d.warnings == ["implausible_value:energy_kcal"]


def test_non_finite_value_becomes_none_and_flagged():
    d = to_draft(ex(per_100g=n(sugars_g=math.nan, fat_g=math.inf)))
    assert d.per_100g.sugars_g is None and d.per_100g.fat_g is None
    assert d.warnings == [
        "implausible_value:sugars_g",
        "implausible_value:fat_g",
        "per_100g_missing",
    ]


def test_per_100g_preferred_when_both_printed():
    d = to_draft(
        ex(
            basis_detected="both",
            per_100g=n(sugars_g=20),
            per_serving=n(sugars_g=6, fat_g=3),
            serving_size_g=30,
        )
    )
    # No mixing: fat is only printed per serving, so per-100 g fat stays unknown.
    assert d.per_100g.sugars_g == 20 and d.per_100g.fat_g is None
    assert d.derived_from_serving is False and d.serving_size_g == 30


def test_derivation_converts_kj_and_keeps_missing_missing():
    d = to_draft(
        ex(
            basis_detected="per_serving",
            per_100g=n(),
            per_serving=n(energy_kj=209.2, sodium_mg=50, added_sugars_g=2, sugars_g=2),
            serving_size_g=20,
        )
    )
    assert d.per_100g.energy_kcal == pytest.approx(250.0)
    assert d.per_100g.sodium_mg == 250 and d.per_100g.added_sugars_g == 10
    assert d.per_100g.sugars_g == 10
    assert d.per_100g.protein_g is None and d.per_100g.fat_g is None
    assert d.derived_from_serving and d.warnings == []


def test_derivation_from_ml_serving():
    d = to_draft(
        ex(
            basis_detected="per_serving",
            per_100g=None,
            per_serving=n(sugars_g=25),
            serving_size_g=250,
            category_guess="beverage",
        )
    )
    assert d.per_100g.sugars_g == 10 and d.category == "beverage" and d.derived_from_serving


def test_derived_value_is_plausibility_checked():
    d = to_draft(ex(per_100g=None, per_serving=n(sugars_g=30), serving_size_g=10))
    assert d.per_100g.sugars_g == 300 and d.warnings == ["implausible_value:sugars_g"]


@pytest.mark.parametrize("size", [0, -5, 10_000, math.nan, math.inf])
def test_implausible_serving_size_blocks_derivation(size):
    d = to_draft(ex(per_100g=None, per_serving=n(sugars_g=5), serving_size_g=size))
    assert d.per_100g.sugars_g is None and not d.derived_from_serving
    assert d.warnings == ["implausible_value:serving_size_g", "per_100g_missing"]


def test_implausible_serving_size_kept_in_draft_when_finite():
    d = to_draft(ex(per_100g=n(sugars_g=5), serving_size_g=10_000))
    assert d.serving_size_g == 10_000 and d.warnings == ["implausible_value:serving_size_g"]


def test_non_finite_serving_size_becomes_none():
    assert to_draft(ex(serving_size_g=math.nan)).serving_size_g is None


def test_no_nutrition_table_at_all():
    d = to_draft(ex(basis_detected="unknown", per_100g=None, per_serving=None))
    assert all(v is None for v in d.per_100g.model_dump().values())
    assert d.warnings == ["per_100g_missing"] and not d.derived_from_serving


def test_per_serving_only_without_size_never_assumes_100g():
    d = to_draft(
        ex(basis_detected="per_serving", per_100g=n(), per_serving=n(energy_kcal=150, fat_g=8))
    )
    assert d.per_100g.energy_kcal is None and d.per_100g.fat_g is None
    assert d.warnings == ["per_100g_missing"]


@pytest.mark.parametrize(
    ("raw", "expected"),
    [(0.95, 0.95), (1.7, 1.0), (-0.2, 0.0), (math.nan, 0.0), (math.inf, 0.0), (0.7, 0.7)],
)
def test_confidence_clamped(raw, expected):
    assert to_draft(ex(confidence=raw)).confidence == expected


@pytest.mark.parametrize("raw", [-0.2, math.nan, math.inf, 0.69])
def test_bad_confidence_is_low(raw):
    assert to_draft(ex(per_100g=n(sugars_g=5), confidence=raw)).warnings == ["low_confidence"]


def test_confidence_at_threshold_not_low():
    assert "low_confidence" not in to_draft(ex(confidence=0.7)).warnings


def test_unreadable_fields_become_warnings():
    d = to_draft(
        ex(per_100g=n(sugars_g=5), unreadable_fields=[" sugars_g ", "", "ingredients", "sugars_g"])
    )
    assert d.warnings == ["unreadable_field:sugars_g", "unreadable_field:ingredients"]


def test_missing_category_defaults_to_general_with_warning():
    d = to_draft(ex(per_100g=n(sugars_g=5), category_guess=None))
    assert d.category == "general" and d.warnings == ["category_unknown"]


def test_veg_mark_passed_through():
    assert to_draft(ex(veg_mark="non_veg")).veg_mark == "non_veg"
    assert to_draft(ex(veg_mark=None)).veg_mark is None


def test_mixed_script_ingredients_keep_order_and_script():
    d = to_draft(ex(ingredients=["Wheat flour (गेहूं का आटा)", "  ", "दूध पाउडर", "INS 330"]))
    assert d.ingredients == ["Wheat flour (गेहूं का आटा)", "दूध पाउडर", "INS 330"]


def test_warning_order_is_deterministic():
    d = to_draft(
        ex(
            per_100g=n(energy_kcal=100, protein_g=10, carbs_g=60, fat_g=20, sugars_g=250),
            category_guess=None,
            confidence=0.3,
            unreadable_fields=["fat_g"],
        )
    )
    assert d.warnings == [
        "implausible_value:sugars_g",
        "energy_mismatch",
        "low_confidence",
        "category_unknown",
        "unreadable_field:fat_g",
    ]


def test_input_extraction_not_mutated():
    e = ex(per_100g=None, per_serving=n(sugars_g=5.0), serving_size_g=25)
    before = e.model_dump()
    to_draft(e)
    assert e.model_dump() == before
