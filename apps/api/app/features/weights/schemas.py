"""Weight log API schemas (Plan 12 Task 23; spec 6.5, 6.6; rulings G24-G28).

Weights are health data. Under `hide_all` every kg, the weekly rate and the target are `null`
(`numbers_hidden` true): the chart keeps its shape through `y`, never through numbers.
"""

import datetime as dt
from typing import Literal
from uuid import UUID

from pydantic import AwareDatetime, BaseModel, ConfigDict, Field

ProjectionReasonOut = Literal[
    "ready", "too_few_weigh_ins", "moving_away", "no_target", "too_far", "reached"
]


class WeightIn(BaseModel):
    """`weight_kg` is checked by the service (2 to 300, else 422 `weight_out_of_range`) and kept
    to 2 dp. A value outside 30 to 200, or far from the last weigh-in, needs `confirm_unusual`."""

    member_id: UUID | None = None
    weight_kg: float
    confirm_unusual: bool = False
    client_id: UUID | None = None


class WeightOut(BaseModel):
    date: dt.date
    weight_kg: float | None
    measured_at: AwareDatetime
    source: Literal["manual"]
    client_id: UUID | None
    numbers_hidden: bool


class WeightsOut(BaseModel):
    items: list[WeightOut]
    numbers_hidden: bool


class WeightPointOut(BaseModel):
    date: dt.date
    weight_kg: float | None
    outlier: bool
    y: float | None


class TrendPointOut(BaseModel):
    date: dt.date
    trend_kg: float | None
    y: float | None


class WeeklyRateOut(BaseModel):
    kg: float
    pct_bw: float


class ProjectionOut(BaseModel):
    target_kg: float | None
    date: dt.date | None


class WeightTrendOut(BaseModel):
    member_id: UUID
    days: Literal[30, 90, 365]
    from_: dt.date = Field(alias="from")
    to: dt.date
    points: list[WeightPointOut]
    trend: list[TrendPointOut]
    weekly_rate: WeeklyRateOut | None
    projection: ProjectionOut | None
    projection_reason: ProjectionReasonOut
    flags: list[Literal["rapid_loss"]]
    numbers_hidden: bool
    pending_clinician_review: Literal[True] = True

    model_config = ConfigDict(populate_by_name=True)
