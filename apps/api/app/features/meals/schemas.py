from datetime import date
from enum import StrEnum
from typing import Literal
from uuid import UUID

from pydantic import AwareDatetime, BaseModel, Field, field_validator, model_validator

from app.core.errors import ApiError
from app.features.products.schemas import NutriScoreGrade
from app.features.targets.schemas import NumbersHidden
from app.scoring.targets import ProteinBasis, TargetsStatus

MAX_GRAMS = 5000.0  # meal_logs check: 0 < grams <= 5000
MAX_SERVINGS = 200.0

Band = Literal["ok", "near", "over", "unknown"]


SourceKind = Literal["product", "off", "quick_add"]


def _validation_error(*fields: str) -> ApiError:
    return ApiError("validation_error", 422, details={"fields": [f"body.{f}" for f in fields]})


class QuickIn(BaseModel):
    """A quick add (Plan 11 Ruling E11): kcal and optional macros the person typed. A blank
    stays null (never 0), so the entry is incomplete for it. ``name`` is user text: stored
    trimmed, never sent to analytics, logs or prompts."""

    name: str | None = Field(default=None, max_length=60)
    energy_kcal: float | None = Field(default=None, gt=0, le=5000)
    protein_g: float | None = Field(default=None, ge=0, le=500)
    fat_g: float | None = Field(default=None, ge=0, le=500)
    carbs_g: float | None = Field(default=None, ge=0, le=500)
    fibre_g: float | None = Field(default=None, ge=0, le=200)

    @field_validator("name", mode="before")
    @classmethod
    def _trim(cls, value: object) -> object:
        if isinstance(value, str):
            return value.strip() or None
        return value


class MealIn(BaseModel):
    """Log what a member ate. Exactly one food reference (own ``product_id``, a ``barcode``
    for Open Food Facts products, or ``quick``) and, except for a quick add, exactly one
    portion (``grams`` or ``servings``; servings need the product's serving size).

    ``member_id`` defaults to the primary member. ``meal_slot_id`` defaults to the slot the
    server picks from the local time. ``local_date`` logs onto a past day (``eaten_at`` becomes
    that date at the current local clock time, capped at now); it cannot be sent together with
    ``eaten_at``.

    ``client_id`` makes the call idempotent: posting the same id again (an offline retry)
    returns the stored log with 200 and never creates a second row.
    """

    member_id: UUID | None = None
    product_id: UUID | None = None
    barcode: str | None = Field(default=None, max_length=64)
    quick: QuickIn | None = None
    grams: float | None = Field(default=None, gt=0, le=MAX_GRAMS)
    servings: float | None = Field(default=None, gt=0, le=MAX_SERVINGS)
    meal_slot_id: UUID | None = None
    local_date: date | None = Field(
        default=None, description="Log onto this local day (at most 30 days ago, not in future)."
    )
    eaten_at: AwareDatetime | None = Field(
        default=None,
        description="Timezone-aware. Default: now. At most 5 minutes ahead, at most 30 days ago.",
    )
    client_id: UUID | None = None

    @model_validator(mode="after")
    def _exactly_one(self) -> "MealIn":
        refs = sum(x is not None for x in (self.product_id, self.barcode, self.quick))
        if refs != 1:
            raise ApiError("invalid_product_ref", 422)
        if self.local_date is not None and self.eaten_at is not None:
            raise _validation_error("local_date", "eaten_at")
        if self.quick is not None:
            if self.grams is not None or self.servings is not None:
                raise _validation_error(*(f for f in ("grams", "servings") if getattr(self, f)))
            if self.quick.energy_kcal is None:
                raise ApiError("quick_add_energy_required", 422)
        elif (self.grams is None) == (self.servings is None):
            raise ApiError("portion_required", 422)
        return self


class MealPatch(BaseModel):
    """Edit an entry. ``null`` means unchanged (Ruling E10: the generated Dart client sends
    every unset field as null). At least one field must be set. ``quick`` is for quick-add
    entries only; the portion fields are for the others."""

    grams: float | None = Field(default=None, gt=0, le=MAX_GRAMS)
    servings: float | None = Field(default=None, gt=0, le=MAX_SERVINGS)
    meal_slot_id: UUID | None = None
    eaten_at: AwareDatetime | None = None
    quick: QuickIn | None = None

    @model_validator(mode="after")
    def _valid(self) -> "MealPatch":
        if self.grams is not None and self.servings is not None:
            raise _validation_error("grams", "servings")
        if all(
            v is None
            for v in (self.grams, self.servings, self.meal_slot_id, self.eaten_at, self.quick)
        ):
            raise _validation_error()
        if self.quick is not None and self.quick.energy_kcal is None:
            raise ApiError("quick_add_energy_required", 422)
        return self


class CopyIn(BaseModel):
    """Copy one meal (``from_slot_id``) or the whole day (no ``from_slot_id``) onto another day.

    ``client_id`` is required: each copy's own id is derived from it and the source entry, so a
    retry (a lost response, a double tap) returns the same rows and creates nothing. An entry
    whose slot has since been archived needs an explicit ``to_slot_id``.
    """

    member_id: UUID | None = None
    from_date: date
    from_slot_id: UUID | None = None
    to_date: date
    to_slot_id: UUID | None = None
    client_id: UUID


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
    fibre_g: float | None


class MealOut(BaseModel):
    id: UUID
    member_id: UUID
    product_id: UUID | None = Field(description="Our own product; null for Open Food Facts")
    barcode: str | None = Field(description="Open Food Facts barcode; null for our products")
    product_name: str = Field(
        description="The product name; the typed name (or empty) for a quick add"
    )
    grade: NutriScoreGrade | None = Field(
        description="Nutri-Score calculated by SmartNutri at log time; null if not enough data"
    )
    grams: float | None = Field(description="The portion in grams; null for a quick add")
    eaten_at: AwareDatetime
    nutrients: NutrientSnapshot
    client_id: UUID | None
    attribution: str | None = Field(
        description='"attribution.off" for Open Food Facts products (credit OFF), else null'
    )
    source_kind: SourceKind
    meal_slot_id: UUID
    local_date: date = Field(description="The day the entry belongs to, in the account's zone")
    incomplete: list[str] = Field(
        description="NutrientSnapshot keys that are unknown (null) on this entry, before hiding"
    )
    updated_at: AwareDatetime


class CopyOut(BaseModel):
    created: list[MealOut] = Field(description="The copies, in the order of their sources")


# --- summaries (Plan 6 T4) ---------------------------------------------------------------


class Totals(BaseModel):
    """Sums of the KNOWN values only; see ``Summary.incomplete``. null when no meal in the
    period has a value for that nutrient (also when nothing was logged): never shown as 0."""

    energy_kcal: float | None
    protein_g: float | None
    fat_g: float | None
    carbs_g: float | None
    fibre_g: float | None
    sugars_g: float | None
    salt_g: float | None


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
    protein_g: bool
    fat_g: bool
    carbs_g: bool
    fibre_g: bool
    sugars_g: bool
    salt_g: bool


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
    protein_g_per_kg: float | None = Field(
        description=(
            "The g per kg body weight per day the protein target was computed with (thresholds.yaml, "
            "pending clinician review), for the protein.guide copy. Null whenever "
            "protein_target_g is null. Display only; never compute a target on the client"
        )
    )
    protein_basis: ProteinBasis | None = Field(
        default=None,
        description=(
            "Which weight protein_g_per_kg applies to: lean_mass, adjusted_weight or "
            "actual_weight (the legacy weight x g/kg rule, whenever it gives a target). Null "
            "whenever protein_target_g is null. Display only (the protein.guide_* copy)"
        ),
    )
    protein_target_status: TargetsStatus | None = Field(
        default=None,
        description=(
            "null = the legacy rule applied (no goal settings, or health_data not active). "
            "Otherwise the daily-targets status; anything but `ready` means no protein target "
            "(not_available_minor, paused_pregnancy, needs_body_data)"
        ),
    )


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
    protein_left_g: float | None = Field(
        description=(
            "period=day only: max(0, limits.protein_target_g - totals.protein_g), 1 dp (the "
            "whole target when nothing is logged). Null when there is no target, when protein "
            "is incomplete for the day, or for period=week. A guide, not a need."
        )
    )
    numbers_hidden: NumbersHidden = Field(
        default_factory=lambda: NumbersHidden(energy=False, macros=False),
        description=(
            "What the member hid with the eye toggle (daily-targets settings). A hidden total "
            "is null here, never 0; bands and `incomplete` are unchanged"
        ),
    )
    pending_clinician_review: bool = True


class WeekCounts(BaseModel):
    """Account-wide counts for the weekly share text. Counts only, no health data."""

    start: date
    end: date
    scans: int = Field(description="Products checked (analyses) in the 7 IST days")
    logged: int = Field(description="Meal logs in the 7 IST days, all members")
