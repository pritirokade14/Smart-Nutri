"""API shapes of the diary day, week, partial-day status and recents (Plan 11 Task 5).

Everything here is computed by the API; clients render it and never compute a total, a
remaining value, a progress fraction, a local date or a default slot. Hidden numbers (Q7) are
null here, never 0.
"""

from datetime import date
from typing import Literal
from uuid import UUID

from pydantic import AwareDatetime, BaseModel, Field

from app.features.meals.schemas import (
    IncompleteNutrients,
    MealOut,
    NutrientBands,
    Totals,
)
from app.features.products.schemas import NutriScoreGrade
from app.features.targets.schemas import NumbersHidden, TargetsOut

TargetsStatusOut = Literal[
    "ready",
    "none",
    "needs_body_data",
    "not_available_minor",
    "paused_pregnancy",
    "consent_required",
]


class Macro4(BaseModel):
    """Energy and the three macros a daily guide covers. null per field: not available."""

    energy_kcal: float | None
    protein_g: float | None
    fat_g: float | None
    carbs_g: float | None


class SlotDayOut(BaseModel):
    slot_id: UUID
    label_key: str | None = Field(description="i18n key of a default slot's name")
    custom_label: str | None = Field(description="User text: shown as typed, never translated")
    position: int
    archived: bool
    entries: list[MealOut]
    totals: Totals
    incomplete: IncompleteNutrients


class DiaryDayOut(BaseModel):
    member_id: UUID
    date: date
    today: date = Field(description="The account's local today; clients never work out dates")
    timezone: str
    slots: list[SlotDayOut] = Field(
        description=(
            "The member's active slots in position order, plus an archived slot only on a day "
            "that has entries in it"
        )
    )
    totals: Totals
    incomplete: IncompleteNutrients
    targets: TargetsOut | None = Field(
        description="That day's frozen targets; null when `targets_status` is consent_required"
    )
    targets_status: TargetsStatusOut
    remaining: Macro4 | None = Field(
        description=(
            "target - eaten, 1 dp; negative means over. null as a whole unless the day's "
            "targets are `ready`. A field is null when that nutrient is incomplete (a total "
            "with an unknown value is a lower bound) or hidden. With nothing logged it equals "
            "the target"
        )
    )
    progress: Macro4 | None = Field(
        description=(
            "eaten / target, 2 dp (0 with nothing logged); same null rules as `remaining`. A "
            "hidden value is rounded to the nearest 0.25: the ring shape only"
        )
    )
    limits_bands: NutrientBands
    partial_logged: bool
    numbers_hidden: NumbersHidden
    pending_clinician_review: Literal[True] = True


class DayTileTargets(BaseModel):
    energy_kcal: int | None
    protein_g: int | None


class DayTile(BaseModel):
    date: date
    items: int
    totals: Totals
    incomplete: IncompleteNutrients
    targets: DayTileTargets | None = Field(
        description="That day's frozen energy and protein targets; null without a ready target"
    )
    progress: Macro4 | None
    partial_logged: bool
    bands: NutrientBands


class DiaryWeekOut(BaseModel):
    member_id: UUID
    start: date
    end: date
    today: date
    days: list[DayTile] = Field(description="7 days, oldest first")
    averages: Macro4 = Field(
        description=(
            "Per averaged day, 1 dp. Averaged days are those with items that are not marked "
            "partial; null when there are none"
        )
    )
    averages_incomplete: IncompleteNutrients = Field(
        description="true for a nutrient unknown on any averaged day: its average is a lower bound"
    )
    averaged_days: int
    protein_met_days: int = Field(
        description="Averaged days whose frozen protein target is ready and was met"
    )
    numbers_hidden: NumbersHidden
    pending_clinician_review: Literal[True] = True


class DiaryDayStatusIn(BaseModel):
    member_id: UUID | None = None
    partial_logged: bool


class DiaryDayStatusOut(BaseModel):
    date: date
    partial_logged: bool


class RecentItem(BaseModel):
    source_kind: Literal["product", "off", "food"]
    product_id: UUID | None
    barcode: str | None
    food_id: UUID | None = Field(
        default=None, description="A generic food or dish; log it again with `food_id`"
    )
    name: str
    grade: NutriScoreGrade | None
    grams: float
    quantity: float | None = Field(
        default=None, description="The portion as last logged, with `unit`; null for older entries"
    )
    unit: str | None = None
    meal_slot_id: UUID
    last_eaten_at: AwareDatetime
    attribution: str | None
    attributions: list[str] = Field(default_factory=list)


class RecentsOut(BaseModel):
    items: list[RecentItem]
