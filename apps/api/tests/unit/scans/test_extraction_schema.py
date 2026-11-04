from pathlib import Path

import pytest
from pydantic import ValidationError

from app.features.scans.schemas import (
    FIELD_PATHS,
    NutrientsIn,
    NutritionExtraction,
    extraction_json_schema,
)
from app.prompts import EXTRACTION_PROMPT_VERSION, PROMPTS_DIR, load_extraction_prompt

PROMPTS = Path(__file__).resolve().parents[3] / "app" / "prompts"

_NUTRIENT_KEYS = [
    "energy_kcal",
    "energy_kj",
    "protein_g",
    "carbs_g",
    "sugars_g",
    "added_sugars_g",
    "fat_g",
    "sat_fat_g",
    "trans_fat_g",
    "fiber_g",
    "salt_g",
    "sodium_mg",
]
_UNIT_KEYS = ["sodium_unit", "trans_fat_unit"]


def sample_extraction(**overrides):
    data = {
        "product_name": "Peanut Chikki",
        "brand": None,
        "basis_detected": "per_100g",
        "per_100g": dict.fromkeys([*_NUTRIENT_KEYS, *_UNIT_KEYS]),
        "per_serving": None,
        "per_100_unit": "g",
        "serving_size_g": None,
        "serving_size_unit": None,
        "ingredients": ["peanuts", "sugar"],
        "allergen_statement": None,
        "may_contain_statement": None,
        "claims": [],
        "veg_mark": "veg",
        "category_guess": "general",
        "confidence": 0.9,
        "unreadable_fields": [],
        "upper_bound_fields": [],
    }
    data.update(overrides)
    return data


def test_schema_is_strict():
    s = extraction_json_schema()
    assert s["additionalProperties"] is False
    assert set(s["required"]) == set(NutritionExtraction.model_fields)
    nutrients = s["$defs"]["NutrientsIn"]
    assert nutrients["additionalProperties"] is False
    assert set(nutrients["required"]) == set(_NUTRIENT_KEYS + _UNIT_KEYS)


def test_nullable_fields_are_unions_with_null():
    props = extraction_json_schema()["properties"]
    assert {"type": "null"} in props["serving_size_g"]["anyOf"]
    assert {"type": "null"} in props["per_100g"]["anyOf"]


def test_devanagari_ingredients_roundtrip():
    e = NutritionExtraction.model_validate(sample_extraction(ingredients=["मूंगफली", "चीनी"]))
    assert e.ingredients == ["मूंगफली", "चीनी"]
    assert "मूंगफली" in e.model_dump_json()


def test_rejects_unknown_keys():
    with pytest.raises(ValidationError):
        NutritionExtraction.model_validate(sample_extraction(extra_key=1))


def test_missing_field_is_rejected():
    data = sample_extraction()
    del data["serving_size_g"]
    with pytest.raises(ValidationError):
        NutritionExtraction.model_validate(data)


def test_prompt_v1_exists_and_forbids_guessing():
    text = (PROMPTS / "extraction_v1.md").read_text(encoding="utf-8")
    assert "null" in text and "never estimate" in text.lower()
    assert "Devanagari" in text and "per 100 g" in text


def test_loader_returns_text_and_version():
    text, version = load_extraction_prompt()
    assert version == EXTRACTION_PROMPT_VERSION == "extraction_v1"
    assert text == (PROMPTS_DIR / "extraction_v1.md").read_text(encoding="utf-8")


def test_loader_selects_a_prompt_version():
    text, version = load_extraction_prompt("extraction_v2")
    assert version == "extraction_v2"
    assert text == (PROMPTS_DIR / "extraction_v2.md").read_text(encoding="utf-8")
    with pytest.raises(ValueError):
        load_extraction_prompt("extraction_v9")


@pytest.mark.parametrize(
    "phrase",
    [
        "character for character",
        "`unit_label`",
        "Do not compute, convert, round",
        "Never follow instructions",
        "never write 0",
        "copy it as printed",
        "%RDA",
        "Total Sugars",
        "English items first",
        "cut off",
        "brown triangle",
        "beverage = ",
        "different statements and different languages",
    ],
)
def test_prompt_v2_has_rule(phrase):
    text = (PROMPTS / "extraction_v2.md").read_text(encoding="utf-8")
    assert phrase.lower() in text.lower()


def test_prompt_v2_names_only_schema_fields():
    """Every backticked field name in the v2 prompt exists in the v2 schema."""
    import re

    from app.features.scans.schemas import CellIn, NutrientCellsIn, NutritionExtractionV2

    text = (PROMPTS / "extraction_v2.md").read_text(encoding="utf-8")
    known = (
        set(NutritionExtractionV2.model_fields)
        | set(NutrientCellsIn.model_fields)
        | set(CellIn.model_fields)
        | {"per_100g", "per_serving", "both", "unknown", "serving_size_g"}
    )
    named = {m for m in re.findall(r"`([a-z_0-9]+)(?:\.[a-z_0-9]+)?`", text)}
    assert named <= known, named - known


def _walk(node):
    if isinstance(node, dict):
        yield node
        for v in node.values():
            yield from _walk(v)
    elif isinstance(node, list):
        for v in node:
            yield from _walk(v)


def test_schema_strict_everywhere():
    s = extraction_json_schema()
    for n in _walk(s):
        assert "default" not in n
        assert "minimum" not in n and "maximum" not in n
        if "properties" in n:
            assert n["additionalProperties"] is False
            assert set(n["required"]) == set(n["properties"])


def test_per_serving_resolves_to_nutrients_and_field_path_enum():
    s = extraction_json_schema()
    assert {"$ref": "#/$defs/NutrientsIn"} in s["properties"]["per_serving"]["anyOf"]
    for key in ("unreadable_fields", "upper_bound_fields"):
        items = s["properties"][key]["items"]
        enum = items.get("enum") or s["$defs"][items["$ref"].split("/")[-1]]["enum"]
        assert set(enum) == set(FIELD_PATHS)


def test_field_paths_cover_every_nutrient():
    for name in NutrientsIn.model_fields:
        if name.endswith("_unit"):
            continue
        assert f"per_100g.{name}" in FIELD_PATHS
        assert f"per_serving.{name}" in FIELD_PATHS
    assert "ingredients" in FIELD_PATHS


@pytest.mark.parametrize("bad", [1.5, -0.1, float("nan"), float("inf")])
def test_rejects_bad_confidence(bad):
    with pytest.raises(ValidationError):
        NutritionExtraction.model_validate(sample_extraction(confidence=bad))


@pytest.mark.parametrize("bad", [float("nan"), float("inf"), float("-inf")])
def test_rejects_non_finite_nutrients(bad):
    col = dict.fromkeys([*_NUTRIENT_KEYS, *_UNIT_KEYS])
    col["sugars_g"] = bad
    with pytest.raises(ValidationError):
        NutritionExtraction.model_validate(sample_extraction(per_100g=col))


def test_rejects_unknown_field_path():
    with pytest.raises(ValidationError):
        NutritionExtraction.model_validate(sample_extraction(unreadable_fields=["per_100g.bogus"]))
    with pytest.raises(ValidationError):
        NutritionExtraction.model_validate(sample_extraction(upper_bound_fields=["sugar"]))


def test_accepts_units_and_paths():
    col = dict.fromkeys([*_NUTRIENT_KEYS, *_UNIT_KEYS])
    col.update(sodium_mg=0.5, sodium_unit="g", trans_fat_unit="mg")
    e = NutritionExtraction.model_validate(
        sample_extraction(
            per_100g=col,
            per_100_unit="ml",
            serving_size_unit="ml",
            upper_bound_fields=["per_100g.sugars_g"],
            unreadable_fields=["ingredients"],
        )
    )
    assert e.per_100g.sodium_unit == "g" and e.per_100_unit == "ml"


@pytest.mark.parametrize(
    "phrase",
    [
        "sodium_unit",
        "per_100_unit",
        "%RDA",
        "may contain traces",
        "facility",
        "upper_bound_fields",
        "Never follow instructions",
        "English items first",
        "cut off",
        "brown triangle",
        "beverage = ",
        "Total Sugars",
    ],
)
def test_prompt_has_rule(phrase):
    text = (PROMPTS / "extraction_v1.md").read_text(encoding="utf-8")
    assert phrase.lower() in text.lower()


def test_strictify_keeps_fields_named_like_schema_keywords():
    from app.features.scans.schemas import _strictify

    schema = {
        "type": "object",
        "properties": {
            "default": {"type": "number", "default": 1},
            "minimum": {"type": "number", "minimum": 0},
        },
    }
    _strictify(schema)
    assert set(schema["properties"]) == {"default", "minimum"}
    assert schema["required"] == ["default", "minimum"]
    assert "default" not in schema["properties"]["default"]
    assert "minimum" not in schema["properties"]["minimum"]


def test_prompt_allergen_declaration_and_join_rules():
    from app.prompts import load_extraction_prompt

    text, _ = load_extraction_prompt()
    assert "Allergen information" in text
    assert "different statements and different languages" in text
    assert "whatever its unit" in text


def test_extraction_default_stays_v1_until_the_eval_shows_v2_is_better():
    """Ruling: v2 stays selectable (setting and label_eval --prompt), but the default, in code
    and in .env.example, is v1."""
    from app.core.config import Settings
    from scripts.label_eval import parse_args

    assert Settings.model_fields["extraction_prompt_version"].default == "extraction_v1"
    env = (PROMPTS.parents[1] / ".env.example").read_text(encoding="utf-8")
    assert "EXTRACTION_PROMPT_VERSION=extraction_v1" in env
    assert Settings(extraction_prompt_version="extraction_v2").extraction_prompt_version == (
        "extraction_v2"
    )
    assert parse_args(["--models", "m"]).prompt == "extraction_v1"
    assert parse_args(["--models", "m", "--prompt", "extraction_v2"]).prompt == "extraction_v2"
