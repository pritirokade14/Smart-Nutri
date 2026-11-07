"""Recipes API shapes (Plan 12 Task 12; spec 5.9, 6.3). Every number in `RecipeOut` is redacted
with the member's numbers display (G15); `incomplete_nutrients` and the weights stay."""

from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, Field, field_validator, model_validator

from app.core.errors import ApiError
from app.features.foods.units import UnitCode
from app.features.meals.schemas import NutrientSnapshot
from app.features.targets.schemas import NumbersHidden

MAX_INGREDIENTS = 50


class RecipeIngredientIn(BaseModel):
    """Exactly one reference (a generic food, one of your custom foods, one of our products or
    an Open Food Facts barcode), else 422 `invalid_product_ref`, and an amount: ``quantity`` of a
    household ``unit`` (grams always work)."""

    food_id: UUID | None = None
    custom_food_id: UUID | None = None
    product_id: UUID | None = None
    barcode: str | None = Field(default=None, max_length=64)
    quantity: float = Field(gt=0, le=5000, allow_inf_nan=False)
    unit: UnitCode

    @model_validator(mode="after")
    def _one_ref(self) -> "RecipeIngredientIn":
        given = [x for x in (self.food_id, self.custom_food_id, self.product_id, self.barcode) if x]
        if len(given) != 1:
            raise ApiError("invalid_product_ref", 422)
        return self


class RecipeIn(BaseModel):
    """``servings`` (optional) gives the per-serving values; ``cooked_weight_g`` (optional) is the
    pot weighed after cooking, the best basis for the per-100 g values. Without it the raw
    total is used, which needs every ingredient to have a mass."""

    name: str = Field(min_length=1, max_length=80)
    servings: float | None = Field(default=None, gt=0, le=100, allow_inf_nan=False)
    cooked_weight_g: float | None = Field(default=None, gt=0, le=20000, allow_inf_nan=False)
    ingredients: list[RecipeIngredientIn] = Field(
        description="1 to 50, else 422 `recipe_ingredient_limit`"
    )
    client_id: UUID | None = None

    @field_validator("name", mode="before")
    @classmethod
    def _trim(cls, value: object) -> object:
        return value.strip() if isinstance(value, str) else value

    @model_validator(mode="after")
    def _valid(self) -> "RecipeIn":
        if not self.name:
            raise ApiError("validation_error", 422, details={"fields": ["body.name"]})
        if not 1 <= len(self.ingredients) <= MAX_INGREDIENTS:
            raise ApiError("recipe_ingredient_limit", 422, details={"max": MAX_INGREDIENTS})
        return self


class RecipeIngredientOut(BaseModel):
    position: int
    source_kind: Literal["product", "off", "food", "custom_food"]
    food_id: UUID | None
    custom_food_id: UUID | None
    product_id: UUID | None
    barcode: str | None
    name: str
    quantity: float
    unit: str
    grams: float = Field(description="The amount in the ingredient's basis (g, or ml)")
    attribution: str | None
    available: bool = Field(
        description=(
            "false when the custom food it used was deleted: replace it before saving the recipe"
        )
    )


class RecipeOut(BaseModel):
    id: UUID
    name: str
    servings: float | None
    cooked_weight_g: float | None
    total_raw_g: float | None = Field(
        description="The raw total; null when an ingredient has no mass"
    )
    basis_weight_g: float = Field(description="The cooked weight, or else the raw total")
    per_100g: NutrientSnapshot = Field(
        description=(
            "Per 100 g of the basis weight, 1 dp: the sum of the KNOWN ingredients. A nutrient "
            "listed in `incomplete_nutrients` is a lower bound (show it as 'at least'); null "
            "when no ingredient knows it, or hidden"
        )
    )
    per_serving: NutrientSnapshot | None = Field(
        description="Per serving, 1 dp, same rules; null without `servings`"
    )
    incomplete_nutrients: list[str] = Field(
        description="NutrientSnapshot keys at least one ingredient does not know"
    )
    attributions: list[str]
    ingredients: list[RecipeIngredientOut]
    numbers_hidden: NumbersHidden
    updated_at: datetime


class RecipeSummaryOut(BaseModel):
    id: UUID
    name: str
    servings: float | None
    incomplete_nutrients: list[str]
    updated_at: datetime


class RecipesOut(BaseModel):
    items: list[RecipeSummaryOut]
    next_cursor: str | None = Field(description="Opaque; pass back as `cursor`")
