"""Deterministic parsing of verbatim label cells (label accuracy v2, prompt extraction_v2).

With extraction_v2 the vision model copies each nutrition cell as printed ("<0.5 g", "Nil",
"१२.५ ग्रा") instead of turning it into a number. This module does the reading, in code:

- digits of any script (Devanagari and Marathi ०-९ included) become ASCII digits;
- "12,5" is 12.5; "1,883.5" is 1883.5; "1,883" alone is ambiguous (1.883 or 1883), so it
  is unreadable, never guessed;
- "<X", "≤X" and "less than X" are X with qualifier `upper_bound`;
- "Nil" and "शून्य" are 0 (qualifier `nil`); a printed 0 is just 0;
- a bracketed percentage next to the value ("12.5 g (18%)") is dropped (it is %RDA);
- units: g, mg, kcal, kJ and ml, in English, Hindi and Marathi spellings;
- anything else ("Traces", "-", "N/A", ranges, "~5", ">5", a bare "12%", two numbers in one
  cell, an unknown unit) is `unreadable`: no value.

`to_extraction` turns a `NutritionExtractionV2` into the `NutritionExtraction` the normaliser
reads (`to_draft`), so every v1 safety rule applies unchanged. Units are checked against the
row: a unit that does not belong to the row (a kJ value in the kcal row, protein in mg, a cell
unit that disagrees with the row's unit label) makes the cell unreadable. Upper bounds,
`sodium_unit` and `trans_fat_unit` are computed here, never reported by the model.

Pure: no I/O.
"""

from __future__ import annotations

import re
import unicodedata
from typing import Any, Literal, NamedTuple

from pydantic import BaseModel

from app.features.scans.schemas import (
    NUTRIENT_FIELDS,
    CellIn,
    NutrientCellsIn,
    NutrientsIn,
    NutritionExtraction,
    NutritionExtractionV2,
)

__all__ = [
    "EXTRACTION_SCHEMAS",
    "Cell",
    "Qualifier",
    "Unit",
    "extraction_schema",
    "parse_cell",
    "parse_unit",
    "to_extraction",
]

Unit = Literal["g", "mg", "kcal", "kJ", "ml"]
Qualifier = Literal["exact", "upper_bound", "nil", "unreadable", "absent"]

# The schema the model answers with, per prompt version (the cache key includes the version).
EXTRACTION_SCHEMAS: dict[str, type[BaseModel]] = {
    "extraction_v1": NutritionExtraction,
    "extraction_v2": NutritionExtractionV2,
}


class Cell(NamedTuple):
    value: float | None
    unit: Unit | None
    qualifier: Qualifier


_ABSENT = Cell(None, None, "absent")
_UNREADABLE = Cell(None, None, "unreadable")

# Unit spellings, compared after NFC, lower-casing and removing spaces, dots and brackets.
_UNITS: dict[str, Unit] = {
    **dict.fromkeys(("g", "gm", "gms", "gr", "gram", "grams", "gramme", "grammes"), "g"),
    **dict.fromkeys(("ग्रा", "ग्राम", "ग्रॅ", "ग्रॅम", "ग्रम"), "g"),
    **dict.fromkeys(("mg", "mgs", "milligram", "milligrams"), "mg"),
    **dict.fromkeys(("मिग्रा", "मिलीग्राम", "मिलिग्राम", "मिग्रॅ", "मिलीग्रॅम", "मिलिग्रॅम"), "mg"),
    **dict.fromkeys(("kcal", "kcals", "kilocalorie", "kilocalories"), "kcal"),
    **dict.fromkeys(
        ("किलोकैलोरी", "किकै", "किलोकॅलरी", "किकॅलरी", "किकॅ", "किलोकेलरी", "किकेलरी"), "kcal"
    ),
    **dict.fromkeys(("kj", "kilojoule", "kilojoules", "किलोजूल", "किलोज्यूल", "किज्यू"), "kJ"),
    **dict.fromkeys(("ml", "millilitre", "milliliter", "मिली", "मिलीलीटर", "मिलिलिटर"), "ml"),
}
_NIL = frozenset({"nil", "शून्य", "निल", "नील"})
_UPPER = re.compile(r"^(?:<|≤|less\s*than|lessthan)\s*")
_RDA = re.compile(r"\(\s*[\d.,]+\s*%\s*\)")
_NUMBER_UNIT = re.compile(r"(?P<num>\d[\d.,]*)\s*(?P<unit>[^\d]*)")
# Invisible characters that never change a value (zero-width space/joiners, BOM).
_INVISIBLE = dict.fromkeys((0x200B, 0x200C, 0x200D, 0xFEFF))


def _ascii_digits(text: str) -> str:
    """Digits of any script (Devanagari ०-९, ...) as ASCII digits; other characters kept."""
    return "".join(
        str(unicodedata.decimal(ch)) if not ch.isascii() and unicodedata.decimal(ch, None) is not None
        else ch
        for ch in text
    )  # fmt: skip


def _clean(text: str) -> str:
    text = unicodedata.normalize("NFC", text).translate(_INVISIBLE)
    return " ".join(_ascii_digits(text).split())


def parse_unit(text: str | None) -> Unit | None:
    """A unit spelling (any case, dots, spaces or brackets) -> its unit; None if unknown."""
    if text is None:
        return None
    key = re.sub(r"[\s.()\[\]]", "", unicodedata.normalize("NFC", text).translate(_INVISIBLE))
    return _UNITS.get(key.lower())


def _number(text: str) -> float | None:
    """ASCII digits with "." or "," -> a number; None when malformed or ambiguous."""
    if re.fullmatch(r"\d+(?:\.\d+)?", text):
        return float(text)
    if re.fullmatch(r"\d+,\d{1,2}", text):  # decimal comma: "12,5", "0,45"
        return float(text.replace(",", "."))
    if re.fullmatch(r"\d{1,3}(?:,\d{3})+\.\d+", text) or re.fullmatch(
        r"\d{1,3}(?:,\d{3}){2,}", text
    ):
        return float(text.replace(",", ""))  # thousands separators: "1,883.5", "1,234,567"
    return None  # "1,883" (1.883 or 1883?), "12.5.3", "1.883,5", ...


def parse_cell(text: str | None) -> Cell:
    """One printed cell -> (value, unit, qualifier). Never guesses: see the module docstring."""
    if text is None:
        return _ABSENT
    s = _clean(text)
    if not s:
        return _ABSENT
    s = _RDA.sub("", s).strip()
    low = s.lower()
    if low.rstrip(".") in _NIL:
        return Cell(0.0, None, "nil")
    qualifier: Qualifier = "exact"
    if m := _UPPER.match(low):
        qualifier, low = "upper_bound", low[m.end() :]
    m = _NUMBER_UNIT.fullmatch(low)
    if m is None:
        return _UNREADABLE
    value = _number(m["num"])
    unit_text = m["unit"].strip()
    unit = parse_unit(unit_text) if unit_text else None
    if value is None or (unit_text and unit is None):
        return _UNREADABLE
    return Cell(value, unit, qualifier)


# --- NutritionExtractionV2 -> NutritionExtraction ----------------------------------------

# Units each row may carry (None = the field's own unit, as in extraction_v1).
_ROW_UNITS: dict[str, frozenset[Unit]] = {
    "energy_kcal": frozenset({"kcal"}),
    "energy_kj": frozenset({"kJ"}),
    "sodium_mg": frozenset({"mg", "g"}),
    "trans_fat_g": frozenset({"g", "mg"}),
}
_GRAMS: frozenset[Unit] = frozenset({"g"})
_SERVING_UNITS: frozenset[Unit] = frozenset({"g", "ml"})


def _cell_unit(cell: CellIn, parsed: Cell, allowed: frozenset[Unit]) -> tuple[bool, Unit | None]:
    """(readable, unit): the cell's own unit, else the row's unit label; both must agree and
    belong to the row. An unknown unit label makes the cell unreadable."""
    label_text = (cell.unit_label or "").strip()
    label = parse_unit(label_text) if label_text else None
    if label_text and label is None:
        return False, None
    if parsed.unit is not None and label is not None and parsed.unit != label:
        return False, None
    unit = parsed.unit or label
    return unit is None or unit in allowed, unit


def _column(
    col: NutrientCellsIn | None, path: str, unreadable: list[str], bounds: list[str]
) -> NutrientsIn | None:
    if col is None:
        return None
    values: dict[str, Any] = dict.fromkeys(NutrientsIn.model_fields)
    for field in NUTRIENT_FIELDS:
        cell: CellIn | None = getattr(col, field)
        parsed = parse_cell(cell.printed) if cell is not None else _ABSENT
        if parsed.qualifier == "absent":
            continue
        readable, unit = (
            _cell_unit(cell, parsed, _ROW_UNITS.get(field, _GRAMS))
            if cell is not None
            else (False, None)
        )
        if parsed.qualifier == "unreadable" or not readable:
            unreadable.append(f"{path}.{field}")
            continue
        values[field] = parsed.value
        if parsed.qualifier == "upper_bound":
            bounds.append(f"{path}.{field}")
        if field == "sodium_mg":
            values["sodium_unit"] = unit
        elif field == "trans_fat_g":
            values["trans_fat_unit"] = unit
    return NutrientsIn(**values)


def _serving(cell: CellIn | None, unreadable: list[str]) -> tuple[float | None, Unit | None]:
    """The serving size: an exact number in g or ml (or unit-less, as in v1). A count
    ("1 biscuit"), a multiple ("2 x 15 g"), a bound or another unit is unreadable."""
    parsed = parse_cell(cell.printed) if cell is not None else _ABSENT
    if parsed.qualifier == "absent" or cell is None:
        return None, None
    readable, unit = _cell_unit(cell, parsed, _SERVING_UNITS)
    if parsed.qualifier != "exact" or not readable:
        unreadable.append("serving_size_g")
        return None, None
    return parsed.value, unit


def to_extraction(raw: BaseModel) -> NutritionExtraction:
    """The `NutritionExtraction` the normaliser reads: v1 as is, v2 parsed cell by cell."""
    if isinstance(raw, NutritionExtraction):
        return raw
    if not isinstance(raw, NutritionExtractionV2):
        raise TypeError(f"not an extraction: {type(raw).__name__}")
    found: list[str] = []
    bounds: list[str] = []
    serving, serving_unit = _serving(raw.serving_size, found)
    per_100g = _column(raw.per_100g, "per_100g", found, bounds)
    per_serving = _column(raw.per_serving, "per_serving", found, bounds)
    return NutritionExtraction(
        product_name=raw.product_name,
        brand=raw.brand,
        basis_detected=raw.basis_detected,
        per_100g=per_100g,
        per_serving=per_serving,
        per_100_unit=raw.per_100_unit,
        serving_size_g=serving,
        serving_size_unit=serving_unit,
        ingredients=raw.ingredients,
        allergen_statement=raw.allergen_statement,
        may_contain_statement=raw.may_contain_statement,
        claims=raw.claims,
        veg_mark=raw.veg_mark,
        category_guess=raw.category_guess,
        confidence=raw.confidence,
        # The model's own paths first (input order), then the cells the parser could not read.
        unreadable_fields=list(dict.fromkeys([*raw.unreadable_fields, *found])),
        upper_bound_fields=bounds,
    )


def extraction_schema(prompt_version: str) -> type[BaseModel]:
    """The model-facing schema for a prompt version (KeyError for an unknown version)."""
    return EXTRACTION_SCHEMAS[prompt_version]
