"""Label-extraction schema (Plan 4 Task 1).

`NutritionExtraction` is exactly what the vision model returns: values as printed,
per-100 g and per-serving kept separate. No derivation or conversion happens here
(the normaliser does that). Every field is required but nullable, as OpenAI-style
strict json_schema needs; a value not printed on the label is `None`.
"""

from __future__ import annotations

import copy
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field

_STRICT = ConfigDict(extra="forbid", allow_inf_nan=False)


class NutrientsIn(BaseModel):
    """One nutrition-table column as printed. None = not printed or unreadable."""

    model_config = _STRICT

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
    sodium_unit: Literal["mg", "g"] | None  # unit exactly as printed
    trans_fat_unit: Literal["mg", "g"] | None


NUTRIENT_FIELDS: tuple[str, ...] = tuple(
    name for name in NutrientsIn.model_fields if not name.endswith("_unit")
)
_TOP_LEVEL_PATHS = (
    "product_name",
    "brand",
    "serving_size_g",
    "ingredients",
    "allergen_statement",
    "may_contain_statement",
    "claims",
    "veg_mark",
    "category_guess",
)
FIELD_PATHS: tuple[str, ...] = (
    *_TOP_LEVEL_PATHS,
    *(f"per_100g.{n}" for n in NUTRIENT_FIELDS),
    *(f"per_serving.{n}" for n in NUTRIENT_FIELDS),
)
FieldPath = Literal[FIELD_PATHS]  # type: ignore[valid-type]


class NutritionExtraction(BaseModel):
    model_config = _STRICT

    product_name: str | None
    brand: str | None
    basis_detected: Literal["per_100g", "per_serving", "both", "unknown"]
    per_100g: NutrientsIn | None
    per_serving: NutrientsIn | None
    per_100_unit: Literal["g", "ml"] | None  # unit of the per-100 column
    serving_size_g: float | None
    serving_size_unit: Literal["g", "ml"] | None
    ingredients: list[str]  # as printed, original script, order kept
    allergen_statement: str | None
    may_contain_statement: str | None
    claims: list[str]  # front-of-pack claims as printed
    veg_mark: Literal["veg", "non_veg"] | None
    category_guess: Literal["general", "beverage", "water", "cheese", "fat"] | None
    confidence: float = Field(ge=0, le=1)  # the model's own legibility estimate
    unreadable_fields: list[FieldPath]  # type: ignore[valid-type]
    upper_bound_fields: list[FieldPath]  # type: ignore[valid-type]  # printed "<X"; value is X


def _strictify(node: Any) -> None:
    """Make a JSON-schema node strict-mode compatible, in place.

    Only schema nodes are edited. The names inside a ``properties`` (or ``$defs``) map
    are field/definition names, so a field called ``default`` or ``minimum`` is kept.
    """
    if isinstance(node, list):
        for item in node:
            _strictify(item)
        return
    if not isinstance(node, dict):
        return
    if node.get("type") == "object" or "properties" in node:
        node["additionalProperties"] = False
        node["required"] = list(node.get("properties", {}))
    node.pop("default", None)
    # strict mode rejects numeric bounds; Pydantic still enforces them on parse
    node.pop("minimum", None)
    node.pop("maximum", None)
    for key, value in node.items():
        if key in ("properties", "$defs") and isinstance(value, dict):
            for sub in value.values():  # values are schema nodes; keys are names
                _strictify(sub)
        else:
            _strictify(value)


def extraction_json_schema() -> dict[str, Any]:
    """`NutritionExtraction` JSON schema adapted for strict mode.

    Every object (including `$defs`) gets `additionalProperties: false` and lists all
    of its properties as required; nullability stays a union with `null`. Numeric
    `minimum`/`maximum` are stripped (strict mode rejects them); validation still
    happens in Pydantic.
    """
    schema = copy.deepcopy(NutritionExtraction.model_json_schema())
    _strictify(schema)
    return schema
