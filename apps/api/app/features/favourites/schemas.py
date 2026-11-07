"""Favourites schemas (Plan 12 Task 17; spec 5.10, 6.4).

A food favourite is a starred food with an optional default portion. A meal favourite is a
saved copy of one slot's entries on one day. Neither carries a nutrient value: the numbers
come from the diary entry created when it is logged (and are redacted there).

The meal name is user text: kept exactly as typed (no trimming, no case change), never sent to
analytics, logs or prompts, never translated.
"""

from datetime import date, datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, Field, field_validator, model_validator

from app.core.errors import ApiError
from app.features.foods.units import UnitCode
from app.features.meals.schemas import MAX_QUANTITY, MealOut

FavouriteKind = Literal["food", "meal"]
FavouriteSource = Literal["product", "off", "food", "custom_food", "recipe"]
ItemSource = Literal["product", "off", "food", "custom_food", "recipe", "quick_add"]
MEAL_NAME_MAX = 40  # code points


def _validation_error(*fields: str) -> ApiError:
    return ApiError("validation_error", 422, details={"fields": [f"body.{f}" for f in fields]})


class FavouriteIn(BaseModel):
    """Star a food. Exactly one reference: ``product_id``, ``barcode`` (Open Food Facts or
    your own product), ``food_id``, ``custom_food_id`` or ``recipe_id``. ``default_quantity``
    with ``default_unit`` is the portion one tap logs; both or neither. A unit that cannot be
    converted for this food is 422 ``unit_grams_unknown``."""

    member_id: UUID | None = None
    product_id: UUID | None = None
    barcode: str | None = Field(default=None, max_length=64)
    food_id: UUID | None = None
    custom_food_id: UUID | None = None
    recipe_id: UUID | None = None
    default_quantity: float | None = Field(default=None, gt=0, le=MAX_QUANTITY)
    default_unit: UnitCode | None = None

    @model_validator(mode="after")
    def _shape(self) -> "FavouriteIn":
        refs = (self.product_id, self.barcode, self.food_id, self.custom_food_id, self.recipe_id)
        if sum(x is not None for x in refs) != 1:
            raise ApiError("invalid_product_ref", 422)
        if (self.default_quantity is None) != (self.default_unit is None):
            raise _validation_error(
                "default_quantity" if self.default_quantity is None else "default_unit"
            )
        return self


class FavouriteMealIn(BaseModel):
    """Save the entries of one meal slot on one day as a named favourite meal. ``name`` is
    user text, 1 to 40 characters, kept exactly as typed."""

    member_id: UUID | None = None
    from_date: date
    from_slot_id: UUID
    name: str = Field(min_length=1, max_length=MEAL_NAME_MAX)
    client_id: UUID | None = None

    @field_validator("name")
    @classmethod
    def _not_blank(cls, value: str) -> str:
        if not value.strip():
            raise _validation_error("name")
        return value


class FavouriteLogIn(BaseModel):
    """Log a favourite meal again. ``client_id`` is required: each entry's own id is derived
    from it, so a retry returns the same rows with 200 and creates nothing."""

    meal_slot_id: UUID | None = Field(default=None, description="Default: the server's pick")
    local_date: date | None = Field(
        default=None, description="Log onto this local day (at most 30 days ago, not in future)."
    )
    client_id: UUID


class FavouriteItemOut(BaseModel):
    name: str | None
    quantity: float | None
    unit: str | None
    grams: float | None
    basis: Literal["g", "ml"] = Field(
        default="g", description="The unit of `grams`: grams or millilitres (an ml-basis food)"
    )
    source_kind: ItemSource
    attributions: list[str] = Field(default_factory=list)


class FavouriteOut(BaseModel):
    id: UUID
    member_id: UUID
    kind: FavouriteKind
    source_kind: FavouriteSource | None = Field(description="Null for a saved meal")
    product_id: UUID | None
    barcode: str | None
    food_id: UUID | None
    custom_food_id: UUID | None
    recipe_id: UUID | None
    name: str = Field(
        description="A food: its name when starred. A meal: the name you typed (user text)"
    )
    default_quantity: float | None
    default_unit: str | None
    item_count: int = Field(description="1 for a food, the number of saved entries for a meal")
    items: list[FavouriteItemOut] | None = Field(
        description="The saved entries of a meal as they were; null for a food"
    )
    attributions: list[str] = Field(default_factory=list)
    created_at: datetime


class FavouritesOut(BaseModel):
    items: list[FavouriteOut]


class FavouriteLogOut(BaseModel):
    created: list[MealOut] = Field(description="The new entries, in the saved order")
