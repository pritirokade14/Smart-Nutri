"""Turn a model `NutritionExtraction` into a `ProductDraft` for the confirm screen (pure).

Health-critical rules:
- Never invent a value. A value not printed stays None. The only derivations are
  kJ -> kcal (only when kcal is not printed) and, when the per-100 column has no engine
  value AND the label prints per-serving values AND a plausible serving size,
  per_100g = value x 100 / serving_size_g (`derived_from_serving = True`). Never assume a
  100 g serving. Columns are never mixed. Derived values are NOT rounded (clients round
  for display only; the engine and the save path get the exact quotient).
- "Has values" (for derivation, `per_100g_missing` and the basis check) means at least one
  ENGINE field (`ENGINE_FIELDS`). A lone display-only value (trans fat 0, added sugars 0)
  never counts.
- An unreadable nutrient (any `per_100g.*` / `per_serving.*` path in `unreadable_fields`)
  is never trusted: it is cleared to None before anything else (unit conversion, kJ ->
  kcal, derivation), so a per-serving path is cleared BEFORE derivation. An unreadable
  `serving_size_g` is cleared too, so nothing is derived from it.
- Printed units are converted in code (the model never converts): sodium printed in g
  -> mg (x 1000, `sodium_to_mg`); trans fat printed in mg -> g (/ 1000). A sodium value
  with no printed unit is kept as the printed number for display, flagged
  `unit_unconfirmed:<path>` on each printed column, and withheld when it is on the column
  used for `per_100g`.
- `per_serving` is the printed per-serving column in draft units (after unreadable-
  clearing, kJ -> kcal and the unit conversions above), so clients can show it and the user
  can save it with basis per_serving (the SERVER converts it: `per_100g_from_serving`,
  the same helper the derivation uses). None when no per-serving value is printed.
- Implausible values are KEPT so the user can see and fix them, and flagged as
  `implausible_value:<field>`. Plausibility is the engine's own (`Product.sanitized()`),
  so a flagged draft field is exactly what the save endpoint rejects. Only non-finite
  numbers (NaN, inf) become None, since they cannot be shown or serialised.
- Salt and sodium are both kept (the engine uses the higher of the two).
- `added_sugars_g` and `trans_fat_g` are kept for display only; they are not engine inputs.
- A per-100 ml column or an ml serving means a drink: the category becomes beverage
  unless the model said water or beverage, or fat or cheese (an oil printed per 100 ml
  stays "fat"); every case except beverage/water adds `category_check`.
- "<X" values are kept as X (an upper bound) and flagged `upper_bound:<path>`.
- An unreadable ingredient list or allergen line caps confidence below the engine's
  min_extraction_confidence, so allergic members get `unknown`, never `ok`.
- Ingredients keep their script (Devanagari stays Devanagari); only whitespace is trimmed.

`engine_withheld` (ruling R13): engine fields shown on the confirm screen that the engine
must not see until the user confirms them on the confirm screen (save:
`ProductCreate.confirmed_fields`, ruling R14). `engine_nutrients()` passes them as None.
Listed in `ENGINE_FIELDS` order, without duplicates:
- every engine field, when `basis_mismatch` (the printed basis is in doubt);
- `protein_g` / `fiber_g` printed as "<X" on the column used (an upper bound is never
  evidence for a positive reason such as good_protein_density);
- `sodium_mg`, when `unit_unconfirmed` (sodium printed without a unit on the column used);
- every printed field a failed arithmetic check involves (label accuracy v2), using the map
  `confirm_rules.CHECK_FIELDS` shared with the confirm hints: `energy_mismatch` -> energy,
  protein, carbs, fat, fibre; `kcal_kj_mismatch` -> energy; `salt_sodium_mismatch` -> salt,
  sodium; `fat_parts_mismatch` -> fat, sat fat; `decimal_shift:<path>` and
  `column_mismatch:<field>` -> that field.

Arithmetic checks (on the column used; tolerances are data-quality constants, not health
thresholds, and are tested in tests/unit/scans/test_consistency_checks.py):
- Atwater: |kcal - E| <= max(ENERGY_MISMATCH_RATIO x kcal, ENERGY_MISMATCH_MIN_KCAL), where E
  may be anywhere in 4p + 4c + 9f +/- FIBRE_KCAL_PER_G x fibre (carbs with or without fibre;
  fibre at 2 kcal/g), so honest high-fibre labels are not flagged.
- kcal vs kJ: |kJ / 4.184 - kcal| within the same energy tolerance.
- salt vs sodium: |salt - sodium x 2.5 / 1000| <= SALT_MISMATCH_RATIO x salt. A unit-less
  sodium passes when either reading (mg or g) does (its unit is asked anyway).
- fat parts: sat + trans <= fat + CROSS_FIELD_TOLERANCE_G (sugars <= carbs and sat <= fat are
  the engine's own `implausible_value` checks; added <= total sugars and trans <= fat are the
  display-only ones).
- decimal-shift probe: when x10 or /10 (DECIMAL_SHIFT_FACTORS) on ONE field makes a failed
  Atwater check pass, that field is named; salt and sodium are named together (x10 on one is
  /10 on the other).

`confirm` (ruling R21): what the confirm screen must ask (basis, category, ticks, sodium unit)
per offered basis. Computed from the draft's own fields by
`app.features.products.confirm_rules.confirm_hints`, the same helpers that enforce the save,
every time a draft is built or loaded (a stored or posted `confirm` is ignored).

Warning codes, always in this order:
  implausible_value:<field>   draft fields outside the engine's bounds: engine nutrient
                              fields (engine order), added_sugars_g, trans_fat_g, serving_size_g
  per_100g_missing            no per-100 g engine value at all (and nothing derivable)
  basis_mismatch              basis_detected disagrees with the columns filled: per_serving
                              but only per_100g has values, per_100g but only per_serving
                              has values, or unknown with any values. All engine fields
                              are withheld until the user picks the basis.
  per_serving_ignored         per-serving values were printed but not used (the per-100 g
                              column was used and lacks those fields, or nothing could be
                              derived); the columns are never mixed
  energy_mismatch             kcal disagrees with 4p + 4c + 9f (+/- 2 kcal/g fibre)
  kcal_kj_mismatch            printed kcal disagrees with printed kJ / 4.184 (kcal is used)
  salt_sodium_mismatch        salt disagrees with sodium x 2.5 / 1000
  fat_parts_mismatch          sat fat + trans fat is more than total fat
  decimal_shift:<path>        a x10 or /10 slip on this printed cell would explain a failed
                              check (draft field order)
  column_mismatch:<field>     both columns and a plausible serving are printed, and this
                              engine field's per-serving value is not per_100g x serving / 100
                              within max(10%, its rounding unit); never on a derived draft;
                              upper bounds and unit-less sodium are skipped (engine order)
  unit_unconfirmed:<path>     sodium printed without a unit, per printed column
                              (per_100g first, then per_serving); the printed number is shown;
                              withheld from the engine when on the column used
  low_confidence              (capped) confidence below min_extraction_confidence
  category_unknown            no category and no ml signal; "general" was used
  category_check              ml printed and the guess was not beverage/water (beverage was
                              used, or the fat/cheese guess was kept)
  unreadable_field:<path>     printed but illegible (extraction field path, input order);
                              a nutrient or serving-size value there is cleared to None
  upper_bound:<path>          printed as "<X"; X is kept (extraction field path, input order)
"""

from __future__ import annotations

import math
from collections.abc import Callable, Mapping
from typing import Literal, get_args

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.features.products.confirm_rules import (
    UPPER_BOUND_FIELDS,
    DraftConfirm,
    checked_fields,
    confirm_hints,
    placeholder_confirm,
)
from app.features.products.schemas import NutrientsOut
from app.features.scans.schemas import NUTRIENT_FIELDS, NutrientsIn, NutritionExtraction
from app.scoring import Nutrients, Product, load_config
from app.scoring.models import CROSS_FIELD_TOLERANCE_G, MAX_GRAMS_PER_100

__all__ = [
    "ENGINE_FIELDS",
    "DraftNutrients",
    "EngineField",
    "ProductDraft",
    "engine_nutrients",
    "implausible_fields",
    "per_100g_from_serving",
    "sodium_to_mg",
    "to_draft",
]

_CategoryName = Literal["general", "beverage", "water", "cheese", "fat"]
_CATEGORIES: tuple[_CategoryName, ...] = ("general", "beverage", "water", "cheese", "fat")
# The draft fields the engine reads (`Nutrients` fields that the draft has), in engine
# order. A test keeps this equal to the engine's own field list.
EngineField = Literal[
    "energy_kcal",
    "protein_g",
    "carbs_g",
    "sugars_g",
    "fat_g",
    "sat_fat_g",
    "fiber_g",
    "salt_g",
    "sodium_mg",
]
ENGINE_FIELDS: tuple[EngineField, ...] = get_args(EngineField)
# Every warning code `to_draft` can emit (the part before ":"), in warning order. Each needs
# `warning.<code>` in packages/i18n (tests/unit/scans/test_warning_codes_i18n.py).
WARNING_CODES: tuple[str, ...] = (
    "implausible_value",
    "per_100g_missing",
    "basis_mismatch",
    "per_serving_ignored",
    "energy_mismatch",
    "kcal_kj_mismatch",
    "salt_sodium_mismatch",
    "fat_parts_mismatch",
    "decimal_shift",
    "column_mismatch",
    "unit_unconfirmed",
    "low_confidence",
    "category_unknown",
    "category_check",
    "unreadable_field",
    "upper_bound",
)


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

    # `per_serving` has a default only so drafts stored before it existed still load; the
    # API always sends it, so the contract marks it required.
    model_config = ConfigDict(json_schema_serialization_defaults_required=True)

    name: str | None
    brand: str | None
    category: _CategoryName
    per_100g: DraftNutrients
    # The printed per-serving column in draft units (after unreadable-clearing, kJ -> kcal,
    # sodium g -> mg; a unit-less sodium is the printed number, see `unit_unconfirmed`).
    # None when no per-serving value is printed. Save it with basis per_serving; the server
    # converts it to per 100 g.
    per_serving: DraftNutrients | None = None
    serving_size_g: float | None  # as printed, g or ml
    ingredients: list[str]
    allergen_statement: str | None
    may_contain_statement: str | None
    claims: list[str]
    veg_mark: Literal["veg", "non_veg"] | None
    confidence: float  # clamped to [0, 1]; capped when allergen text is unreadable
    derived_from_serving: bool
    # Shown, but the engine must not see them until the user confirms them on the confirm
    # screen (save: ProductCreate.confirmed_fields, ruling R14). ENGINE_FIELDS order.
    engine_withheld: list[EngineField]
    warnings: list[str]  # codes, some as "<code>:<field or path>"
    # R21: what the confirm screen must ask. Always recomputed from the fields above by
    # the validator (the save path's own helpers), so it is never stale or client-supplied.
    confirm: DraftConfirm = Field(default_factory=placeholder_confirm)

    @model_validator(mode="after")
    def _derive(self) -> ProductDraft:
        """`engine_withheld` deduplicated in engine order; `confirm` computed from the draft."""
        withheld = set(self.engine_withheld)
        self.engine_withheld = [f for f in ENGINE_FIELDS if f in withheld]
        self.confirm = confirm_hints(self)
        return self


_KJ_PER_KCAL = 4.184  # unit conversion, as in products/off_mapping.py
# Data-quality heuristics from the plan (Task 3 rules 4 and 5), not health thresholds.
ENERGY_MISMATCH_RATIO = 0.15
ENERGY_MISMATCH_MIN_KCAL = 20.0
SALT_MISMATCH_RATIO = 0.2
# Label accuracy v2 (data-quality constants, not health thresholds). Fibre counts 2 kcal/g
# (EU Regulation 1169/2011 Annex XIV). A decimal slip is one field off by x10 or /10.
FIBRE_KCAL_PER_G = 2.0
DECIMAL_SHIFT_FACTORS = (10.0, 0.1)
# Column ratio check: per_serving ~= per_100g x serving / 100 within
# max(COLUMN_RATIO_TOLERANCE x the larger value, the field's rounding unit). The units allow
# for labels that round each column on its own (whole kcal or 5 kcal, sodium to 10 mg, grams
# to whole numbers or "0" under 0.5 g), so small values are only checked loosely.
COLUMN_RATIO_TOLERANCE = 0.10
COLUMN_ROUNDING_UNITS: dict[str, float] = {"energy_kcal": 5.0, "sodium_mg": 10.0, "default": 0.5}
# Ruling R10: an unreadable ingredient list or allergen line caps confidence here, below
# the engine's min_extraction_confidence (a test keeps it below), so allergens are unknown.
UNREADABLE_ALLERGEN_CONFIDENCE_CAP = 0.69
_ALLERGEN_PATHS = frozenset({"ingredients", "allergen_statement", "may_contain_statement"})
_Column = Literal["per_100g", "per_serving"]

# Display-only fields: (field, the engine field it is part of).
_DISPLAY_ONLY = (("added_sugars_g", "sugars_g"), ("trans_fat_g", "fat_g"))


def sodium_to_mg(value: float | None, unit: Literal["mg", "g"] | None) -> float | None:
    """Sodium in mg: x 1000 when the unit is g; a null unit means mg (the field's own unit)."""
    if value is None:
        return None
    return value * 1000 if unit == "g" else value


def per_100g_from_serving(value: float | None, serving_size_g: float) -> float | None:
    """value x 100 / serving_size_g, exact (never rounded). The caller checks the serving."""
    return None if value is None else value * 100 / serving_size_g


def _finite(value: float | None) -> float | None:
    return value if value is not None and math.isfinite(value) else None


def _text(value: str | None) -> str | None:
    return value.strip() or None if value is not None else None


def _texts(values: list[str]) -> list[str]:
    return [s for v in values if (s := v.strip())]


def _readable(col: NutrientsIn | None, path: _Column, unreadable: set[str]) -> NutrientsIn | None:
    """The printed column with every unreadable nutrient cleared to None (input untouched)."""
    if col is None:
        return None
    cleared = {f: None for f in NUTRIENT_FIELDS if f"{path}.{f}" in unreadable}
    return col.model_copy(update=cleared) if cleared else col


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
    values["sodium_mg"] = sodium_to_mg(col.sodium_mg, col.sodium_unit)
    if col.trans_fat_unit == "mg" and col.trans_fat_g is not None:
        values["trans_fat_g"] = col.trans_fat_g / 1000
    return values


def _has_engine_values(values: dict[str, float | None]) -> bool:
    return any(_finite(values[f]) is not None for f in ENGINE_FIELDS)


def _serving_plausible(serving: float | None) -> bool:
    return "serving_size_g" not in Product(name="", serving_size_g=serving).sanitized()[1]


def _clamp_confidence(value: float) -> float:
    if not math.isfinite(value) or value < 0:
        return 0.0
    return min(value, 1.0)


def _energy_tolerance(kcal: float) -> float:
    return max(ENERGY_MISMATCH_RATIO * kcal, ENERGY_MISMATCH_MIN_KCAL)


def _per_100g(
    per_100: dict[str, float | None],
    per_serving: dict[str, float | None],
    serving: float | None,
    serving_ok: bool,
) -> tuple[dict[str, float | None], bool, _Column]:
    """(per-100 g values, derived_from_serving, the printed column used).

    The ONLY derivation is the per-serving one; the two columns are never mixed. Derived
    values are exact quotients (not rounded).
    """
    if _has_engine_values(per_100) or not serving_ok or serving is None:
        return per_100, False, "per_100g"
    if not _has_engine_values(per_serving):
        return per_100, False, "per_100g"
    derived = {k: per_100g_from_serving(v, serving) for k, v in per_serving.items()}
    return derived, True, "per_serving"


def _basis_mismatch(
    basis: str, per_100: dict[str, float | None], per_serving: dict[str, float | None]
) -> bool:
    """The detected basis disagrees with the columns that hold engine values."""
    p100, ps = _has_engine_values(per_100), _has_engine_values(per_serving)
    return (
        (basis == "per_serving" and p100 and not ps)
        or (basis == "per_100g" and ps and not p100)
        or (basis == "unknown" and (p100 or ps))
    )


def _per_serving_ignored(
    values: dict[str, float | None], per_serving: dict[str, float | None], path: _Column
) -> bool:
    """Per-serving values printed but absent from the draft (columns are never mixed)."""
    return path == "per_100g" and any(
        _finite(v) is not None and values[k] is None for k, v in per_serving.items()
    )


def _implausible_fields(
    values: Mapping[str, float | None], *, non_finite: set[str], serving_bad: bool
) -> list[str]:
    """Fields outside the engine's plausibility bounds, in a fixed order (values untouched)."""
    implausible = set(non_finite)
    # Engine plausibility (per field and cross-field), on the engine fields only.
    _, dropped = Product(
        name="", per_100g=Nutrients(**{f: values.get(f) for f in ENGINE_FIELDS})
    ).sanitized()
    implausible |= set(dropped)
    for field, whole in _DISPLAY_ONLY:
        v, w = values.get(field), values.get(whole)
        if v is not None and (
            not 0 <= v <= MAX_GRAMS_PER_100 or (w is not None and v > w + CROSS_FIELD_TOLERANCE_G)
        ):
            implausible.add(field)
    if serving_bad:
        implausible.add("serving_size_g")
    order = (*ENGINE_FIELDS, *(f for f, _ in _DISPLAY_ONLY), "serving_size_g")
    return [f for f in order if f in implausible]


def implausible_fields(
    values: Mapping[str, float | None], *, serving_size_g: float | None
) -> list[str]:
    """Per-100 g draft fields (missing keys = None) and the serving size that fail the
    engine's plausibility rules, in the draft's warning order. The save endpoint uses this
    so it rejects exactly what the draft flags as `implausible_value`."""
    serving_bad = serving_size_g is not None and not _serving_plausible(serving_size_g)
    return _implausible_fields(values, non_finite=set(), serving_bad=serving_bad)


def _sodium_unit_unconfirmed(col: NutrientsIn | None) -> bool:
    return col is not None and col.sodium_mg is not None and col.sodium_unit is None


_ATWATER_FIELDS = ("energy_kcal", "protein_g", "carbs_g", "fat_g", "fiber_g")


def _atwater_ok(v: Mapping[str, float | None]) -> bool:
    """kcal agrees with 4p + 4c + 9f within `_energy_tolerance`, the expected value widened by
    `FIBRE_KCAL_PER_G` x fibre either way: carbs that include fibre give 4p + 4(c - fib) + 9f
    + 2 fib (= base - 2 fib); carbs that exclude it give base + 2 fib. Callers check that kcal,
    p, c and f are printed; a missing fibre gives no widening."""
    kcal, p, c, f = (v[k] or 0.0 for k in _ATWATER_FIELDS[:4])
    base = 4 * p + 4 * c + 9 * f
    widen = FIBRE_KCAL_PER_G * (v["fiber_g"] or 0.0)
    gap = max(base - widen - kcal, kcal - base - widen, 0.0)
    return gap <= _energy_tolerance(kcal)


def _salt_ok(salt: float, sodium_mg: float) -> bool:
    salt_from_sodium = Nutrients(sodium_mg=sodium_mg).salt()  # the engine's conversion
    return salt_from_sodium is None or abs(salt - salt_from_sodium) <= SALT_MISMATCH_RATIO * salt


def _salt_sodium_ok(salt: float, sodium: float, *, unit_unconfirmed: bool) -> bool:
    """Salt agrees with sodium. A unit-less sodium agrees when either reading (mg or g) does:
    its unit is asked anyway, and salt cannot be blamed for the missing unit."""
    readings = (sodium, sodium * 1000) if unit_unconfirmed else (sodium,)
    return any(_salt_ok(salt, mg) for mg in readings)


def _decimal_shift_suspects(
    values: Mapping[str, float | None],
    fields: tuple[str, ...],
    passes: Callable[[Mapping[str, float | None]], bool],
) -> list[str]:
    """Printed fields where x10 or /10 on that field alone makes a failed check pass."""
    return [
        f
        for f in fields
        if values[f] is not None
        and any(passes({**values, f: values[f] * k}) for k in DECIMAL_SHIFT_FACTORS)
    ]


def _consistency_warnings(
    values: dict[str, float | None],
    col: NutrientsIn | None,
    path: _Column,
    *,
    sodium_unit_unconfirmed: bool,
) -> list[str]:
    """Arithmetic checks on the column used (label accuracy v2 item 1). Each failed check
    withholds the fields it involves (`confirm_rules.CHECK_FIELDS`); `decimal_shift:<path>`
    names a field that a x10 or /10 slip would explain."""
    warnings: list[str] = []
    suspects: list[str] = []
    if all(values[k] is not None for k in _ATWATER_FIELDS[:4]) and not _atwater_ok(values):
        warnings.append("energy_mismatch")
        found = _decimal_shift_suspects(values, _ATWATER_FIELDS, _atwater_ok)
        if len(found) == 1:  # name a field only when exactly one explains the gap
            suspects += found

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

        def salt_passes(v: Mapping[str, float | None]) -> bool:
            s, na = v["salt_g"] or 0.0, v["sodium_mg"] or 0.0  # both printed here
            return _salt_sodium_ok(s, na, unit_unconfirmed=sodium_unit_unconfirmed)

        if not salt_passes(values):
            warnings.append("salt_sodium_mismatch")
            # x10 on salt and /10 on sodium are the same fix, so both (or neither) are named.
            suspects += _decimal_shift_suspects(values, ("salt_g", "sodium_mg"), salt_passes)

    fat, sat, trans = values["fat_g"], values["sat_fat_g"], values["trans_fat_g"]
    if (
        fat is not None
        and sat is not None
        and trans is not None
        and sat + trans > fat + CROSS_FIELD_TOLERANCE_G
    ):
        warnings.append("fat_parts_mismatch")

    warnings += [f"decimal_shift:{path}.{f}" for f in DraftNutrients.model_fields if f in suspects]
    return warnings


def _column_ratio_mismatches(
    per_100: Mapping[str, float | None],
    per_serving: Mapping[str, float | None],
    serving: float,
    *,
    skip: set[str],
) -> list[str]:
    """Engine fields (engine order) printed on both columns that disagree once the serving
    size is applied (label accuracy v2 item 2). `skip`: fields not comparable (an upper bound
    on either column, a unit-less sodium)."""
    out: list[str] = []
    for f in ENGINE_FIELDS:
        a, b = _finite(per_100.get(f)), _finite(per_serving.get(f))
        if f in skip or a is None or b is None:
            continue
        expected = a * serving / 100
        unit = COLUMN_ROUNDING_UNITS.get(f, COLUMN_ROUNDING_UNITS["default"])
        if abs(b - expected) > max(COLUMN_RATIO_TOLERANCE * max(abs(b), abs(expected)), unit):
            out.append(f)
    return out


def _ratio_skip(
    e: NutritionExtraction, per_100_col: NutrientsIn | None, per_serving_col: NutrientsIn | None
) -> set[str]:
    bounds = {p.split(".", 1)[1] for p in e.upper_bound_fields if "." in p}
    if _sodium_unit_unconfirmed(per_100_col) or _sodium_unit_unconfirmed(per_serving_col):
        bounds.add("sodium_mg")
    return bounds


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
        if guess == "fat" or guess == "cheese":  # e.g. an oil printed per 100 ml
            return guess, ["category_check"]
        return "beverage", ["category_check"]
    if guess is None:
        return "general", ["category_unknown"]
    return guess, []


def _engine_withheld(
    e: NutritionExtraction,
    values: dict[str, float | None],
    source: NutrientsIn | None,
    path: _Column,
    warnings: list[str],
    *,
    basis_mismatch: bool,
) -> list[EngineField]:
    """Engine fields the engine must not see until the user confirms them (ENGINE_FIELDS order)."""
    if basis_mismatch:
        return list(ENGINE_FIELDS)
    withheld: set[str] = set()
    bounds = set(e.upper_bound_fields)
    # An upper-bound protein/fibre on the column used is never evidence for a positive reason.
    withheld |= {f for f in UPPER_BOUND_FIELDS if f"{path}.{f}" in bounds and values[f] is not None}
    if _sodium_unit_unconfirmed(source):
        withheld.add("sodium_mg")
    # Fields a failed arithmetic check involves (the same map the confirm hints use).
    withheld |= {f for f in checked_fields(warnings) if values.get(f) is not None}
    return [f for f in ENGINE_FIELDS if f in withheld]


def _shown_column(values: dict[str, float | None]) -> DraftNutrients | None:
    """A printed column for display (non-finite -> None), or None when nothing is printed."""
    shown = {k: _finite(v) for k, v in values.items()}
    return DraftNutrients(**shown) if any(v is not None for v in shown.values()) else None


def _path_warnings(code: str, paths: list[str]) -> list[str]:
    return [f"{code}:{path}" for path in dict.fromkeys(_texts(paths))]


def engine_nutrients(draft: ProductDraft) -> Nutrients:
    """The engine-facing per-100 g values of a draft.

    Fields in `engine_withheld` are passed as None: the engine must not see them until the user confirms them. Display-only
    fields (added sugars, trans fat) are not passed.
    """
    withheld = set(draft.engine_withheld)
    return Nutrients(
        **{f: None if f in withheld else getattr(draft.per_100g, f) for f in ENGINE_FIELDS}
    )


def to_draft(e: NutritionExtraction) -> ProductDraft:
    unreadable = set(e.unreadable_fields)
    serving = None if "serving_size_g" in unreadable else e.serving_size_g
    serving_ok = serving is not None and _serving_plausible(serving)

    # Unreadable nutrients are cleared first, so nothing below (units, kJ, derivation,
    # basis and consistency checks) ever sees them.
    per_100_col = _readable(e.per_100g, "per_100g", unreadable)
    per_serving_col = _readable(e.per_serving, "per_serving", unreadable)
    per_100, per_serving = _column(per_100_col), _column(per_serving_col)
    values, derived, path = _per_100g(per_100, per_serving, serving, serving_ok)
    source = per_serving_col if path == "per_serving" else per_100_col

    # Non-finite numbers can't be shown or fixed in a form: blank them and flag them.
    non_finite = {k for k, v in values.items() if v is not None and _finite(v) is None}
    values = {k: _finite(v) for k, v in values.items()}

    warnings = [
        f"implausible_value:{f}"
        for f in _implausible_fields(
            values, non_finite=non_finite, serving_bad=serving is not None and not serving_ok
        )
    ]
    if not _has_engine_values(values):
        warnings.append("per_100g_missing")
    basis_mismatch = _basis_mismatch(e.basis_detected, per_100, per_serving)
    if basis_mismatch:
        warnings.append("basis_mismatch")
    if _per_serving_ignored(values, per_serving, path):
        warnings.append("per_serving_ignored")
    warnings += _consistency_warnings(
        values, source, path, sodium_unit_unconfirmed=_sodium_unit_unconfirmed(source)
    )
    # Both printed columns and a plausible serving: they must agree (never on a derived draft,
    # whose per-100 g column was computed from the per-serving one).
    if path == "per_100g" and serving_ok and serving is not None:
        skip = _ratio_skip(e, per_100_col, per_serving_col)
        warnings += [
            f"column_mismatch:{f}"
            for f in _column_ratio_mismatches(per_100, per_serving, serving, skip=skip)
        ]
    # Each printed column with a unit-less sodium (both can be saved, R17).
    for column, col in (("per_100g", per_100_col), ("per_serving", per_serving_col)):
        if _sodium_unit_unconfirmed(col):
            warnings.append(f"unit_unconfirmed:{column}.sodium_mg")

    confidence = _confidence(e)
    if confidence < load_config().thresholds["min_extraction_confidence"]:
        warnings.append("low_confidence")

    category, category_warnings = _category(e)
    warnings += category_warnings
    warnings += _path_warnings("unreadable_field", e.unreadable_fields)
    warnings += _path_warnings("upper_bound", e.upper_bound_fields)

    withheld = _engine_withheld(e, values, source, path, warnings, basis_mismatch=basis_mismatch)
    return ProductDraft(
        name=_text(e.product_name),
        brand=_text(e.brand),
        category=category,
        per_100g=DraftNutrients(**values),
        per_serving=_shown_column(per_serving),
        serving_size_g=_finite(serving),
        ingredients=_texts(e.ingredients),
        allergen_statement=_text(e.allergen_statement),
        may_contain_statement=_text(e.may_contain_statement),
        claims=_texts(e.claims),
        veg_mark=e.veg_mark if e.veg_mark in ("veg", "non_veg") else None,
        confidence=confidence,
        derived_from_serving=derived,
        engine_withheld=withheld,
        warnings=warnings,
    )
