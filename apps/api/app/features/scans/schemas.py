"""Label-extraction schema (Plan 4 Task 1).

`NutritionExtraction` is exactly what the vision model returns: values as printed,
per-100 g and per-serving kept separate. No derivation or conversion happens here
(the normaliser does that). Every field is required but nullable, as OpenAI-style
strict json_schema needs; a value not printed on the label is `None`.
"""

from __future__ import annotations

import copy
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict


class NutrientsIn(BaseModel):
    """One nutrition-table column as printed. None = not printed or unreadable."""

    model_config = ConfigDict(extra="forbid")

    energy_kcal: float | None
    energy_kj: float | None
    protein_g: float | None
    carbs_g: float | None
    sugars_g: float | None
    added_sugars_g: float | None
    fat_g: float | None
    sat_fat_g: float | None
    trans_fat_g: float | None
    fiber_g: float | None
    salt_g: float | None
    sodium_mg: float | None


class NutritionExtraction(BaseModel):
    model_config = ConfigDict(extra="forbid")

    product_name: str | None
    brand: str | None
    basis_detected: Literal["per_100g", "per_serving", "both", "unknown"]
    per_100g: NutrientsIn | None
    per_serving: NutrientsIn | None
    serving_size_g: float | None
    ingredients: list[str]  # as printed, original script, order kept
    allergen_statement: str | None
    may_contain_statement: str | None
    claims: list[str]  # front-of-pack claims as printed
    veg_mark: Literal["veg", "non_veg"] | None
    category_guess: Literal["general", "beverage", "water", "cheese", "fat"] | None
    confidence: float  # 0..1, the model's own legibility estimate
    unreadable_fields: list[str]


def _strictify(node: Any) -> None:
    if isinstance(node, dict):
        if node.get("type") == "object" or "properties" in node:
            node["additionalProperties"] = False
            node["required"] = list(node.get("properties", {}))
        node.pop("default", None)
        for value in node.values():
            _strictify(value)
    elif isinstance(node, list):
        for item in node:
            _strictify(item)


def extraction_json_schema() -> dict[str, Any]:
    """`NutritionExtraction` JSON schema adapted for strict mode.

    Every object (including `$defs`) gets `additionalProperties: false` and lists all
    of its properties as required; nullability stays a union with `null`.
    """
    schema = copy.deepcopy(NutritionExtraction.model_json_schema())
    _strictify(schema)
    return schema
