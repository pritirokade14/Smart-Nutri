"""Ruling R21(a): the server tells clients what to ask on the confirm screen.

`ProductDraft.confirm` is computed by `app.features.products.confirm_rules`, the same helpers
`create_product` uses to enforce a save. One test per R21(c) draft case, plus the helpers
the save path calls.
"""

import pytest

from app.features.products.confirm_rules import (
    ColumnConfirm,
    DraftConfirm,
    basis_required,
    category_required,
    confirm_hints,
    needs_serving_confirmation,
    sodium_unit_unconfirmed,
    withheld_fields,
)
from app.features.scans.normalize import ENGINE_FIELDS, ProductDraft, to_draft
from app.features.scans.schemas import NutrientsIn, NutritionExtraction

# Plausible both as per 100 g and as per 30 g serving (x 100/30).
VALUES = {
    "energy_kcal": 150.0,
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
    return NutrientsIn(**(dict.fromkeys(NutrientsIn.model_fields) | VALUES | kw))


def ns(**kw) -> NutrientsIn:
    """The same food per 30 g serving (agrees with `n()`: no `column_mismatch`)."""
    scaled = {k: v * 0.3 if isinstance(v, float) else v for k, v in VALUES.items()}
    return NutrientsIn(**(dict.fromkeys(NutrientsIn.model_fields) | scaled | kw))


def ex(**kw) -> NutritionExtraction:
    data = {
        "product_name": "Test Snack",
        "brand": "Acme",
        "basis_detected": "per_100g",
        "per_100g": n(),
        "per_serving": None,
        "per_100_unit": "g",
        "serving_size_g": None,
        "serving_size_unit": None,
        "ingredients": ["wheat flour", "sugar"],
        "allergen_statement": "Contains wheat",
        "may_contain_statement": None,
        "claims": [],
        "veg_mark": "veg",
        "category_guess": "general",
        "confidence": 0.9,
        "unreadable_fields": [],
        "upper_bound_fields": [],
    }
    return NutritionExtraction(**(data | kw))


def col(
    printed: bool = True,
    shared: bool = False,
    confirm_fields: list[str] | None = None,
    sodium_unit_required: bool = False,
    serving_required: bool = False,
) -> ColumnConfirm:
    return ColumnConfirm(
        printed=printed,
        shared=shared,
        confirm_fields=confirm_fields or [],
        sodium_unit_required=sodium_unit_required,
        serving_required=serving_required,
    )


def hints(
    per_100g: ColumnConfirm | None = None,
    per_serving: ColumnConfirm | None = None,
    *,
    basis: bool = False,
    category: bool = False,
) -> DraftConfirm:
    return DraftConfirm.model_validate(
        {
            "basis_required": basis,
            "category_required": category,
            "columns": {
                "per_100g": None if per_100g is None else per_100g.model_dump(),
                "per_serving": None if per_serving is None else per_serving.model_dump(),
            },
        }
    )


CLEAN = hints(col())


# --- one test per R21(c) case ---------------------------------------------------------------


def test_clean_draft_needs_nothing_and_offers_only_per_100g():
    d = to_draft(ex())
    assert d.confirm == CLEAN
    assert d.confirm == confirm_hints(d)


def test_clean_draft_with_a_serving_asks_to_tick_it():
    # R18: a scanned serving size is stored only when ticked.
    d = to_draft(ex(serving_size_g=30))
    assert d.confirm == hints(col(confirm_fields=["serving_size_g"]))


def test_basis_mismatch_both_columns_printed():
    d = to_draft(ex(basis_detected="unknown", per_serving=ns(), serving_size_g=30))
    assert "basis_mismatch" in d.warnings
    assert d.confirm == hints(
        col(confirm_fields=["serving_size_g"]),
        col(confirm_fields=["serving_size_g"], serving_required=True),
        basis=True,
    )


def test_basis_mismatch_one_column_is_shared():
    # Basis per serving, values only in the per-100 g object: one printed column, its basis
    # is the doubt, so it is shown whatever basis the user picks.
    d = to_draft(ex(basis_detected="per_serving", serving_size_g=30))
    assert "basis_mismatch" in d.warnings and not d.derived_from_serving
    assert d.confirm == hints(
        col(shared=True, confirm_fields=["serving_size_g"]),
        col(printed=False, confirm_fields=["serving_size_g"], serving_required=True),
        basis=True,
    )


def test_basis_mismatch_without_a_serving_needs_one_only_for_per_serving():
    d = to_draft(ex(basis_detected="per_serving"))
    assert d.confirm == hints(
        col(shared=True),
        col(printed=False, confirm_fields=["serving_size_g"], serving_required=True),
        basis=True,
    )


def test_derived_from_serving_offers_only_the_serving_column():
    d = to_draft(
        ex(basis_detected="per_serving", per_100g=None, per_serving=n(), serving_size_g=30)
    )
    assert d.derived_from_serving and "basis_mismatch" not in d.warnings
    assert d.confirm == hints(None, col(confirm_fields=["serving_size_g"], serving_required=True))


def test_derived_with_basis_mismatch_shares_the_serving_column():
    # Basis per 100 g but only per-serving values: per_100g holds derived numbers, which are
    # never a printed column.
    d = to_draft(ex(basis_detected="per_100g", per_100g=None, per_serving=n(), serving_size_g=30))
    assert d.derived_from_serving and "basis_mismatch" in d.warnings
    assert d.confirm == hints(
        col(printed=False, confirm_fields=["serving_size_g"], serving_required=True),
        col(shared=True, confirm_fields=["serving_size_g"], serving_required=True),
        basis=True,
    )


def test_unit_unconfirmed_sodium_on_per_100g():
    d = to_draft(ex(per_100g=n(sodium_unit=None)))
    assert "unit_unconfirmed:per_100g.sodium_mg" in d.warnings
    # The unit picker confirms sodium: it is never a tick.
    assert d.confirm == hints(col(sodium_unit_required=True))


def test_unit_unconfirmed_sodium_on_the_other_column_still_needs_the_unit():
    # R19: a unit-less sodium on EITHER column, whichever column is saved.
    d = to_draft(ex(per_serving=ns(sodium_unit=None, sodium_mg=0.06), serving_size_g=30))
    assert "unit_unconfirmed:per_serving.sodium_mg" in d.warnings
    # Both columns are printed, so both are offered (R22); the basis is not in doubt.
    per_100g = col(confirm_fields=["serving_size_g"], sodium_unit_required=True)
    per_serving = col(
        confirm_fields=["serving_size_g"], sodium_unit_required=True, serving_required=True
    )
    assert d.confirm == hints(per_100g, per_serving)


def test_upper_bound_protein_on_per_100g():
    d = to_draft(ex(per_100g=n(protein_g=0.5), upper_bound_fields=["per_100g.protein_g"]))
    assert d.confirm == hints(col(confirm_fields=["protein_g"]))


def test_upper_bound_protein_on_the_other_column_is_asked_too():
    # R19.3: an upper bound on ANY column (the user may transcribe either).
    d = to_draft(
        ex(
            per_serving=ns(protein_g=0.5),
            serving_size_g=30,
            upper_bound_fields=["per_serving.protein_g", "per_100g.fiber_g"],
        )
    )
    fields = ["protein_g", "fiber_g", "serving_size_g"]
    assert d.confirm == hints(
        col(confirm_fields=fields), col(confirm_fields=fields, serving_required=True)
    )


def test_upper_bound_on_a_non_engine_doubt_field_is_not_asked():
    d = to_draft(ex(upper_bound_fields=["per_100g.sugars_g"]))
    assert d.confirm == CLEAN


def test_category_check_requires_a_category_choice():
    d = to_draft(ex(per_100_unit="ml"))
    assert "category_check" in d.warnings
    assert d.confirm == hints(col(), category=True)


def test_category_unknown_requires_a_category_choice():
    d = to_draft(ex(category_guess=None))
    assert "category_unknown" in d.warnings
    assert d.confirm == hints(col(), category=True)


def test_low_confidence_changes_no_hint():
    d = to_draft(ex(confidence=0.5))
    assert "low_confidence" in d.warnings and d.confirm == CLEAN


def test_implausible_value_changes_no_hint():
    d = to_draft(ex(per_100g=n(sugars_g=40)))  # more sugar than carbohydrate
    assert "implausible_value:sugars_g" in d.warnings and d.confirm == CLEAN


def test_devanagari_changes_no_hint():
    d = to_draft(ex(ingredients=["गेहूं का आटा", "चीनी"], allergen_statement="इसमें गेहूं है"))
    assert d.ingredients == ["गेहूं का आटा", "चीनी"] and d.confirm == CLEAN


def test_empty_draft_offers_both_unprinted_columns_and_requires_a_basis():
    d = to_draft(ex(per_100g=None))
    assert "per_100g_missing" in d.warnings
    assert d.confirm == hints(
        col(printed=False),
        col(printed=False, confirm_fields=["serving_size_g"], serving_required=True),
        basis=True,
    )


# --- the stored or posted confirm is never trusted ------------------------------------------


def test_confirm_is_recomputed_when_a_draft_is_loaded():
    d = to_draft(ex(per_100g=n(sodium_unit=None)))
    stale = d.model_dump(mode="json") | {"confirm": CLEAN.model_dump(mode="json")}
    assert ProductDraft.model_validate(stale).confirm == d.confirm


def test_confirm_is_in_the_dumped_draft():
    d = to_draft(ex())
    assert d.model_dump(mode="json")["confirm"] == CLEAN.model_dump(mode="json")


def test_positive_suppressed_is_gone():
    # R21(b): the deprecated alias was unreleased; engine_withheld is the only list.
    assert "positive_suppressed" not in ProductDraft.model_fields
    assert "positive_suppressed" not in to_draft(ex()).model_dump()


# --- the enforcement helpers (create_product calls these) -----------------------------------


def test_sodium_unit_unconfirmed_on_either_column():
    assert not sodium_unit_unconfirmed(to_draft(ex()))
    assert sodium_unit_unconfirmed(to_draft(ex(per_100g=n(sodium_unit=None))))
    d = to_draft(ex(per_serving=ns(sodium_unit=None), serving_size_g=30))
    assert sodium_unit_unconfirmed(d)


def test_withheld_fields_on_basis_mismatch_keep_only_per_field_doubts():
    d = to_draft(
        ex(
            basis_detected="unknown",
            per_100g=n(sodium_unit=None, protein_g=0.5),
            upper_bound_fields=["per_100g.protein_g"],
        )
    )
    assert d.engine_withheld == list(ENGINE_FIELDS)  # the engine sees nothing yet
    assert withheld_fields(d) == {"protein_g", "sodium_mg"}  # an explicit basis answers the rest


@pytest.mark.parametrize(
    ("kw", "basis", "expected"),
    [
        ({}, "per_100g", False),
        ({}, "per_serving", True),
        (
            {
                "basis_detected": "per_serving",
                "per_100g": None,
                "per_serving": n(),
                "serving_size_g": 30,
            },
            "per_100g",
            True,
        ),
    ],
)
def test_needs_serving_confirmation(kw, basis, expected):
    assert needs_serving_confirmation(to_draft(ex(**kw)), basis) is expected


def test_basis_and_category_required():
    assert not basis_required(to_draft(ex())) and not category_required(to_draft(ex()))
    assert basis_required(to_draft(ex(basis_detected="unknown")))
    assert category_required(to_draft(ex(category_guess=None)))


# --- P9 safety S5: a deterministic supplement hint ------------------------------------------


def test_clean_draft_has_no_category_suggestion():
    assert to_draft(ex()).confirm.category_suggestion is None


@pytest.mark.parametrize(
    "kw",
    [
        {"ingredients": ["whey protein concentrate", "cocoa", "sucralose"]},
        {"ingredients": ["soy protein isolate", "cocoa"]},
        # 55 g protein per 100 g (energy 400 so the Atwater check passes).
        {"per_100g": n(protein_g=55.0, energy_kcal=400.0, carbs_g=30.0, sugars_g=5.0,
                       fat_g=11.0)},
    ],
)  # fmt: skip
def test_whey_or_high_protein_suggests_supplement_and_asks_for_the_category(kw):
    d = to_draft(ex(**kw))
    assert d.confirm.category_suggestion == "supplement"
    assert d.confirm.category_required  # never preselect: the user picks
    assert d.category != "supplement"  # a hint only: the category is never set for the user
    assert d.confirm == confirm_hints(d)


def test_whey_powder_in_a_biscuit_suggests_nothing():
    d = to_draft(ex(ingredients=["wheat flour", "sugar", "whey powder", "milk solids"]))
    assert d.confirm.category_suggestion is None and not d.confirm.category_required


# --- R22: offer exactly the printed columns --------------------------------------------------


def test_per_serving_only_without_a_serving_offers_only_per_serving():
    # Never an empty per_100g column next to the printed per-serving one: the user could type
    # the per-serving numbers into per-100 g inputs.
    d = to_draft(ex(basis_detected="per_serving", per_100g=None, per_serving=n()))
    assert not d.derived_from_serving and "basis_mismatch" not in d.warnings
    assert d.confirm.columns.per_100g is None
    assert d.confirm.columns.per_serving is not None
    assert d.confirm.columns.per_serving.printed
    assert "serving_size_g" in d.confirm.columns.per_serving.confirm_fields
    assert d.confirm.basis_required is False


def test_no_printed_column_offers_both_and_requires_a_basis():
    d = to_draft(ex(per_100g=None, per_serving=None))
    assert d.confirm.basis_required is True
    assert d.confirm.columns.per_100g == col(printed=False)
    assert d.confirm.columns.per_serving == col(
        printed=False, confirm_fields=["serving_size_g"], serving_required=True
    )


def test_both_columns_printed_without_a_mismatch_offers_both_with_a_preselectable_basis():
    d = to_draft(ex(basis_detected="per_100g", per_serving=ns(), serving_size_g=30))
    assert "basis_mismatch" not in d.warnings and not d.derived_from_serving
    assert d.confirm.basis_required is False
    assert d.confirm.columns.per_100g is not None and d.confirm.columns.per_100g.printed
    assert d.confirm.columns.per_serving is not None and d.confirm.columns.per_serving.printed


@pytest.mark.parametrize("derived", [False, True])
@pytest.mark.parametrize("basis", ["per_100g", "per_serving"])
def test_serving_required_is_the_enforcement_helper(derived, basis):
    """R23(b): the hint is `needs_serving_confirmation` itself, per column."""
    if derived:
        d = to_draft(
            ex(basis_detected="per_serving", per_100g=None, per_serving=n(), serving_size_g=30)
        )
    else:
        d = to_draft(ex(basis_detected="unknown", per_serving=ns(), serving_size_g=30))
    column = getattr(d.confirm.columns, basis)
    if column is not None:
        assert column.serving_required is needs_serving_confirmation(d, basis)
    assert needs_serving_confirmation(d, basis) is (derived or basis == "per_serving")
