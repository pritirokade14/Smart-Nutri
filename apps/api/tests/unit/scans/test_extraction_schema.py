from pathlib import Path

import pytest
from pydantic import ValidationError

from app.features.scans.schemas import NutritionExtraction, extraction_json_schema
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


def sample_extraction(**overrides):
    data = {
        "product_name": "Peanut Chikki",
        "brand": None,
        "basis_detected": "per_100g",
        "per_100g": dict.fromkeys(_NUTRIENT_KEYS),
        "per_serving": None,
        "serving_size_g": None,
        "ingredients": ["peanuts", "sugar"],
        "allergen_statement": None,
        "may_contain_statement": None,
        "claims": [],
        "veg_mark": "veg",
        "category_guess": "general",
        "confidence": 0.9,
        "unreadable_fields": [],
    }
    data.update(overrides)
    return data


def test_schema_is_strict():
    s = extraction_json_schema()
    assert s["additionalProperties"] is False
    assert set(s["required"]) == set(NutritionExtraction.model_fields)
    nutrients = s["$defs"]["NutrientsIn"]
    assert nutrients["additionalProperties"] is False
    assert set(nutrients["required"]) == set(_NUTRIENT_KEYS)


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
