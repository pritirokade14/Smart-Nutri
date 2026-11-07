"""Daily-targets API schemas (Plan 10 Task 4; spec 6.1, Rulings D3-D5, D11, D12).

Targets are information the API computes; the clients render them and never compute a target,
a rate in kg, a remaining value or a flag. Numbers the user chose to hide arrive as `null`
with `numbers_hidden`, never as 0.
"""

import datetime as dt
from typing import Annotated, Literal
from uuid import UUID

from pydantic import AwareDatetime, BaseModel, Field

from app.features.members.schemas import BirthYear, HeightCm, Sex, WeightKg
from app.scoring.targets import ActivityLevel, Direction, ProteinBasis, SexReference

NumbersDisplay = Literal["show", "hide_energy", "hide_all"]
SummaryView = Literal["remaining", "consumed"]
TargetsStatusOut = Literal[
    "ready", "needs_body_data", "not_available_minor", "paused_pregnancy", "none"
]


class NumbersHidden(BaseModel):
    """Which groups of numbers the user hid (also on the meals summary, Plan 10 Task 5)."""

    energy: bool
    macros: bool


class GoalSettingsIn(BaseModel):
    """Spec 6.1. `member_id` is optional (the primary). `rate_pct_bw_per_week` must be one of
    the YAML options for the direction and is null for `maintain`; omitted means the default."""

    member_id: UUID | None = None
    direction: Direction
    activity_level: ActivityLevel
    rate_pct_bw_per_week: float | None = None
    target_weight_kg: Annotated[float, Field(ge=2, le=300)] | None = None
    sex_reference: SexReference | None = None
    pregnant_or_breastfeeding: bool
    fat_pct_energy: float | None = None
    energy_mode: Literal["formula", "adaptive"] = "formula"
    numbers_display: NumbersDisplay = "show"
    summary_view: SummaryView = "remaining"


class GoalSettingsOut(GoalSettingsIn):
    member_id: UUID
    updated_at: AwareDatetime


class BodyDataIn(BaseModel):
    """Unsaved body data for a preview. A field that is SENT (even as null) overrides the
    stored one; a field left out keeps the stored value."""

    birth_year: BirthYear | None = None
    sex: Sex | None = None
    height_cm: HeightCm | None = None
    weight_kg: WeightKg | None = None
    body_fat_pct: float | None = None


class TargetsPreviewIn(GoalSettingsIn):
    body: BodyDataIn | None = None


class DisplayIn(BaseModel):
    """The eye toggle (Ruling D4): only these two fields change; null means unchanged."""

    member_id: UUID | None = None
    numbers_display: NumbersDisplay | None = None
    summary_view: SummaryView | None = None


class DisplayOut(BaseModel):
    """What `PUT /display` returns: only the display fields. It needs only `terms`, so it must
    never carry the pregnancy answer, the target weight or the direction."""

    member_id: UUID
    numbers_display: NumbersDisplay
    summary_view: SummaryView
    updated_at: AwareDatetime


class RateOut(BaseModel):
    """Unsigned (`direction` carries the sign), 2 dp (Ruling D12). `kg_per_week` is null under
    `hide_all`: the pace shows as a percent only, so the body weight can't be worked out."""

    pct_bw_per_week: float
    kg_per_week: float | None


class TargetsExplanation(BaseModel):
    """ "How we got this". Kcal values are whole kcal, weights 1 dp (Ruling D12). Numbers are
    null when hidden (Ruling D11); `protein_basis` is never hidden."""

    bmr_kcal: int | None
    activity_factor: float | None
    maintenance_kcal: int | None
    adjustment_kcal: int | None
    weight_kg_used: float | None
    protein_basis: ProteinBasis
    protein_g_per_kg: float | None
    protein_reference_weight_kg: float | None
    body_fat_pct_used: float | None
    ibw_kg: float | None
    floor_kcal: int | None


class TargetsOut(BaseModel):
    """Spec 6.1 plus `rate_options` and `unusual_fields` (Ruling D5)."""

    member_id: UUID
    date: dt.date
    status: TargetsStatusOut
    missing_fields: list[str]
    energy_kcal: int | None
    protein_g: int | None
    fat_g: int | None
    carbs_g: int | None
    basis: Literal["formula", "adaptive"] | None
    direction: Direction | None
    rate: RateOut | None
    rate_options: list[RateOut]
    explanation: TargetsExplanation | None
    flags: list[str]
    unusual_fields: list[str]
    numbers_hidden: NumbersHidden
    sources: list[str]
    pending_clinician_review: Literal[True] = True
