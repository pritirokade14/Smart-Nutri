"""Turn a model `NutritionExtraction` into a `ProductDraft` for the confirm screen (pure).

Health-critical rules:
- Never invent a value. A value not printed stays None. The only derivations are
  kJ -> kcal (only when kcal is not printed) and, when the label prints ONLY per-serving
  values AND a plausible serving size, per_100g = value x 100 / serving_size_g
  (`derived_from_serving = True`). Never assume a 100 g serving. Columns are never mixed.
- Printed units are converted in code (the model never converts): sodium printed in g
  -> mg (x 1000); trans fat printed in mg -> g (/ 1000). A sodium value with no printed
  unit is kept as mg but flagged `unit_unconfirmed:<path>` so the user confirms it.
- Implausible values are KEPT so the user can see and fix them, and flagged as
  `implausible_value:<field>`. Plausibility is the engine's own (`Product.sanitized()`),
  so a flagged draft field is exactly what the save endpoint rejects. Only non-finite
  numbers (NaN, inf) become None, since they cannot be shown or serialised.
- Salt and sodium are both kept (the engine uses the higher of the two).
- `added_sugars_g` and `trans_fat_g` are kept for display only; they are not engine inputs.
- A per-100 ml column or an ml serving means a drink: the category becomes beverage
  unless the model said water (the stricter per-100 ml drink thresholds apply).
- "<X" values are kept as X (an upper bound) and flagged `upper_bound:<path>`. An
  upper-bound protein or fibre is NOT evidence for a positive reason (e.g. "<0.1 g
  protein, <1 kcal" must not give good_protein_density): it is listed in
  `positive_suppressed`, and `engine_nutrients()` passes it to the engine as None.
- An unreadable ingredient list or allergen line caps confidence below the engine's
  min_extraction_confidence, so allergic members get `unknown`, never `ok`.
- Ingredients keep their script (Devanagari stays Devanagari); only whitespace is trimmed.

Warning codes, always in this order:
  implausible_value:<field>   draft fields outside the engine's bounds: engine nutrient
                              fields (engine order), added_sugars_g, trans_fat_g, serving_size_g
  per_100g_missing            no per-100 g value at all (and nothing derivable)
  energy_mismatch             kcal disagrees with 4p + 4c + 9f
  kcal_kj_mismatch            printed kcal disagrees with printed kJ / 4.184 (kcal is used)
  salt_sodium_mismatch        salt disagrees with sodium x 2.5 / 1000
  unit_unconfirmed:<path>     sodium printed without a unit on the column used; taken as mg
  low_confidence              (capped) confidence below min_extraction_confidence
  category_unknown            no category and no ml signal; "general" was used
  category_check              ml printed, so beverage replaced a non-drink or missing guess
  unreadable_field:<path>     printed but illegible (extraction field path, input order)
  upper_bound:<path>          printed as "<X"; X is kept (extraction field path, input order)
"""

from __future__ import annotations

import math
from typing import Literal

from pydantic import BaseModel

from app.features.products.schemas import NutrientsOut
from app.features.scans.schemas import NutrientsIn, NutritionExtraction
from app.scoring import Nutrients, Product, load_config
from app.scoring.models import CROSS_FIELD_TOLERANCE_G, MAX_GRAMS_PER_100

__all__ = ["DraftNutrients", "ProductDraft", "engine_nutrients", "to_draft"]

_CategoryName = Literal["general", "beverage", "water", "cheese", "fat"]
_CATEGORIES: tuple[_CategoryName, ...] = ("general", "beverage", "water", "cheese", "fat")
_Suppressible = Literal["protein_g", "fiber_g"]


class DraftNutrients(NutrientsOut):
    """Per 100 g / 100 ml for the confirm screen. None = not printed (never invented).

    The engine fields are M1's `NutrientsOut`. `added_sugars_g` and `trans_fat_g` are
    shown for the user to confirm but are NOT engine inputs (the engine's `Nutrients`
    has no such fields), so `ProductCreate.per_100g` (a `NutrientsOut`) drops them on save.
    """

    added_sugars_g: float | None
    trans_fat_g: float | None


class ProductDraft(BaseModel):
    """A normalised extraction awaiting user confirmation. Never saved as-is."""

    name: str | None
    brand: str | None
    category: _CategoryName
    per_100g: DraftNutrients
    serving_size_g: float | None  # as printed, g or ml
    ingredients: list[str]
    allergen_statement: str | None
    may_contain_statement: str | None
    claims: list[str]
    veg_mark: Literal["veg", "non_veg"] | None
    confidence: float  # clamped to [0, 1]; capped when allergen text is unreadable
    derived_from_serving: bool
    # Draft fields printed as "<X": shown, but never evidence for a positive reason.
    positive_suppressed: list[_Suppressible]
    warnings: list[str]  # codes, some as "<code>:<field or path>"


_KJ_PER_KCAL = 4.184  # unit conversion, as in products/off_mapping.py
# Data-quality heuristics from the plan (Task 3 rules 4 and 5), not health thresholds.
ENERGY_MISMATCH_RATIO = 0.15
ENERGY_MISMATCH_MIN_KCAL = 20.0
SALT_MISMATCH_RATIO = 0.2
# Ruling R10: an unreadable ingredient list or allergen line caps confidence here, below
# the engine's min_extraction_confidence (a test keeps it below), so allergens are unknown.
UNREADABLE_ALLERGEN_CONFIDENCE_CAP = 0.69
_ALLERGEN_PATHS = frozenset({"ingredients", "allergen_statement", "may_contain_statement"})
_DRINKS = frozenset({"beverage", "water"})
_SUPPRESSIBLE: tuple[_Suppressible, ...] = ("protein_g", "fiber_g")

_ENGINE_FIELDS = tuple(
    f for f in Nutrients.__dataclass_fields__ if f in DraftNutrients.model_fields
)
# Display-only fields: (field, the engine field it is part of).
_DISPLAY_ONLY = (("added_sugars_g", "sugars_g"), ("trans_fat_g", "fat_g"))


def _finite(value: float | None) -> float | None:
    return value if value is not None and math.isfinite(value) else None


def _text(value: str | None) -> str | None:
    return value.strip() or None if value is not None else None


def _texts(values: list[str]) -> list[str]:
    return [s for v in values if (s := v.strip())]


def _column(col: NutrientsIn | None) -> dict[str, float | None]:
    """One printed column as draft fields in draft units.

    kcal from kJ only when kcal is not printed; sodium printed in g -> mg; trans fat
    printed in mg -> g. A null unit means the field's own unit (mg sodium, g trans fat).
    """
    if col is None:
        return dict.fromkeys(DraftNutrients.model_fields)
    values = {f: getattr(col, f) for f in DraftNutrients.model_fields}
    if values["energy_kcal"] is None and col.energy_kj is not None:
        values["energy_kcal"] = col.energy_kj / _KJ_PER_KCAL
    if col.sodium_unit == "g" and col.sodium_mg is not None:
        values["sodium_mg"] = col.sodium_mg * 1000
    if col.trans_fat_unit == "mg" and col.trans_fat_g is not None:
        values["trans_fat_g"] = col.trans_fat_g / 1000
    return values


def _has_values(values: dict[str, float | None]) -> bool:
    return any(_finite(v) is not None for v in values.values())


def _serving_plausible(serving: float | None) -> bool:
    return "serving_size_g" not in Product(name="", serving_size_g=serving).sanitized()[1]


def _clamp_confidence(value: float) -> float:
    if not math.isfinite(value) or value < 0:
        return 0.0
    return min(value, 1.0)


def _energy_tolerance(kcal: float) -> float:
    return max(ENERGY_MISMATCH_RATIO * kcal, ENERGY_MISMATCH_MIN_KCAL)


def _per_100g(
    e: NutritionExtraction, serving_ok: bool
) -> tuple[dict[str, float | None], bool, Literal["per_100g", "per_serving"]]:
    """(per-100 g values, derived_from_serving, the printed column used).

    The ONLY derivation is the per-serving one; the two columns are never mixed.
    """
    values = _column(e.per_100g)
    if _has_values(values) or not serving_ok or e.serving_size_g is None:
        return values, False, "per_100g"
    per_serving = _column(e.per_serving)
    if not _has_values(per_serving):
        return values, False, "per_100g"
    size = e.serving_size_g
    derived = {k: None if v is None else v * 100 / size for k, v in per_serving.items()}
    return derived, True, "per_serving"


def _implausible_fields(
    values: dict[str, float | None], *, non_finite: set[str], serving_bad: bool
) -> list[str]:
    """Fields outside the engine's plausibility bounds, in a fixed order (values untouched)."""
    implausible = set(non_finite)
    # Engine plausibility (per field and cross-field), on the engine fields only.
    _, dropped = Product(
        name="", per_100g=Nutrients(**{f: values[f] for f in _ENGINE_FIELDS})
    ).sanitized()
    implausible |= set(dropped)
    for field, whole in _DISPLAY_ONLY:
        v, w = values[field], values[whole]
        if v is not None and (
            not 0 <= v <= MAX_GRAMS_PER_100 or (w is not None and v > w + CROSS_FIELD_TOLERANCE_G)
        ):
            implausible.add(field)
    if serving_bad:
        implausible.add("serving_size_g")
    order = (*_ENGINE_FIELDS, *(f for f, _ in _DISPLAY_ONLY), "serving_size_g")
    return [f for f in order if f in implausible]


def _consistency_warnings(
    values: dict[str, float | None], col: NutrientsIn | None, path: str
) -> list[str]:
    warnings: list[str] = []
    kcal, p, c, f = (values[k] for k in ("energy_kcal", "protein_g", "carbs_g", "fat_g"))
    if (
        kcal is not None
        and p is not None
        and c is not None
        and f is not None
        and abs(kcal - (4 * p + 4 * c + 9 * f)) > _energy_tolerance(kcal)
    ):
        warnings.append("energy_mismatch")

    # Both energies printed on the column used and they disagree (printed kcal wins).
    printed_kcal = _finite(col.energy_kcal) if col is not None else None
    printed_kj = _finite(col.energy_kj) if col is not None else None
    if (
        printed_kcal is not None
        and printed_kj is not None
        and abs(printed_kj / _KJ_PER_KCAL - printed_kcal) > _energy_tolerance(printed_kcal)
    ):
        warnings.append("kcal_kj_mismatch")

    salt, sodium = values["salt_g"], values["sodium_mg"]
    if salt is not None and sodium is not None:
        salt_from_sodium = Nutrients(sodium_mg=sodium).salt()  # the engine's conversion
        if salt_from_sodium is not None and abs(salt - salt_from_sodium) > (
            SALT_MISMATCH_RATIO * salt
        ):
            warnings.append("salt_sodium_mismatch")

    if col is not None and col.sodium_mg is not None and col.sodium_unit is None:
        warnings.append(f"unit_unconfirmed:{path}.sodium_mg")
    return warnings


def _confidence(e: NutritionExtraction) -> float:
    """Clamped to [0, 1] (NaN/inf -> 0), then capped when allergen-relevant text is unreadable."""
    confidence = _clamp_confidence(e.confidence)
    if _ALLERGEN_PATHS.intersection(e.unreadable_fields):
        confidence = min(confidence, UNREADABLE_ALLERGEN_CONFIDENCE_CAP)
    return confidence


def _category(e: NutritionExtraction) -> tuple[_CategoryName, list[str]]:
    guess = e.category_guess if e.category_guess in _CATEGORIES else None
    if "ml" in (e.per_100_unit, e.serving_size_unit):
        if guess == "beverage" or guess == "water":
            return guess, []
        return "beverage", ["category_check"]
    if guess is None:
        return "general", ["category_unknown"]
    return guess, []


def _positive_suppressed(
    e: NutritionExtraction, values: dict[str, float | None], path: str
) -> list[_Suppressible]:
    """Upper-bound protein/fibre on the column used: never evidence for a positive reason."""
    bounds = set(e.upper_bound_fields)
    return [f for f in _SUPPRESSIBLE if f"{path}.{f}" in bounds and values[f] is not None]


def _path_warnings(code: str, paths: list[str]) -> list[str]:
    return [f"{code}:{path}" for path in dict.fromkeys(_texts(paths))]


def engine_nutrients(draft: ProductDraft) -> Nutrients:
    """The engine-facing per-100 g values of a draft.

    Fields in `positive_suppressed` (an upper-bound protein or fibre, printed "<X") are
    passed as None, so they can never support a positive reason such as
    good_protein_density. Display-only fields (added sugars, trans fat) are not passed.
    """
    values = {f: getattr(draft.per_100g, f) for f in _ENGINE_FIELDS}
    for field in draft.positive_suppressed:
        values[field] = None
    return Nutrients(**values)


def to_draft(e: NutritionExtraction) -> ProductDraft:
    serving = e.serving_size_g
    serving_ok = serving is not None and _serving_plausible(serving)
    values, derived, path = _per_100g(e, serving_ok)
    source = e.per_serving if path == "per_serving" else e.per_100g

    # Non-finite numbers can't be shown or fixed in a form: blank them and flag them.
    non_finite = {k for k, v in values.items() if v is not None and _finite(v) is None}
    values = {k: _finite(v) for k, v in values.items()}

    warnings = [
        f"implausible_value:{f}"
        for f in _implausible_fields(
            values, non_finite=non_finite, serving_bad=serving is not None and not serving_ok
        )
    ]
    if not _has_values(values):
        warnings.append("per_100g_missing")
    warnings += _consistency_warnings(values, source, path)

    confidence = _confidence(e)
    if confidence < load_config().thresholds["min_extraction_confidence"]:
        warnings.append("low_confidence")

    category, category_warnings = _category(e)
    warnings += category_warnings
    warnings += _path_warnings("unreadable_field", e.unreadable_fields)
    warnings += _path_warnings("upper_bound", e.upper_bound_fields)

    return ProductDraft(
        name=_text(e.product_name),
        brand=_text(e.brand),
        category=category,
        per_100g=DraftNutrients(**values),
        serving_size_g=_finite(serving),
        ingredients=_texts(e.ingredients),
        allergen_statement=_text(e.allergen_statement),
        may_contain_statement=_text(e.may_contain_statement),
        claims=_texts(e.claims),
        veg_mark=e.veg_mark if e.veg_mark in ("veg", "non_veg") else None,
        confidence=confidence,
        derived_from_serving=derived,
        positive_suppressed=_positive_suppressed(e, values, path),
        warnings=warnings,
    )
