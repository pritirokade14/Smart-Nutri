from datetime import date
from enum import StrEnum
from typing import Literal
from uuid import UUID

from pydantic import AwareDatetime, BaseModel, Field, model_validator

from app.core.errors import ApiError
from app.features.products.schemas import NutriScoreGrade

MAX_GRAMS = 5000.0  # meal_logs check: 0 < grams <= 5000
MAX_SERVINGS = 200.0

Band = Literal["ok", "near", "over", "unknown"]


class MealIn(BaseModel):
    """Log what a member ate. Exactly one product reference (own ``product_id``, or a
    ``barcode`` for Open Food Facts products) and exactly one portion (``grams`` or
    ``servings``; servings need the product's serving size).

    ``client_id`` makes the call idempotent: posting the same id again (an offline retry)
    returns the stored log with 200 and never creates a second row.
    """

    member_id: UUID
    product_id: UUID | None = None
    barcode: str | None = Field(default=None, max_length=64)
    grams: float | None = Field(default=None, gt=0, le=MAX_GRAMS)
    servings: float | None = Field(default=None, gt=0, le=MAX_SERVINGS)
    eaten_at: AwareDatetime | None = Field(
        default=None,
        description="Timezone-aware. Default: now. At most 5 minutes ahead, at most 30 days ago.",
    )
    client_id: UUID | None = None

    @model_validator(mode="after")
    def _exactly_one(self) -> "MealIn":
        if (self.product_id is None) == (self.barcode is None):
            raise ApiError("invalid_product_ref", 422)
        if (self.grams is None) == (self.servings is None):
            raise ApiError("portion_required", 422)
        return self


class NutrientSnapshot(BaseModel):
    """Nutrients in the portion eaten (per_100g x grams / 100, 1 dp). null = not on the label
    (never counted as 0)."""

    energy_kcal: float | None
    sugars_g: float | None
    salt_g: float | None
    protein_g: float | None
    fat_g: float | None
    sat_fat_g: float | None
    carbs_g: float | None


class MealOut(BaseModel):
    id: UUID
    member_id: UUID
    product_id: UUID | None = Field(description="Our own product; null for Open Food Facts")
    barcode: str | None = Field(description="Open Food Facts barcode; null for our products")
    product_name: str
    grade: NutriScoreGrade | None = Field(
        description="Nutri-Score calculated by SmartNutri at log time; null if not enough data"
    )
    grams: float
    eaten_at: AwareDatetime
    nutrients: NutrientSnapshot
    client_id: UUID | None
    attribution: str | None = Field(
        description='"attribution.off" for Open Food Facts products (credit OFF), else null'
    )


# --- summaries (Plan 6 T4) ---------------------------------------------------------------


class Totals(BaseModel):
    """Sums of the KNOWN values only; see ``Summary.incomplete``. null when no meal in the
    period has a value for that nutrient (also when nothing was logged): never shown as 0."""

    energy_kcal: float | None
    sugars_g: float | None
    salt_g: float | None
    protein_g: float | None


class SummaryPeriod(StrEnum):
    DAY = "day"
    WEEK = "week"


class NutrientBand(StrEnum):
    """Where a total stands against a limit. Never shown green unless ``ok``; ``unknown`` is
    never green on any client."""

    OK = "ok"
    NEAR = "near"
    OVER = "over"
    UNKNOWN = "unknown"


class IncompleteNutrients(BaseModel):
    """Per nutrient (Totals keys): true when a meal had no value for it. The total then counts
    only the known meals and is a lower bound."""

    energy_kcal: bool
    sugars_g: bool
    salt_g: bool
    protein_g: bool


class DailyLimitsOut(BaseModel):
    """Per DAY, from the rules engine (thresholds.yaml, pending clinician review)."""

    sugar_g: float | None
    salt_g: float | None
    protein_target_g: float | None = Field(
        description=(
            "A target, not a limit. Adults (18+) with a weight only; null for children, "
            "adolescents, an unknown age or no weight"
        )
    )
    kcal: float | None = Field(description="Always null in v1 (no personal energy target)")


class NutrientBands(BaseModel):
    """day: total vs the daily limit. week: total vs the daily limit x the days with logged
    items, and ``over`` whenever any day is ``over``. ``unknown`` when the limit is unknown
    (``kcal`` always), when nothing was logged, when the total is null, or when the total is
    incomplete and not already over.

    ``protein_g`` is a target: ``ok`` once met, otherwise ``unknown`` (no band; never ``near``
    or ``over``). Below the target, show the total against ``limits.protein_target_g``."""

    sugar_g: NutrientBand
    salt_g: NutrientBand
    protein_g: NutrientBand
    kcal: NutrientBand


class DaySummary(BaseModel):
    date: date
    totals: Totals
    items: int
    incomplete: IncompleteNutrients
    bands: NutrientBands = Field(description="That day's totals vs the DAILY limits")


class Summary(BaseModel):
    member_id: UUID
    period: SummaryPeriod
    start: date
    end: date
    totals: Totals
    incomplete: IncompleteNutrients
    limits: DailyLimitsOut
    bands: NutrientBands
    days: list[DaySummary] = Field(description="1 for day, 7 for week (oldest first)")
    pending_clinician_review: bool = True


class WeekCounts(BaseModel):
    """Account-wide counts for the weekly share text. Counts only, no health data."""

    start: date
    end: date
    scans: int = Field(description="Products checked (analyses) in the 7 IST days")
    logged: int = Field(description="Meal logs in the 7 IST days, all members")
