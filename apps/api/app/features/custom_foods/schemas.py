"""Custom foods API shapes (Plan 12 Task 11; spec 5.8, 6.3). A custom food is the label the
account typed: a blank nutrient is absent (unknown), never 0. Names and values are user data and
are never sent to analytics, logs or prompts."""

from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, Field, field_validator, model_validator

from app.core.errors import ApiError
from app.features.foods.units import UnitCode
from app.features.meals.schemas import NutrientSnapshot

MAX_NAME = 80
MAX_PORTIONS = 10
NUTRIENT_FIELDS = (
    "energy_kcal",
    "protein_g",
    "carbs_g",
    "sugars_g",
    "fat_g",
    "sat_fat_g",
    "fibre_g",
    "salt_g",
    "sodium_mg",
)
_NutrientValue = Field(default=None, ge=0, le=100000, allow_inf_nan=False)


def _trim(value: object) -> object:
    return value.strip() if isinstance(value, str) else value


class CustomNutrientsIn(BaseModel):
    """What the label says, per 100 g/ml or per serving (`values_per`). A blank is `null`
    (unknown). Salt and sodium follow the engine's rule (the higher one wins)."""

    energy_kcal: float | None = _NutrientValue
    protein_g: float | None = _NutrientValue
    carbs_g: float | None = _NutrientValue
    sugars_g: float | None = _NutrientValue
    fat_g: float | None = _NutrientValue
    sat_fat_g: float | None = _NutrientValue
    fibre_g: float | None = _NutrientValue
    salt_g: float | None = _NutrientValue
    sodium_mg: float | None = _NutrientValue


class CustomPortionIn(BaseModel):
    unit: UnitCode = Field(description="A count or volume unit (never g or serving)")
    grams_per_unit: float = Field(
        gt=0, le=2000, description="The amount of one unit in the food's basis"
    )


class CustomFoodIn(BaseModel):
    """A full description of the food (`PUT` replaces it, so a nutrient left out is unknown).
    ``values_per = "serving"`` needs ``serving_g`` (in the basis unit, g or ml); the API
    converts to per 100 g/ml."""

    name: str = Field(min_length=1, max_length=MAX_NAME)
    brand: str | None = Field(default=None, max_length=MAX_NAME)
    basis: Literal["g", "ml"]
    values_per: Literal["100", "serving"]
    serving_g: float | None = Field(
        default=None, gt=0, le=5000, allow_inf_nan=False, description="Basis units per serving"
    )
    nutrients: CustomNutrientsIn
    density_g_per_ml: float | None = Field(
        default=None, ge=0.2, le=2.0, allow_inf_nan=False, description="Grams in one ml"
    )
    barcode: str | None = Field(default=None, max_length=64)
    portions: list[CustomPortionIn] = Field(default_factory=list, max_length=MAX_PORTIONS)
    client_id: UUID | None = None

    @field_validator("name", "brand", mode="before")
    @classmethod
    def _trimmed(cls, value: object) -> object:
        return _trim(value)

    @model_validator(mode="after")
    def _valid(self) -> "CustomFoodIn":
        if not self.name:
            raise ApiError("validation_error", 422, details={"fields": ["body.name"]})
        if self.brand == "":
            self.brand = None
        if self.values_per == "serving" and self.serving_g is None:
            raise ApiError("validation_error", 422, details={"fields": ["body.serving_g"]})
        units = [p.unit for p in self.portions]
        if len(set(units)) != len(units):
            raise ApiError("validation_error", 422, details={"fields": ["body.portions"]})
        return self


class EnteredOut(BaseModel):
    values_per: Literal["100", "serving"]
    serving_g: float | None
    nutrients: CustomNutrientsIn


class CustomPortionOut(BaseModel):
    unit: str
    grams_per_unit: float


class CustomFoodOut(BaseModel):
    """Not redacted by the numbers display: it is the label the user typed and needs it to
    edit (G15)."""

    id: UUID
    name: str
    brand: str | None
    basis: Literal["g", "ml"]
    per_100: NutrientSnapshot = Field(
        description="Per 100 g (or 100 ml), unrounded; null = unknown"
    )
    entered: EnteredOut = Field(description="The values as typed")
    serving_g: float | None
    density_g_per_ml: float | None
    barcode: str | None
    portions: list[CustomPortionOut]
    created_at: datetime
    updated_at: datetime


class CustomFoodsOut(BaseModel):
    items: list[CustomFoodOut]
    next_cursor: str | None = Field(description="Opaque; pass back as `cursor` for the next page")
