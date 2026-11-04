"""Label accuracy v2, item 3: the model copies each nutrition cell verbatim (extraction_v2),
and `app.features.scans.cells` parses it deterministically.

Anything the parser cannot read with certainty becomes None and an `unreadable_fields`
path (never a guess): ranges, percentages, "Traces", "-", ambiguous "1,883", unknown units,
two numbers in one cell, a unit that does not belong to the row.
"""

import pytest

from app.features.scans.cells import (
    Cell,
    extraction_schema,
    parse_cell,
    parse_unit,
    to_extraction,
)
from app.features.scans.normalize import to_draft
from app.features.scans.schemas import (
    CellIn,
    NutrientCellsIn,
    NutritionExtraction,
    NutritionExtractionV2,
    extraction_json_schema,
)


@pytest.mark.parametrize(
    ("text", "expected"),
    [
        # plain numbers and units
        ("12.5", Cell(12.5, None, "exact")),
        ("12.5 g", Cell(12.5, "g", "exact")),
        ("12.5g", Cell(12.5, "g", "exact")),
        ("12.5 gm", Cell(12.5, "g", "exact")),
        ("0", Cell(0.0, None, "exact")),
        ("0.0 g", Cell(0.0, "g", "exact")),
        ("450 kcal", Cell(450.0, "kcal", "exact")),
        ("450 Kcal", Cell(450.0, "kcal", "exact")),
        ("450kcal", Cell(450.0, "kcal", "exact")),
        ("1883 kJ", Cell(1883.0, "kJ", "exact")),
        ("200 mg", Cell(200.0, "mg", "exact")),
        ("250 ml", Cell(250.0, "ml", "exact")),
        ("  12.5  g ", Cell(12.5, "g", "exact")),
        (chr(0x200B) + "12.5" + chr(0x200D) + " g", Cell(12.5, "g", "exact")),
        # comma decimals and thousands
        ("12,5 g", Cell(12.5, "g", "exact")),
        ("0,45", Cell(0.45, None, "exact")),
        ("1,883.5 kJ", Cell(1883.5, "kJ", "exact")),
        ("1,234,567", Cell(1234567.0, None, "exact")),
        # Devanagari digits and Hindi/Marathi units
        ("१२.५", Cell(12.5, None, "exact")),
        ("१२.५ ग्रा", Cell(12.5, "g", "exact")),
        ("१२.५ ग्राम", Cell(12.5, "g", "exact")),
        ("१२.५ ग्रॅ", Cell(12.5, "g", "exact")),
        ("२०० मि.ग्रा.", Cell(200.0, "mg", "exact")),
        ("२०० मिग्रॅ", Cell(200.0, "mg", "exact")),
        ("४५० किलो कैलोरी", Cell(450.0, "kcal", "exact")),
        ("४५० कि.कॅलरी", Cell(450.0, "kcal", "exact")),
        ("०.५", Cell(0.5, None, "exact")),
        # qualifiers
        ("<0.5 g", Cell(0.5, "g", "upper_bound")),
        ("< 0.5", Cell(0.5, None, "upper_bound")),
        ("less than 0.5 g", Cell(0.5, "g", "upper_bound")),
        ("≤0.1", Cell(0.1, None, "upper_bound")),
        ("<०.५ ग्रा", Cell(0.5, "g", "upper_bound")),
        ("Nil", Cell(0.0, None, "nil")),
        ("NIL", Cell(0.0, None, "nil")),
        ("nil.", Cell(0.0, None, "nil")),
        ("शून्य", Cell(0.0, None, "nil")),
        # %RDA in brackets next to the value is ignored
        ("12.5 g (18%)", Cell(12.5, "g", "exact")),
        # absent
        (None, Cell(None, None, "absent")),
        ("", Cell(None, None, "absent")),
        ("   ", Cell(None, None, "absent")),
        # unreadable: never guessed
        ("Traces", Cell(None, None, "unreadable")),
        ("trace", Cell(None, None, "unreadable")),
        ("-", Cell(None, None, "unreadable")),
        ("—", Cell(None, None, "unreadable")),
        ("N/A", Cell(None, None, "unreadable")),
        ("ND", Cell(None, None, "unreadable")),
        ("1,883", Cell(None, None, "unreadable")),  # 1.883 or 1883: ambiguous
        ("12%", Cell(None, None, "unreadable")),
        ("5-7 g", Cell(None, None, "unreadable")),
        ("~5 g", Cell(None, None, "unreadable")),
        (">5", Cell(None, None, "unreadable")),
        ("200 mcg", Cell(None, None, "unreadable")),
        ("12.5.3", Cell(None, None, "unreadable")),
        ("450 kcal / 1883 kJ", Cell(None, None, "unreadable")),
        ("2 x 15 g", Cell(None, None, "unreadable")),
        ("1 biscuit", Cell(None, None, "unreadable")),
    ],
)
def test_parse_cell(text, expected):
    assert parse_cell(text) == expected


@pytest.mark.parametrize(
    ("text", "unit"),
    [
        ("g", "g"),
        ("(g)", "g"),
        ("mg", "mg"),
        ("MG", "mg"),
        ("kcal", "kcal"),
        ("kJ", "kJ"),
        ("ml", "ml"),
        ("मि.ग्रा.", "mg"),
        ("ग्रॅम", "g"),
        ("%", None),
        ("mcg", None),
        ("", None),
    ],
)
def test_parse_unit(text, unit):
    assert parse_unit(text) == unit


def test_parser_never_raises_and_never_reads_digits_that_are_not_there():
    import random

    rng = random.Random(20261104)
    pool = list("0123456789०१२३४५६७८९.,<>-–—~%()/ gmkcalJ ") + ["mg", "ग्रा", "Nil", "x"]
    for _ in range(5000):
        text = "".join(rng.choice(pool) for _ in range(rng.randint(0, 10)))
        c = parse_cell(text)
        assert c.qualifier in {"exact", "upper_bound", "nil", "unreadable", "absent"}
        if c.value is not None and c.qualifier != "nil":
            assert any(ch.isdigit() for ch in text)


# --- NutritionExtractionV2 -> NutritionExtraction ---------------------------------------


def cell(printed: str | None, unit_label: str | None = None) -> CellIn:
    return CellIn(printed=printed, unit_label=unit_label)


def cells(**kw) -> NutrientCellsIn:
    return NutrientCellsIn(**(dict.fromkeys(NutrientCellsIn.model_fields) | kw))


def ex2(**kw) -> NutritionExtractionV2:
    data = {
        "product_name": "Masala Crunch",
        "brand": "Acme",
        "basis_detected": "per_100g",
        "per_100g": cells(),
        "per_serving": None,
        "per_100_unit": "g",
        "serving_size": None,
        "ingredients": ["wheat flour"],
        "allergen_statement": None,
        "may_contain_statement": None,
        "claims": [],
        "veg_mark": "veg",
        "category_guess": "general",
        "confidence": 0.9,
        "unreadable_fields": [],
    }
    return NutritionExtractionV2(**(data | kw))


def test_v2_values_units_and_bounds_are_computed_in_code():
    e = to_extraction(
        ex2(
            per_100g=cells(
                energy_kcal=cell("450", "kcal"),
                protein_g=cell("<0.5 g"),
                sugars_g=cell("Nil"),
                sodium_mg=cell("0.4", "g"),
                trans_fat_g=cell("50 mg"),
                fiber_g=cell("Traces"),
                salt_g=cell("१.०", "ग्रा"),
            ),
            serving_size=cell("30 g"),
        )
    )
    assert isinstance(e, NutritionExtraction)
    p = e.per_100g
    assert p.energy_kcal == 450 and p.protein_g == 0.5 and p.sugars_g == 0.0
    assert p.sodium_mg == 0.4 and p.sodium_unit == "g"
    assert p.trans_fat_g == 50 and p.trans_fat_unit == "mg"
    assert p.fiber_g is None and p.salt_g == 1.0
    assert e.upper_bound_fields == ["per_100g.protein_g"]
    assert e.unreadable_fields == ["per_100g.fiber_g"]
    assert e.serving_size_g == 30 and e.serving_size_unit == "g"


def test_v2_sodium_without_any_unit_stays_unconfirmed():
    e = to_extraction(ex2(per_100g=cells(sodium_mg=cell("400"))))
    assert e.per_100g.sodium_mg == 400 and e.per_100g.sodium_unit is None
    assert "unit_unconfirmed:per_100g.sodium_mg" in to_draft(e).warnings


@pytest.mark.parametrize(
    ("field", "c"),
    [
        ("energy_kcal", cell("1883 kJ")),  # a kJ value in the kcal row
        ("energy_kj", cell("450", "kcal")),
        ("protein_g", cell("3 mg")),  # protein is never printed in mg
        ("sodium_mg", cell("200", "kcal")),
        ("sugars_g", cell("5 g", "mg")),  # the cell and the row disagree
        ("fat_g", cell("5", "%")),
    ],
)
def test_v2_unit_that_does_not_belong_to_the_row_is_unreadable(field, c):
    e = to_extraction(ex2(per_100g=cells(**{field: c})))
    assert getattr(e.per_100g, field) is None
    assert f"per_100g.{field}" in e.unreadable_fields


def test_v2_model_unreadable_paths_are_kept_first():
    e = to_extraction(
        ex2(
            per_100g=cells(fiber_g=cell("-")),
            unreadable_fields=["ingredients", "per_100g.fiber_g"],
        )
    )
    assert e.unreadable_fields == ["ingredients", "per_100g.fiber_g"]


@pytest.mark.parametrize(
    ("printed", "value", "unit", "unreadable"),
    [
        ("30 g", 30.0, "g", False),
        ("२०० मि.ली.", 200.0, "ml", False),
        ("30", 30.0, None, False),
        ("2 x 15 g", None, None, True),  # never multiplied
        ("<30 g", None, None, True),
        ("30 mg", None, None, True),
        (None, None, None, False),
    ],
)
def test_v2_serving_size(printed, value, unit, unreadable):
    e = to_extraction(ex2(serving_size=cell(printed) if printed is not None else None))
    assert e.serving_size_g == value and e.serving_size_unit == unit
    assert ("serving_size_g" in e.unreadable_fields) is unreadable


def test_v2_columns_and_texts_pass_through():
    e = to_extraction(
        ex2(
            basis_detected="both",
            per_serving=cells(sugars_g=cell("3")),
            per_100_unit="ml",
            ingredients=["दूध", "चीनी"],
            allergen_statement="इसमें दूध है",
        )
    )
    assert e.basis_detected == "both" and e.per_serving.sugars_g == 3
    assert e.per_100_unit == "ml" and e.ingredients == ["दूध", "चीनी"]
    assert e.allergen_statement == "इसमें दूध है"


def test_v2_absent_column_stays_none():
    assert to_extraction(ex2(per_100g=None)).per_100g is None


def test_v1_extraction_passes_through_unchanged():
    v1 = to_extraction(ex2())
    assert to_extraction(v1) is v1


def test_extraction_schema_by_prompt_version():
    assert extraction_schema("extraction_v1") is NutritionExtraction
    assert extraction_schema("extraction_v2") is NutritionExtractionV2
    with pytest.raises(KeyError):
        extraction_schema("extraction_v9")


def test_v2_strict_json_schema_has_no_floats_for_nutrients():
    schema = extraction_json_schema(NutritionExtractionV2)
    cell_def = schema["$defs"]["CellIn"]
    assert cell_def["additionalProperties"] is False
    assert cell_def["required"] == ["printed", "unit_label"]
    column = schema["$defs"]["NutrientCellsIn"]
    assert "sodium_unit" not in column["properties"]
    assert "upper_bound_fields" not in schema["properties"]
    assert schema["additionalProperties"] is False
    assert set(schema["required"]) == set(NutritionExtractionV2.model_fields)


# --- P9 integration q2: "N,NNN" is a thousands separator only when plausible ------------------
# A lone comma followed by exactly three digits is 1.883 or 1883. parse_cell alone never
# guesses; the row decides: thousands only if the result is plausible for that field and
# unit (the engine's per-100 bounds), otherwise unreadable. Never 1000x too small.


@pytest.mark.parametrize("text", ["1,000 g", "1,883", "1,000", "<1,000 mg", "१,८८३ kJ"])
def test_parse_cell_alone_never_reads_an_ambiguous_comma(text):
    c = parse_cell(text)
    assert c.value is None and c.qualifier == "unreadable"


@pytest.mark.parametrize(
    ("field", "c", "value"),
    [
        ("energy_kj", cell("1,883 kJ"), 1883.0),
        ("energy_kj", cell("1,883", "kJ"), 1883.0),
        ("energy_kj", cell("१,८८३", "किलोजूल"), 1883.0),
        ("sodium_mg", cell("1,200 mg"), 1200.0),
        ("sodium_mg", cell("1,200", "mg"), 1200.0),
        ("trans_fat_g", cell("1,200 mg"), 1200.0),
    ],
)
def test_ambiguous_comma_is_thousands_when_plausible(field, c, value):
    e = to_extraction(ex2(per_100g=cells(**{field: c})))
    assert getattr(e.per_100g, field) == value
    assert f"per_100g.{field}" not in e.unreadable_fields


@pytest.mark.parametrize(
    ("field", "c"),
    [
        ("protein_g", cell("1,000 g")),  # 1000 g per 100 g: impossible, and never 1 g
        ("sugars_g", cell("1,883")),
        ("fat_g", cell("1,000", "g")),
        ("energy_kcal", cell("1,000 kcal")),  # > 900 kcal per 100 g
        ("energy_kcal", cell("1,883", "kcal")),
        ("energy_kj", cell("9,999 kJ")),  # > 900 kcal in kJ
        ("sodium_mg", cell("1,200 g")),
        ("sodium_mg", cell("1,200")),  # unit unknown: the strictest row unit (g) decides
        ("trans_fat_g", cell("1,200 g")),
        ("salt_g", cell("<1,000 g")),
    ],
)
def test_ambiguous_comma_is_unreadable_when_implausible(field, c):
    for column in ("per_100g", "per_serving"):
        e = to_extraction(ex2(**{column: cells(**{field: c})}))
        assert getattr(getattr(e, column), field) is None
        assert f"{column}.{field}" in e.unreadable_fields


def test_ambiguous_serving_size():
    e = to_extraction(ex2(serving_size=cell("1,000 g")))
    assert e.serving_size_g == 1000.0 and e.serving_size_unit == "g"
    assert "serving_size_g" not in e.unreadable_fields
    e = to_extraction(ex2(serving_size=cell("9,999 ml")))  # > MAX_SERVING_SIZE_G
    assert e.serving_size_g is None and "serving_size_g" in e.unreadable_fields


def test_ambiguous_comma_never_reads_1000x_too_small():
    fields = ["energy_kcal", "energy_kj", "protein_g", "sugars_g", "sodium_mg", "trans_fat_g"]
    for printed in ["1,000", "1,883", "2,500", "1,000 g", "1,883 kJ", "1,200 mg", "<1,000 mg"]:
        for field in fields:
            e = to_extraction(ex2(per_100g=cells(**{field: cell(printed)})))
            v = getattr(e.per_100g, field)
            assert v is None or v >= 1000, (printed, field, v)
        e = to_extraction(ex2(serving_size=cell(printed)))
        assert e.serving_size_g is None or e.serving_size_g >= 1000, printed
