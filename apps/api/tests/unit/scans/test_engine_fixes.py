"""Engine fixes EF2 and EF3 from the real-data experiments (E5 fault injection on 462+ Open
Food Facts panels; .research/data/e5_after_fix.json).

EF2 (safety): a label that prints sodium only (no salt), in g, read as mg ("0.4 g" -> 0.4 mg).
Nothing could cross-check it, so a salty food reached the engine as almost sodium-free. Now a
non-zero sodium below SODIUM_SUSPECT_MAX_MG per 100 g / 100 ml (water exempt), printed as mg
with no salt on that column, raises `sodium_unit_suspect:<path>`: sodium is withheld and the
confirm screen must ask mg or g (`sodium_unit_required`), exactly as for a unit-less sodium.

EF3: a /10 decimal slip on energy, protein, carbs or fat that the 15 % Atwater tolerance hides.
When the printed panel misses a TIGHT Atwater fit and multiplying exactly one of those fields
by 10 gives a tight fit (and the panel stays physically consistent), that field is named
`decimal_shift:<path>` and withheld.
"""

import pytest

from app.features.products.confirm_rules import sodium_unit_unconfirmed, withheld_fields
from app.features.products.schemas import PrintedNutrients, ProductCreate
from app.features.products.service import stored_values
from app.features.scans.normalize import (
    DECIMAL_PROBE_MIN_GAIN,
    DECIMAL_PROBE_TIGHT_MIN_KCAL,
    DECIMAL_PROBE_TIGHT_RATIO,
    SODIUM_DECIMAL_MAX_MG,
    SODIUM_SUSPECT_MAX_MG,
    WARNING_CODES,
    engine_nutrients,
    to_draft,
)
from app.features.scans.schemas import NutrientsIn, NutritionExtraction

# Sodium-only namkeen label: sodium printed in g (0.4 g = 400 mg), read as 0.4 "mg".
# 4*10 + 4*50 + 9*30 = 510 kcal (label 510): Atwater-consistent.
SODIUM_ONLY = {
    "energy_kcal": 510.0,
    "protein_g": 10.0,
    "carbs_g": 50.0,
    "sugars_g": 3.0,
    "fat_g": 30.0,
    "sat_fat_g": 12.0,
    "fiber_g": None,
    "salt_g": None,
    "sodium_mg": 0.4,
    "sodium_unit": "mg",
}


def n(**kw) -> NutrientsIn:
    return NutrientsIn(**(dict.fromkeys(NutrientsIn.model_fields) | SODIUM_ONLY | kw))


def ex(**kw) -> NutritionExtraction:
    data = {
        "product_name": "Namkeen",
        "brand": None,
        "basis_detected": "per_100g",
        "per_100g": n(),
        "per_serving": None,
        "per_100_unit": "g",
        "serving_size_g": None,
        "serving_size_unit": None,
        "ingredients": ["gram flour", "salt"],
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


SUSPECT_100 = "sodium_unit_suspect:per_100g.sodium_mg"


# --- EF2 --------------------------------------------------------------------------------------
def test_thresholds_are_the_measured_constants():
    # Chosen with the E5 method on Open Food Facts panels (see normalize.py).
    assert SODIUM_SUSPECT_MAX_MG == {"food": 10.0, "beverage": 0.5}
    assert SODIUM_DECIMAL_MAX_MG == 100.0
    assert "sodium_unit_suspect" in WARNING_CODES
    assert WARNING_CODES.index("sodium_unit_suspect") == WARNING_CODES.index("unit_unconfirmed") + 1


def test_sodium_in_g_read_as_mg_without_salt_is_withheld_and_asks_the_unit():
    d = to_draft(ex())
    assert SUSPECT_100 in d.warnings
    assert "sodium_mg" in d.engine_withheld
    assert engine_nutrients(d).sodium_mg is None  # the engine never sees ~0 sodium
    assert d.per_100g.sodium_mg == pytest.approx(0.4)  # shown as printed, never changed
    col = d.confirm.columns.per_100g
    assert col is not None and col.sodium_unit_required is True
    assert "sodium_mg" not in col.confirm_fields  # the unit pick confirms it
    assert sodium_unit_unconfirmed(d) and "sodium_mg" in withheld_fields(d)


@pytest.mark.parametrize(
    ("category", "sodium", "suspect"),
    [
        ("general", 9.0, True),  # whole number below 10 mg, no salt row
        ("general", 10.0, False),
        ("general", 1.99, True),
        ("general", 0.0, False),  # "0" / "Nil" is the same in mg and g
        ("fat", 0.5, True),
        ("cheese", 1.0, True),
        (None, 1.0, True),  # category unknown: the food threshold
        ("beverage", 0.49, True),
        ("beverage", 0.5, False),
        ("beverage", 3.0, False),  # colas print ~3-10 mg
        ("water", 0.1, False),  # plain water can be almost sodium-free
    ],
)
def test_threshold_by_category(category, sodium, suspect):
    d = to_draft(ex(category_guess=category, per_100g=n(sodium_mg=sodium)))
    assert (SUSPECT_100 in d.warnings) is suspect
    assert ("sodium_mg" in d.engine_withheld) is suspect


@pytest.mark.parametrize(
    ("name", "sodium"),
    [("pickle", 2.5), ("papad", 2.2), ("masala", 6.0), ("soy sauce", 5.7)],
)
def test_very_salty_products_printed_in_g_read_as_mg_are_flagged(name, sodium):
    # 2.5 g of sodium per 100 g printed in g and read as "2.5 mg": EF2 used to miss these.
    d = to_draft(ex(product_name=name, per_100g=n(sodium_mg=sodium)))
    assert SUSPECT_100 in d.warnings and "sodium_mg" in d.engine_withheld


@pytest.mark.parametrize("sodium", [12.5, 45.5, 99.9])
def test_non_integer_mg_below_100_is_flagged(sodium):
    # Honest mg labels rarely print decimals: 45.5 "mg" is more likely 0.0455 g misread.
    d = to_draft(ex(per_100g=n(sodium_mg=sodium)))
    assert SUSPECT_100 in d.warnings and "sodium_mg" in d.engine_withheld


@pytest.mark.parametrize("sodium", [10.0, 35.0, 350.0, 1200.0, 100.5, 350.5])
def test_honest_integer_or_large_mg_is_not_flagged(sodium):
    d = to_draft(ex(per_100g=n(sodium_mg=sodium)))
    assert not any(w.startswith("sodium_unit_suspect") for w in d.warnings)
    assert "sodium_mg" not in d.engine_withheld


def test_non_integer_mg_with_salt_printed_is_not_flagged():
    d = to_draft(ex(per_100g=n(sodium_mg=45.5, salt_g=0.12)))
    assert SUSPECT_100 not in d.warnings


def test_ml_drink_uses_the_beverage_threshold():
    # No guess, per 100 ml: the draft category is beverage, so 1.0 mg is plausible (a soda).
    drink = n(
        energy_kcal=44.0,
        protein_g=0.0,
        carbs_g=11.0,
        sugars_g=11.0,
        fat_g=0.0,
        sat_fat_g=0.0,
        sodium_mg=1.0,
    )
    d = to_draft(ex(category_guess=None, per_100_unit="ml", per_100g=drink))
    assert d.category == "beverage" and SUSPECT_100 not in d.warnings


def test_printed_salt_is_the_cross_check_so_no_suspicion():
    # Salt printed and agreeing: a genuinely low-sodium food (rice, flour) is not flagged.
    d = to_draft(ex(per_100g=n(sodium_mg=1.0, salt_g=0.0025)))
    assert SUSPECT_100 not in d.warnings and "sodium_mg" not in d.engine_withheld


def test_printed_g_unit_is_converted_not_suspected():
    d = to_draft(ex(per_100g=n(sodium_mg=0.4, sodium_unit="g")))
    assert d.per_100g.sodium_mg == pytest.approx(400) and SUSPECT_100 not in d.warnings


def test_unitless_sodium_keeps_unit_unconfirmed_only():
    d = to_draft(ex(per_100g=n(sodium_unit=None)))
    assert "unit_unconfirmed:per_100g.sodium_mg" in d.warnings
    assert SUSPECT_100 not in d.warnings


def test_per_serving_column_is_checked_per_100g_via_the_serving():
    # Per 30 g serving: 0.12 "mg" = 0.4 mg / 100 g -> suspect on the serving column too.
    serving = n(
        energy_kcal=153.0,
        protein_g=3.0,
        carbs_g=15.0,
        sugars_g=0.9,
        fat_g=9.0,
        sat_fat_g=3.6,
        sodium_mg=0.12,
    )
    d = to_draft(
        ex(
            per_100g=None,
            per_serving=serving,
            serving_size_g=30.0,
            serving_size_unit="g",
            basis_detected="per_serving",
        )
    )
    assert d.derived_from_serving
    assert "sodium_unit_suspect:per_serving.sodium_mg" in d.warnings
    assert "sodium_mg" in d.engine_withheld
    assert d.confirm.columns.per_serving.sodium_unit_required is True
    # 30 g serving at 4 mg = 13.3 mg / 100 g: plausible.
    ok = to_draft(
        ex(
            per_100g=None,
            per_serving=serving.model_copy(update={"sodium_mg": 4.0}),
            serving_size_g=30.0,
            serving_size_unit="g",
            basis_detected="per_serving",
        )
    )
    assert not any(w.startswith("sodium_unit_suspect") for w in ok.warnings)


def test_save_needs_the_unit_and_g_restores_the_real_sodium():
    draft = to_draft(ex())

    def body(unit):
        return ProductCreate(
            name="Namkeen",
            category="general",
            basis="per_100g",
            nutrients=PrintedNutrients(
                **{k: v for k, v in SODIUM_ONLY.items() if k in PrintedNutrients.model_fields}
            ),
            sodium_unit=unit,
            confirmed_fields=[],
        )

    with pytest.raises(Exception) as err:
        stored_values(body(None), draft)
    assert "sodium_unit" in str(err.value.details)  # type: ignore[attr-defined]
    values, _ = stored_values(body("g"), draft)
    assert values["sodium_mg"] == pytest.approx(400)
    values, _ = stored_values(body("mg"), draft)  # the user says the pack really prints mg
    assert values["sodium_mg"] == pytest.approx(0.4)


# --- EF3 --------------------------------------------------------------------------------------
# Biscuit, honest panel: 4*7 + 4*70 + 9*18 = 470 kcal (label 470). Salt printed and consistent.
BISCUIT = {
    "energy_kcal": 470.0,
    "protein_g": 7.0,
    "carbs_g": 70.0,
    "sugars_g": 25.0,
    "fat_g": 18.0,
    "sat_fat_g": 9.0,
    "fiber_g": None,
    "salt_g": 0.75,
    "sodium_mg": 300.0,
    "sodium_unit": "mg",
}


def biscuit(**kw) -> NutritionExtraction:
    col = NutrientsIn(**(dict.fromkeys(NutrientsIn.model_fields) | BISCUIT | kw))
    return ex(per_100g=col)


def test_probe_constants():
    assert (DECIMAL_PROBE_TIGHT_RATIO, DECIMAL_PROBE_TIGHT_MIN_KCAL, DECIMAL_PROBE_MIN_GAIN) == (
        0.03,
        5.0,
        3.0,
    )


def test_honest_biscuit_has_no_warning():
    d = to_draft(biscuit())
    assert d.warnings == [] and d.engine_withheld == []


def test_protein_slip_hidden_by_the_loose_tolerance_is_withheld():
    # Protein 7 printed 0.7: Atwater 444.8 vs 470 kcal is within 15 % (no energy_mismatch),
    # but protein x 10 fits exactly.
    d = to_draft(biscuit(protein_g=0.7))
    assert "energy_mismatch" not in d.warnings
    assert "decimal_shift:per_100g.protein_g" in d.warnings
    assert d.engine_withheld == ["protein_g"]
    assert engine_nutrients(d).protein_g is None
    assert "protein_g" in d.confirm.columns.per_100g.confirm_fields


@pytest.mark.parametrize(
    ("field", "slipped", "named"),
    [
        ("fat_g", 1.8, True),
        ("energy_kcal", 47.0, True),
        # 70 g carbs printed 7: protein x 10 would also fit, so no single field is named, but
        # energy_mismatch still withholds carbs (and the other Atwater fields).
        ("carbs_g", 7.0, False),
    ],
)
def test_other_atwater_field_slips_are_withheld(field, slipped, named):
    d = to_draft(biscuit(**{field: slipped}))
    assert (f"decimal_shift:per_100g.{field}" in d.warnings) is named
    assert field in d.engine_withheld


def test_a_printed_value_that_is_too_high_is_never_shrunk_by_the_tight_probe():
    # A real juice panel (OFF): 4*14 + 9*0.9 = 64.1 vs 56 kcal. Fat / 10 would fit tightly, but
    # only "printed too low" (x 10) is probed tightly: honest labels did this in E5.
    d = to_draft(
        biscuit(
            energy_kcal=56.0, protein_g=0.0, carbs_g=14.0, sugars_g=13.79, fat_g=0.9, sat_fat_g=0.5
        )
    )
    assert not any(w.startswith("decimal_shift") for w in d.warnings)
    assert d.engine_withheld == []


def test_tight_probe_skips_a_panel_with_an_upper_bound():
    # Protein printed "<0.7 g" is a bound, not a reading: the Atwater gap is not evidence.
    d = to_draft(
        biscuit(protein_g=0.7).model_copy(update={"upper_bound_fields": ["per_100g.protein_g"]})
    )
    assert not any(w.startswith("decimal_shift") for w in d.warnings)
    assert "protein_g" in d.engine_withheld  # withheld anyway as an upper bound


def test_tight_probe_respects_macro_consistency():
    # 4*1.5 + 4*65 + 9*26 = 500 vs 554 kcal (within 15 %). Protein x 10 would fit exactly but
    # makes protein + carbs + fat 106 g, which the engine rejects: no suspect is named.
    d = to_draft(
        biscuit(
            energy_kcal=554.0, protein_g=1.5, carbs_g=65.0, fat_g=26.0, sat_fat_g=5.0, sugars_g=5.0
        )
    )
    assert "energy_mismatch" not in d.warnings
    assert not any(w.startswith("decimal_shift") for w in d.warnings)
