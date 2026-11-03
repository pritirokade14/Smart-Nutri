"""Plan 4 Task 3: extraction -> ProductDraft (pure, health-critical)."""

import math

import pytest

from app.features.products.schemas import NutrientsOut
from app.features.scans.normalize import (
    ENGINE_FIELDS,
    UNREADABLE_ALLERGEN_CONFIDENCE_CAP,
    DraftNutrients,
    ProductDraft,
    engine_nutrients,
    to_draft,
)
from app.features.scans.schemas import NutrientsIn, NutritionExtraction
from app.scoring import Category, Member, Nutrients, Product, Status, analyze, load_config


def n(**kw) -> NutrientsIn:
    return NutrientsIn(**(dict.fromkeys(NutrientsIn.model_fields) | kw))


def n_raw(**kw) -> NutrientsIn:
    """Bypasses validation: the schema rejects NaN/inf, the normaliser still must not trust it."""
    return NutrientsIn.model_construct(**(dict.fromkeys(NutrientsIn.model_fields) | kw))


def ex(**kw) -> NutritionExtraction:
    data = {
        "product_name": None,
        "brand": None,
        "basis_detected": "per_100g",
        "per_100g": n(),
        "per_serving": None,
        "per_100_unit": None,
        "serving_size_g": None,
        "serving_size_unit": None,
        "ingredients": [],
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


def upper_withheld(d: ProductDraft) -> list[str]:
    """The protein/fibre part of `engine_withheld` (an upper bound is never evidence)."""
    return [f for f in d.engine_withheld if f in ("protein_g", "fiber_g")]


def ex_raw(**kw) -> NutritionExtraction:
    """`ex()` then unvalidated overrides (values the schema would reject)."""
    return ex().model_copy(update=kw)


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
    # R13: a lone display-only value does not count as per-100 g data.
    assert to_draft(ex(per_100g=n(trans_fat_g=120))).warnings == [
        "implausible_value:trans_fat_g",
        "per_100g_missing",
    ]


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
    d = to_draft(ex_raw(per_100g=n_raw(sugars_g=math.nan, fat_g=math.inf)))
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
    assert d.warnings == ["per_serving_ignored"] and d.engine_withheld == []


def test_derivation_converts_kj_and_keeps_missing_missing():
    d = to_draft(
        ex(
            basis_detected="per_serving",
            per_100g=n(),
            per_serving=n(
                energy_kj=209.2, sodium_mg=50, sodium_unit="mg", added_sugars_g=2, sugars_g=2
            ),
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
    d = to_draft(
        ex(
            basis_detected="per_serving",
            per_100g=None,
            per_serving=n(sugars_g=30),
            serving_size_g=10,
        )
    )
    assert d.per_100g.sugars_g == 300 and d.warnings == ["implausible_value:sugars_g"]


@pytest.mark.parametrize("size", [0, -5, 10_000, math.nan, math.inf])
def test_implausible_serving_size_blocks_derivation(size):
    d = to_draft(
        ex_raw(
            basis_detected="per_serving",
            per_100g=None,
            per_serving=n(sugars_g=5),
            serving_size_g=size,
        )
    )
    assert d.per_100g.sugars_g is None and not d.derived_from_serving
    assert d.warnings == [
        "implausible_value:serving_size_g",
        "per_100g_missing",
        "per_serving_ignored",
    ]


def test_implausible_serving_size_kept_in_draft_when_finite():
    d = to_draft(ex(per_100g=n(sugars_g=5), serving_size_g=10_000))
    assert d.serving_size_g == 10_000 and d.warnings == ["implausible_value:serving_size_g"]


def test_non_finite_serving_size_becomes_none():
    assert to_draft(ex_raw(serving_size_g=math.nan)).serving_size_g is None


def test_no_nutrition_table_at_all():
    d = to_draft(ex(basis_detected="unknown", per_100g=None, per_serving=None))
    assert all(v is None for v in d.per_100g.model_dump().values())
    assert d.warnings == ["per_100g_missing"] and not d.derived_from_serving


def test_per_serving_only_without_size_never_assumes_100g():
    d = to_draft(
        ex(basis_detected="per_serving", per_100g=n(), per_serving=n(energy_kcal=150, fat_g=8))
    )
    assert d.per_100g.energy_kcal is None and d.per_100g.fat_g is None
    assert d.warnings == ["per_100g_missing", "per_serving_ignored"]


@pytest.mark.parametrize(
    ("raw", "expected"),
    [(0.95, 0.95), (1.7, 1.0), (-0.2, 0.0), (math.nan, 0.0), (math.inf, 0.0), (0.7, 0.7)],
)
def test_confidence_clamped(raw, expected):
    # Defence in depth: the R8 schema rejects these, the normaliser still clamps.
    assert to_draft(ex_raw(confidence=raw)).confidence == expected


@pytest.mark.parametrize("raw", [-0.2, math.nan, math.inf, 0.69])
def test_bad_confidence_is_low(raw):
    d = to_draft(ex_raw(per_100g=n(sugars_g=5), confidence=raw))
    assert d.warnings == ["low_confidence"]


def test_confidence_at_threshold_not_low():
    assert "low_confidence" not in to_draft(ex(confidence=0.7)).warnings


def test_unreadable_fields_become_warnings():
    d = to_draft(
        ex(
            per_100g=n(sugars_g=5, fat_g=3),
            unreadable_fields=["per_100g.sugars_g", "per_serving.sodium_mg", "per_100g.sugars_g"],
        )
    )
    assert d.confidence == 0.9
    assert d.per_100g.sugars_g is None and d.per_100g.fat_g == 3  # R13: never trusted
    assert d.warnings == [
        "unreadable_field:per_100g.sugars_g",
        "unreadable_field:per_serving.sodium_mg",
    ]


def test_missing_category_defaults_to_general_with_warning():
    d = to_draft(ex(per_100g=n(sugars_g=5), category_guess=None))
    assert d.category == "general" and d.warnings == ["category_unknown"]


# --- R10: printed units --------------------------------------------------------------


@pytest.mark.parametrize(
    ("value", "unit", "expected", "warnings"),
    [
        (0.4, "g", 400.0, []),
        (400, "mg", 400, []),
        (400, None, 400, ["unit_unconfirmed:per_100g.sodium_mg"]),
    ],
)
def test_sodium_unit(value, unit, expected, warnings):
    d = to_draft(ex(per_100g=n(sodium_mg=value, sodium_unit=unit)))
    assert d.per_100g.sodium_mg == expected and d.warnings == warnings
    assert d.engine_withheld == (["sodium_mg"] if unit is None else [])


def test_sodium_without_unit_on_serving_column_flagged_with_its_path():
    d = to_draft(
        ex(
            basis_detected="per_serving",
            per_100g=None,
            per_serving=n(sodium_mg=50),
            serving_size_g=20,
        )
    )
    assert d.per_100g.sodium_mg == 250  # kept as mg, never silently trusted
    assert d.warnings == ["unit_unconfirmed:per_serving.sodium_mg"]
    assert d.engine_withheld == ["sodium_mg"] and engine_nutrients(d).sodium_mg is None


def test_unit_unconfirmed_on_the_shown_serving_column_is_flagged_not_withheld():
    # R17: the per-serving column is shown (and can be saved with basis per_serving), so a
    # unit-less sodium there is flagged; only the column used for per_100g is withheld.
    d = to_draft(
        ex(
            per_100g=n(sodium_mg=400, sodium_unit="mg"),
            per_serving=n(sodium_mg=120),
            serving_size_g=30,
        )
    )
    assert d.warnings == ["unit_unconfirmed:per_serving.sodium_mg"]
    assert d.engine_withheld == [] and engine_nutrients(d).sodium_mg == 400
    assert d.per_serving is not None and d.per_serving.sodium_mg == 120


def test_unit_unconfirmed_warnings_for_both_columns_in_column_order():
    d = to_draft(
        ex(
            basis_detected="both",
            per_100g=n(sodium_mg=400),
            per_serving=n(sodium_mg=120),
            serving_size_g=30,
        )
    )
    assert d.warnings == [
        "unit_unconfirmed:per_100g.sodium_mg",
        "unit_unconfirmed:per_serving.sodium_mg",
    ]
    assert d.engine_withheld == ["sodium_mg"]


def test_no_unit_warning_without_printed_sodium():
    assert to_draft(ex(per_100g=n(salt_g=1.0))).warnings == []


@pytest.mark.parametrize(
    ("value", "unit", "expected"), [(200, "mg", 0.2), (0.2, "g", 0.2), (0.2, None, 0.2)]
)
def test_trans_fat_unit(value, unit, expected):
    d = to_draft(ex(per_100g=n(fat_g=5, trans_fat_g=value, trans_fat_unit=unit)))
    assert d.per_100g.trans_fat_g == expected and d.warnings == []


def test_sodium_in_grams_then_plausibility_checked():
    d = to_draft(ex(per_100g=n(sodium_mg=50, sodium_unit="g")))
    assert d.per_100g.sodium_mg == 50_000 and d.warnings == ["implausible_value:sodium_mg"]


def test_trans_fat_mg_not_taken_as_grams():
    # 200 mg read as 200 g would be implausible; converted it is 0.2 g.
    d = to_draft(ex(per_100g=n(fat_g=1, trans_fat_g=200, trans_fat_unit="mg")))
    assert d.per_100g.trans_fat_g == 0.2 and d.warnings == []


def test_units_converted_before_serving_derivation():
    d = to_draft(
        ex(
            basis_detected="per_serving",
            per_100g=None,
            per_serving=n(sodium_mg=0.1, sodium_unit="g", trans_fat_g=50, trans_fat_unit="mg"),
            serving_size_g=20,
        )
    )
    assert d.per_100g.sodium_mg == 500 and d.per_100g.trans_fat_g == 0.25
    assert d.derived_from_serving and d.warnings == []


def test_salt_sodium_check_uses_converted_sodium():
    d = to_draft(ex(per_100g=n(salt_g=1.0, sodium_mg=0.4, sodium_unit="g")))
    assert d.per_100g.sodium_mg == 400 and d.warnings == []


# --- R10: ml means a drink -----------------------------------------------------------


@pytest.mark.parametrize(
    ("per_100_unit", "serving_unit", "guess", "category", "warnings"),
    [
        ("ml", None, "general", "beverage", ["category_check"]),
        (None, "ml", "fat", "fat", ["category_check"]),  # R13: an oil keeps "fat"
        ("ml", "ml", "cheese", "cheese", ["category_check"]),
        ("ml", None, None, "beverage", ["category_check"]),
        ("ml", None, "beverage", "beverage", []),
        (None, "ml", "water", "water", []),
        ("g", "g", "general", "general", []),
        ("g", None, None, "general", ["category_unknown"]),
        (None, None, "fat", "fat", []),
    ],
)
def test_ml_means_drink(per_100_unit, serving_unit, guess, category, warnings):
    d = to_draft(
        ex(
            per_100g=n(sugars_g=5),
            per_100_unit=per_100_unit,
            serving_size_unit=serving_unit,
            category_guess=guess,
        )
    )
    assert d.category == category and d.warnings == warnings


# --- R10: "<X" upper bounds ----------------------------------------------------------


def test_upper_bound_value_kept_and_flagged():
    d = to_draft(
        ex(
            per_100g=n(sugars_g=0.5, fat_g=3, trans_fat_g=0.2),
            upper_bound_fields=["per_100g.sugars_g", "per_100g.trans_fat_g", "per_100g.sugars_g"],
        )
    )
    assert d.per_100g.sugars_g == 0.5 and d.per_100g.trans_fat_g == 0.2
    assert d.warnings == ["upper_bound:per_100g.sugars_g", "upper_bound:per_100g.trans_fat_g"]
    assert upper_withheld(d) == []


def test_upper_bound_protein_and_fibre_are_withheld():
    d = to_draft(
        ex(
            per_100g=n(protein_g=0.1, fiber_g=0.5, sugars_g=3),
            upper_bound_fields=["per_100g.fiber_g", "per_100g.protein_g"],
        )
    )
    # Shown to the user as printed ...
    assert d.per_100g.protein_g == 0.1 and d.per_100g.fiber_g == 0.5
    assert upper_withheld(d) == ["protein_g", "fiber_g"]
    assert d.engine_withheld == ["protein_g", "fiber_g"]
    assert d.warnings == ["upper_bound:per_100g.fiber_g", "upper_bound:per_100g.protein_g"]
    # ... but never reach the engine as evidence.
    eng = engine_nutrients(d)
    assert eng.protein_g is None and eng.fiber_g is None and eng.sugars_g == 3


def test_exact_protein_is_not_suppressed():
    d = to_draft(ex(per_100g=n(protein_g=12), upper_bound_fields=["per_100g.sugars_g"]))
    assert upper_withheld(d) == [] and engine_nutrients(d).protein_g == 12


def test_upper_bound_on_unused_column_does_not_suppress():
    d = to_draft(
        ex(
            per_100g=n(protein_g=2),
            per_serving=n(protein_g=0.1),
            serving_size_g=30,
            upper_bound_fields=["per_serving.protein_g"],
        )
    )
    assert upper_withheld(d) == []


def test_upper_bound_on_serving_column_suppresses_when_derived():
    d = to_draft(
        ex(
            basis_detected="per_serving",
            per_100g=None,
            per_serving=n(protein_g=0.1),
            serving_size_g=200,
            serving_size_unit="ml",
            category_guess="beverage",
            upper_bound_fields=["per_serving.protein_g"],
        )
    )
    assert d.per_100g.protein_g == 0.05 and upper_withheld(d) == ["protein_g"]
    assert engine_nutrients(d).protein_g is None


def test_engine_nutrients_drops_display_only_fields():
    d = to_draft(ex(per_100g=n(sugars_g=10, added_sugars_g=6, fat_g=5, trans_fat_g=0.1)))
    assert engine_nutrients(d) == Nutrients(sugars_g=10, fat_g=5)


def test_diet_drink_upper_bound_protein_gives_no_good_protein_density():
    # A diet cola: "<0.1 g protein, <1 kcal" per 100 ml.
    slimmer = Member(id="m7", name="Weight Loss Adult", age=35, goal="weight_loss")
    d = to_draft(
        ex(
            per_100g=n(
                energy_kcal=1,
                protein_g=0.1,
                carbs_g=0,
                sugars_g=0,
                fat_g=0,
                sat_fat_g=0,
                salt_g=0.02,
            ),
            per_100_unit="ml",
            category_guess="beverage",
            upper_bound_fields=["per_100g.energy_kcal", "per_100g.protein_g"],
            ingredients=["carbonated water", "colour (INS 150d)", "sweetener (INS 951)"],
        )
    )
    assert upper_withheld(d) == ["protein_g"]

    def codes(product: Product) -> set[str]:
        return {r.code for r in analyze(product, [slimmer]).verdicts[0].reasons}

    raw = Nutrients(**{f: getattr(d.per_100g, f) for f in NutrientsOut.model_fields})
    assert "good_protein_density" in codes(_engine_product(d, raw))  # control: the bug
    assert "good_protein_density" not in codes(_engine_product(d))


# --- R10: unreadable allergen-relevant fields cap confidence --------------------------


@pytest.mark.parametrize("path", ["ingredients", "allergen_statement", "may_contain_statement"])
def test_unreadable_allergen_field_caps_confidence(path):
    d = to_draft(ex(per_100g=n(sugars_g=5), confidence=0.95, unreadable_fields=[path]))
    assert d.confidence == 0.69
    assert d.warnings == ["low_confidence", f"unreadable_field:{path}"]


def test_unreadable_cap_never_raises_confidence():
    d = to_draft(ex(per_100g=n(sugars_g=5), confidence=0.4, unreadable_fields=["ingredients"]))
    assert d.confidence == 0.4


def test_unreadable_cap_is_below_engine_threshold():
    assert (
        UNREADABLE_ALLERGEN_CONFIDENCE_CAP < load_config().thresholds["min_extraction_confidence"]
    )


def _engine_product(d: ProductDraft, per_100g: Nutrients | None = None) -> Product:
    return Product(
        name="Draft",
        category=Category(d.category),
        per_100g=engine_nutrients(d) if per_100g is None else per_100g,
        serving_size_g=d.serving_size_g,
        ingredients=tuple(d.ingredients),
        allergen_statement=d.allergen_statement,
        may_contain_statement=d.may_contain_statement,
        claims=tuple(d.claims),
        veg_mark=d.veg_mark,
        extraction_confidence=d.confidence,
    )


def _engine_status(d: ProductDraft, member: Member) -> Status:
    return analyze(_engine_product(d), [member]).verdicts[0].status


def test_cut_off_ingredients_make_allergic_member_unknown():
    peanut = Member(id="m1", name="Peanut Allergic", age=30, allergens=("peanut",))
    label = {
        "per_100g": n(energy_kcal=380, protein_g=8, carbs_g=70, sugars_g=4, fat_g=8, salt_g=1.0),
        "ingredients": ["गेहूं का आटा", "नमक"],
        "confidence": 0.95,
    }
    readable = to_draft(ex(**label))
    cut_off = to_draft(ex(**label, unreadable_fields=["ingredients"]))
    assert _engine_status(readable, peanut) != Status.UNKNOWN  # control
    assert _engine_status(cut_off, peanut) == Status.UNKNOWN


# --- R10: kcal vs kJ -----------------------------------------------------------------


@pytest.mark.parametrize(
    ("kcal", "kj", "mismatch"),
    [(100, 418.4, False), (100, 500, False), (100, 2000, True), (500, 1700, True)],
)
def test_kcal_kj_mismatch(kcal, kj, mismatch):
    # tolerance = max(0.15 x kcal, 20): 500 kJ = 119.5 kcal (19.5 off: ok); 1700 kJ = 406 (94 off)
    d = to_draft(ex(per_100g=n(energy_kcal=kcal, energy_kj=kj)))
    assert d.per_100g.energy_kcal == kcal  # printed kcal still wins
    assert d.warnings == (["kcal_kj_mismatch"] if mismatch else [])


def test_kcal_kj_mismatch_checked_on_the_serving_column_used():
    d = to_draft(
        ex(
            basis_detected="per_serving",
            per_100g=None,
            per_serving=n(energy_kcal=120, energy_kj=1000),
            serving_size_g=25,
        )
    )
    assert d.per_100g.energy_kcal == 480 and d.warnings == ["kcal_kj_mismatch"]


def test_veg_mark_passed_through():
    assert to_draft(ex(veg_mark="non_veg")).veg_mark == "non_veg"
    assert to_draft(ex(veg_mark=None)).veg_mark is None


def test_mixed_script_ingredients_keep_order_and_script():
    d = to_draft(ex(ingredients=["Wheat flour (गेहूं का आटा)", "  ", "दूध पाउडर", "INS 330"]))
    assert d.ingredients == ["Wheat flour (गेहूं का आटा)", "दूध पाउडर", "INS 330"]


def test_warning_order_is_deterministic():
    d = to_draft(
        ex(
            per_100g=n(
                energy_kcal=100,
                energy_kj=2000,
                protein_g=10,
                carbs_g=60,
                fat_g=20,
                sugars_g=250,
                salt_g=1.0,
                sodium_mg=1000,
            ),
            category_guess=None,
            confidence=0.3,
            unreadable_fields=["per_100g.fiber_g", "allergen_statement"],
            upper_bound_fields=["per_100g.salt_g"],
        )
    )
    assert d.warnings == [
        "implausible_value:sugars_g",
        "energy_mismatch",
        "kcal_kj_mismatch",
        "salt_sodium_mismatch",
        "unit_unconfirmed:per_100g.sodium_mg",
        "low_confidence",
        "category_unknown",
        "unreadable_field:per_100g.fiber_g",
        "unreadable_field:allergen_statement",
        "upper_bound:per_100g.salt_g",
    ]
    assert d.engine_withheld == ["sodium_mg"]


def test_warning_order_with_ml_override():
    d = to_draft(ex(per_100g=None, per_100_unit="ml", category_guess="general", confidence=0.5))
    assert d.warnings == ["per_100g_missing", "low_confidence", "category_check"]


def test_input_extraction_not_mutated():
    e = ex(per_100g=None, per_serving=n(sugars_g=5.0), serving_size_g=25)
    before = e.model_dump()
    to_draft(e)
    assert e.model_dump() == before


# --- R13: values the engine must not see until the user confirms them ------------------

_MEMBERS = (
    Member(id="peanut", name="Peanut Allergic", age=30, allergens=("peanut",)),
    Member(id="diabetic", name="Diabetic", age=50, conditions=("diabetes",)),
    Member(id="child6", name="Child", age=6),
    Member(id="infant1", name="Infant", age=1),
    Member(id="hypertensive", name="Hypertensive", age=60, conditions=("hypertension",)),
    Member(id="age_unknown", name="No Age", age=None),
    Member(id="weight_loss", name="Weight Loss", age=35, goal="weight_loss"),
)
_INGREDIENTS = ["wheat flour", "milk solids"]
# A complete, readable biscuit label apart from salt/sodium.
_BISCUIT = {
    "energy_kcal": 380,
    "protein_g": 8,
    "carbs_g": 70,
    "sugars_g": 4,
    "fat_g": 8,
    "sat_fat_g": 2,
}
_CARBS_70 = ("carbs_per_serving_high", Status.CAUTION, {"basis": "per_100g", "carbs_g": 70.0})


def _missing(nutrient: str, rule: str) -> tuple[str, Status, dict]:
    return ("nutrient_missing", Status.UNKNOWN, {"nutrient": nutrient, "rule": rule})


_AGE_UNKNOWN = (Status.UNKNOWN, [("age_unknown", Status.UNKNOWN, {})])
_OK: tuple[Status, list] = (Status.OK, [])

# Biscuit with salt unknown (sodium withheld or unreadable, no salt printed).
_TABLE_SALT_UNKNOWN = {
    "peanut": _OK,
    "diabetic": (Status.UNKNOWN, [_missing("salt", "blood_sugar"), _CARBS_70]),
    "child6": (Status.UNKNOWN, [_missing("salt", "child")]),
    "infant1": (Status.UNKNOWN, [_missing("salt", "infant")]),
    "hypertensive": (Status.UNKNOWN, [_missing("salt", "hypertension")]),
    "age_unknown": _AGE_UNKNOWN,
    "weight_loss": _OK,
}
# Biscuit with 1.0 g salt per 100 g (printed as salt, or as 0.4 g sodium).
_TABLE_SALT_1G = {
    "peanut": _OK,
    "diabetic": (Status.CAUTION, [_CARBS_70]),
    "child6": _OK,
    "infant1": (Status.AVOID, [("infant_salt_high", Status.AVOID, {"salt_g": 1.0})]),
    "hypertensive": (Status.CAUTION, [("salt_moderate", Status.CAUTION, {"salt_g": 1.0})]),
    "age_unknown": _AGE_UNKNOWN,
    "weight_loss": _OK,
}
# Every engine field withheld (basis mismatch); serving size 30 g.
_TABLE_ALL_WITHHELD = {
    "peanut": _OK,
    "diabetic": (
        Status.UNKNOWN,
        [
            _missing("sugars_g", "blood_sugar"),
            _missing("carbs_g", "blood_sugar"),
            _missing("salt", "blood_sugar"),
            _missing("sat_fat", "blood_sugar"),
        ],
    ),
    "child6": (Status.UNKNOWN, [_missing("sugars_g", "child"), _missing("salt", "child")]),
    "infant1": (Status.UNKNOWN, [_missing("salt", "infant")]),
    "hypertensive": (Status.UNKNOWN, [_missing("salt", "hypertension")]),
    "age_unknown": _AGE_UNKNOWN,
    "weight_loss": (
        Status.UNKNOWN,
        [_missing("energy_kcal", "weight_loss"), _missing("protein_g", "weight_loss")],
    ),
}
_ALL_OK = {m.id: _OK for m in _MEMBERS}


def _table(d: ProductDraft, per_100g: Nutrients | None = None) -> dict:
    result = analyze(_engine_product(d, per_100g), list(_MEMBERS))
    return {
        v.member_id: (v.status, [(r.code, r.severity, dict(r.params)) for r in v.reasons])
        for v in result.verdicts
    }


def _raw(d: ProductDraft) -> Nutrients:
    """The draft's values with nothing withheld: what the engine saw before R13."""
    return Nutrients(**{f: getattr(d.per_100g, f) for f in ENGINE_FIELDS})


def test_engine_fields_are_the_engine_inputs_in_engine_order():
    assert ENGINE_FIELDS == tuple(
        f for f in Nutrients.__dataclass_fields__ if f in DraftNutrients.model_fields
    )


# BLOCKING 1: sodium printed without a unit


def test_sodium_without_unit_is_withheld_from_the_engine():
    # "Sodium 0.4" with no unit: really 0.4 g (1.0 g salt). Taken as 0.4 mg it reads as
    # salt-free and every salt-sensitive member got OK.
    d = to_draft(ex(per_100g=n(**_BISCUIT, sodium_mg=0.4), ingredients=_INGREDIENTS))
    assert d.per_100g.sodium_mg == 0.4  # shown as printed for the user to confirm
    assert d.warnings == ["unit_unconfirmed:per_100g.sodium_mg"]
    assert d.engine_withheld == ["sodium_mg"]
    assert engine_nutrients(d) == Nutrients(**_BISCUIT)
    assert _table(d, _raw(d)) == _ALL_OK | {"diabetic": (Status.CAUTION, [_CARBS_70])}  # bug
    assert _table(d) == _TABLE_SALT_UNKNOWN


def test_sodium_without_unit_still_protected_by_printed_salt():
    d = to_draft(ex(per_100g=n(**_BISCUIT, salt_g=1.0, sodium_mg=0.4), ingredients=_INGREDIENTS))
    assert d.engine_withheld == ["sodium_mg"]
    assert engine_nutrients(d) == Nutrients(**_BISCUIT, salt_g=1.0)
    assert _table(d) == _TABLE_SALT_1G


def test_sodium_with_printed_unit_reaches_the_engine():
    d = to_draft(
        ex(per_100g=n(**_BISCUIT, sodium_mg=0.4, sodium_unit="g"), ingredients=_INGREDIENTS)
    )
    assert d.engine_withheld == [] and d.warnings == []
    assert engine_nutrients(d) == Nutrients(**_BISCUIT, sodium_mg=400)
    assert _table(d) == _TABLE_SALT_1G


# BLOCKING 2: unreadable nutrient values are never trusted


def test_unreadable_sodium_value_becomes_none():
    d = to_draft(
        ex(
            per_100g=n(**_BISCUIT, sodium_mg=5, sodium_unit="mg"),
            ingredients=_INGREDIENTS,
            unreadable_fields=["per_100g.sodium_mg"],
        )
    )
    assert d.per_100g.sodium_mg is None
    assert d.warnings == ["unreadable_field:per_100g.sodium_mg"]
    assert d.engine_withheld == []  # nothing left to withhold: the value is gone
    assert _table(d) == _TABLE_SALT_UNKNOWN


def test_unreadable_unitless_sodium_has_no_unit_warning():
    d = to_draft(ex(per_100g=n(salt_g=1.0, sodium_mg=5), unreadable_fields=["per_100g.sodium_mg"]))
    assert d.per_100g.sodium_mg is None and d.engine_withheld == []
    assert d.warnings == ["unreadable_field:per_100g.sodium_mg"]


def test_unreadable_sugars_value_becomes_none():
    d = to_draft(
        ex(
            per_100g=n(**_BISCUIT, salt_g=0.1),
            ingredients=_INGREDIENTS,
            unreadable_fields=["per_100g.sugars_g"],
        )
    )
    assert d.per_100g.sugars_g is None
    assert d.warnings == ["unreadable_field:per_100g.sugars_g"]
    assert _table(d) == {
        "peanut": _OK,
        "diabetic": (Status.UNKNOWN, [_missing("sugars_g", "blood_sugar"), _CARBS_70]),
        "child6": (Status.UNKNOWN, [_missing("sugars_g", "child")]),
        "infant1": _OK,
        "hypertensive": _OK,  # salt (0.1 g) was readable
        "age_unknown": _AGE_UNKNOWN,
        "weight_loss": _OK,
    }


def test_unreadable_serving_value_cleared_before_derivation():
    d = to_draft(
        ex(
            basis_detected="per_serving",
            per_100g=None,
            per_serving=n(sugars_g=5, sodium_mg=50, sodium_unit="mg"),
            serving_size_g=25,
            unreadable_fields=["per_serving.sugars_g"],
        )
    )
    assert d.derived_from_serving
    assert d.per_100g.sugars_g is None and d.per_100g.sodium_mg == 200
    assert d.warnings == ["unreadable_field:per_serving.sugars_g"]


def test_unreadable_kj_is_not_converted_to_kcal():
    d = to_draft(ex(per_100g=n(energy_kj=2000, fat_g=3), unreadable_fields=["per_100g.energy_kj"]))
    assert d.per_100g.energy_kcal is None


def test_unreadable_path_on_the_unused_column_does_not_clear_the_used_one():
    d = to_draft(
        ex(
            basis_detected="both",
            per_100g=n(sugars_g=20),
            per_serving=n(sugars_g=6),
            serving_size_g=30,
            unreadable_fields=["per_serving.sugars_g"],
        )
    )
    assert d.per_100g.sugars_g == 20 and d.warnings == ["unreadable_field:per_serving.sugars_g"]


def test_per_100_column_with_only_unreadable_values_counts_as_empty():
    d = to_draft(
        ex(
            basis_detected="both",
            per_100g=n(sugars_g=3),
            per_serving=n(sugars_g=6),
            serving_size_g=30,
            unreadable_fields=["per_100g.sugars_g"],
        )
    )
    assert d.derived_from_serving and d.per_100g.sugars_g == 20


def test_unreadable_serving_size_blocks_derivation():
    d = to_draft(
        ex(
            basis_detected="per_serving",
            per_100g=None,
            per_serving=n(sugars_g=5),
            serving_size_g=25,
            unreadable_fields=["serving_size_g"],
        )
    )
    assert d.serving_size_g is None and not d.derived_from_serving
    assert d.per_100g.sugars_g is None
    assert d.warnings == [
        "per_100g_missing",
        "per_serving_ignored",
        "unreadable_field:serving_size_g",
    ]


# BLOCKING 3: the basis the model detected disagrees with the column it filled


def test_per_serving_numbers_in_the_per_100g_object_are_withheld():
    # The reviewer's case: basis per_serving, serving 30 g, but the per-serving numbers
    # went into per_100g (true per 100 g: 400 mg sodium, 5 g sugars).
    d = to_draft(
        ex(
            basis_detected="per_serving",
            per_100g=n(
                energy_kcal=40,
                protein_g=1,
                carbs_g=6,
                sugars_g=1.5,
                fat_g=1,
                sat_fat_g=0.3,
                sodium_mg=120,
                sodium_unit="mg",
            ),
            per_serving=None,
            serving_size_g=30,
            ingredients=_INGREDIENTS,
        )
    )
    assert d.per_100g.sodium_mg == 120 and d.per_100g.sugars_g == 1.5  # shown as printed
    assert not d.derived_from_serving
    assert d.warnings == ["basis_mismatch"]
    assert d.engine_withheld == list(ENGINE_FIELDS)
    assert engine_nutrients(d) == Nutrients()
    assert _table(d, _raw(d)) == _ALL_OK  # control: the bug
    assert _table(d) == _TABLE_ALL_WITHHELD


def test_per_100g_basis_with_only_serving_values_is_withheld():
    d = to_draft(
        ex(
            basis_detected="per_100g",
            per_100g=None,
            per_serving=n(sugars_g=1.5, sodium_mg=120, sodium_unit="mg"),
            serving_size_g=30,
            ingredients=_INGREDIENTS,
        )
    )
    assert d.derived_from_serving and d.per_100g.sodium_mg == 400
    assert d.warnings == ["basis_mismatch"]
    assert d.engine_withheld == list(ENGINE_FIELDS) and engine_nutrients(d) == Nutrients()
    assert _table(d) == _TABLE_ALL_WITHHELD


@pytest.mark.parametrize(
    "columns",
    [
        {"per_100g": n(sodium_mg=120, sodium_unit="mg", sugars_g=1.5)},
        {"per_100g": None, "per_serving": n(sugars_g=1.5)},
    ],
)
def test_unknown_basis_with_values_is_withheld(columns):
    d = to_draft(
        ex(basis_detected="unknown", serving_size_g=30, ingredients=_INGREDIENTS, **columns)
    )
    assert d.warnings == ["basis_mismatch"]
    assert d.engine_withheld == list(ENGINE_FIELDS) and engine_nutrients(d) == Nutrients()
    assert _table(d) == _TABLE_ALL_WITHHELD


@pytest.mark.parametrize(
    ("basis", "columns"),
    [
        ("per_100g", {"per_100g": n(sugars_g=5)}),
        ("both", {"per_100g": n(sugars_g=5), "per_serving": n(sugars_g=2)}),
        ("both", {"per_100g": n(sugars_g=5)}),
        ("per_serving", {"per_100g": None, "per_serving": n(sugars_g=2)}),
        ("per_serving", {"per_100g": n(sugars_g=5), "per_serving": n(sugars_g=2)}),
        ("unknown", {"per_100g": None}),
    ],
)
def test_consistent_basis_has_no_mismatch(basis, columns):
    d = to_draft(ex(basis_detected=basis, serving_size_g=40, **columns))
    assert "basis_mismatch" not in d.warnings and d.engine_withheld == []


def test_display_only_values_do_not_block_derivation():
    # basis per_serving; the per-100 g column holds only "trans fat 0".
    d = to_draft(
        ex(
            basis_detected="per_serving",
            per_100g=n(trans_fat_g=0),
            per_serving=n(sugars_g=6, salt_g=0.3),
            serving_size_g=30,
        )
    )
    assert d.derived_from_serving
    assert d.per_100g.sugars_g == 6 * 100 / 30 and d.per_100g.salt_g == 0.3 * 100 / 30
    assert d.warnings == [] and d.engine_withheld == []


@pytest.mark.parametrize("display", [{"trans_fat_g": 0}, {"added_sugars_g": 0}])
def test_display_only_values_do_not_hide_per_100g_missing(display):
    d = to_draft(ex(per_100g=n(**display)))
    assert d.warnings == ["per_100g_missing"]


# SHOULD: per_serving_ignored, categories, unrounded derivation


def test_mixed_columns_flag_ignored_serving_values():
    d = to_draft(
        ex(
            basis_detected="both",
            per_100g=n(energy_kcal=450),
            per_serving=n(sugars_g=12, salt_g=0.6, energy_kcal=135),
            serving_size_g=30,
        )
    )
    assert d.per_100g.energy_kcal == 450 and d.per_100g.sugars_g is None  # still no mixing
    assert d.warnings == ["per_serving_ignored"]


def test_serving_values_also_printed_per_100g_are_not_ignored():
    d = to_draft(
        ex(
            basis_detected="both",
            per_100g=n(energy_kcal=450, sugars_g=40),
            per_serving=n(energy_kcal=135, sugars_g=12),
            serving_size_g=30,
        )
    )
    assert d.warnings == []


def test_oil_per_100_ml_keeps_fat_category():
    d = to_draft(
        ex(
            per_100g=n(energy_kcal=828, fat_g=92, sat_fat_g=10),
            per_100_unit="ml",
            category_guess="fat",
        )
    )
    assert d.category == "fat" and d.warnings == ["category_check"]


def test_derived_values_are_not_rounded():
    d = to_draft(
        ex(
            basis_detected="per_serving",
            per_100g=None,
            per_serving=n(sugars_g=1, salt_g=0.1),
            serving_size_g=30,
        )
    )
    assert d.per_100g.sugars_g == 1 * 100 / 30 and d.per_100g.salt_g == 0.1 * 100 / 30


def test_warning_order_with_basis_warnings():
    d = to_draft(
        ex(
            basis_detected="unknown",
            per_100g=n(sugars_g=250, energy_kcal=100, sodium_mg=300),
            per_serving=n(fat_g=3),
            serving_size_g=30,
            category_guess=None,
            confidence=0.5,
        )
    )
    assert d.warnings == [
        "implausible_value:sugars_g",
        "basis_mismatch",
        "per_serving_ignored",
        "unit_unconfirmed:per_100g.sodium_mg",
        "low_confidence",
        "category_unknown",
    ]
    assert d.engine_withheld == list(ENGINE_FIELDS)


# Contract: engine_withheld


def test_engine_withheld_is_deduplicated_in_engine_order():
    base = to_draft(ex(per_100g=n(protein_g=12, sodium_mg=100, sodium_unit="mg")))
    withheld = ["sodium_mg", "protein_g", "sodium_mg"]
    d = ProductDraft(**(base.model_dump() | {"engine_withheld": withheld}))
    assert d.engine_withheld == ["protein_g", "sodium_mg"]
    assert engine_nutrients(d) == Nutrients()


def test_engine_withheld_rejects_non_engine_fields():
    base = to_draft(ex(per_100g=n(sugars_g=3)))
    with pytest.raises(ValueError):
        ProductDraft(**(base.model_dump() | {"engine_withheld": ["trans_fat_g"]}))


# R17: the printed per-serving column is shown; the server's conversion helpers


def test_per_serving_column_is_shown_after_clearing_and_kj():
    d = to_draft(
        ex(
            per_100g=n(sugars_g=5, energy_kcal=100),
            per_serving=n(
                energy_kj=418.4,
                sugars_g=1.5,
                protein_g=9,
                sodium_mg=0.2,
                sodium_unit="g",
                trans_fat_g=50,
                trans_fat_unit="mg",
            ),
            serving_size_g=30,
            unreadable_fields=["per_serving.protein_g"],
        )
    )
    assert isinstance(d.per_serving, DraftNutrients)
    ps = d.per_serving
    assert ps.energy_kcal == pytest.approx(100) and ps.sugars_g == 1.5
    assert ps.protein_g is None  # unreadable: cleared
    assert ps.sodium_mg == 200 and ps.trans_fat_g == 0.05
    assert d.per_100g.sugars_g == 5  # the per-100 g column is still the one used


def test_per_serving_is_none_without_a_printed_serving_column():
    assert to_draft(ex(per_100g=n(sugars_g=5))).per_serving is None
    assert to_draft(ex(per_100g=n(sugars_g=5), per_serving=n())).per_serving is None


def test_per_serving_kept_when_derived():
    d = to_draft(
        ex(
            basis_detected="per_serving",
            per_100g=None,
            per_serving=n(sugars_g=9),
            serving_size_g=300,
        )
    )
    assert d.derived_from_serving and d.per_100g.sugars_g == 3
    assert d.per_serving.sugars_g == 9


def test_stored_draft_without_per_serving_still_loads():
    base = to_draft(ex(per_100g=n(sugars_g=3))).model_dump()
    del base["per_serving"]
    assert ProductDraft.model_validate(base).per_serving is None


@pytest.mark.parametrize(
    ("value", "unit", "expected"),
    [(0.4, "g", 400.0), (400, "mg", 400), (400, None, 400), (None, "g", None)],
)
def test_sodium_to_mg(value, unit, expected):
    from app.features.scans.normalize import sodium_to_mg

    assert sodium_to_mg(value, unit) == expected


@pytest.mark.parametrize(
    ("value", "serving", "expected"), [(9, 30, 30.0), (10, 25, 40.0), (None, 30, None)]
)
def test_per_100g_from_serving(value, serving, expected):
    from app.features.scans.normalize import per_100g_from_serving

    assert per_100g_from_serving(value, serving) == expected


def test_derivation_uses_the_public_helper_exactly():
    from app.features.scans.normalize import per_100g_from_serving

    d = to_draft(
        ex(
            basis_detected="per_serving",
            per_100g=None,
            per_serving=n(carbs_g=20),
            serving_size_g=30,
        )
    )
    assert d.per_100g.carbs_g == per_100g_from_serving(20, 30)


def test_implausible_fields_matches_the_draft_flags():
    from app.features.scans.normalize import implausible_fields

    values = dict.fromkeys(DraftNutrients.model_fields) | {
        "sugars_g": 40,
        "carbs_g": 20,
        "added_sugars_g": 50,
    }
    assert implausible_fields(values, serving_size_g=0) == [
        "carbs_g",
        "sugars_g",
        "added_sugars_g",
        "serving_size_g",
    ]
    assert implausible_fields({"sugars_g": 5}, serving_size_g=30) == []
