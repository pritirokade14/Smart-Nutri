"""Daily and weekly nutrient summaries (pure; no I/O).

Missing stays missing: a meal whose snapshot has no value for a nutrient adds nothing to the
total and marks that nutrient ``incomplete``. The total is then a lower bound, so its band is
``unknown`` unless the lower bound alone is already over the limit (or, for the protein
target, already meets it). Nothing logged is ``unknown``, never "fine". Bands come from the
engine's ``nutrient_band`` and daily limits from ``app.scoring`` (thresholds.yaml, pending
clinician review); clients only render them.
"""

from collections.abc import Sequence
from datetime import date, timedelta, tzinfo
from decimal import ROUND_HALF_UP, Decimal
from typing import Any
from uuid import UUID

from app.features.meals.models import MealLog
from app.features.meals.schemas import (
    Band,
    DailyLimitsOut,
    DaySummary,
    IncompleteNutrients,
    NutrientBands,
    Summary,
    SummaryPeriod,
    Totals,
)
from app.scoring import DailyLimits, nutrient_band
from app.scoring.config import ScoringConfig

NUTRIENTS = ("energy_kcal", "sugars_g", "salt_g", "protein_g")
PERIOD_DAYS = {"day": 1, "week": 7}


def _round1(value: float) -> float:
    return float(Decimal(repr(value)).quantize(Decimal("0.1"), rounding=ROUND_HALF_UP))


def _limit_band(
    total: float, limit: float | None, incomplete: bool, items: int, cfg: ScoringConfig | None
) -> Band:
    if items == 0:
        return "unknown"
    band = nutrient_band(total, limit, cfg)
    if incomplete and band != "over":
        return "unknown"
    return band


def _target_band(
    total: float, target: float | None, incomplete: bool, items: int, cfg: ScoringConfig | None
) -> Band:
    """A target, not a limit: reaching it is ``ok`` (never ``over``)."""
    if items == 0 or target is None:
        return "unknown"
    band = nutrient_band(total, target, cfg)
    if band == "over":
        return "ok"
    if incomplete:
        return "unknown"  # the target may already be met by the meals with no value
    return band


def _bands(
    totals: dict[str, float],
    incomplete: dict[str, bool],
    items: int,
    limits: DailyLimits,
    factor: int,
    cfg: ScoringConfig | None,
) -> dict[str, Band]:
    def times(v: float | None) -> float | None:
        return None if v is None else v * factor

    return {
        "sugar_g": _limit_band(
            totals["sugars_g"], times(limits.sugar_g), incomplete["sugars_g"], items, cfg
        ),
        "salt_g": _limit_band(
            totals["salt_g"], times(limits.salt_g), incomplete["salt_g"], items, cfg
        ),
        "protein_g": _target_band(
            totals["protein_g"],
            times(limits.protein_target_g),
            incomplete["protein_g"],
            items,
            cfg,
        ),
        "kcal": "unknown",  # no personal energy target in v1
    }


class _Acc:
    def __init__(self) -> None:
        self.sums = dict.fromkeys(NUTRIENTS, 0.0)
        self.incomplete = dict.fromkeys(NUTRIENTS, False)
        self.items = 0

    def add(self, nutrients: dict[str, Any]) -> None:
        self.items += 1
        for k in NUTRIENTS:
            value = nutrients.get(k)
            if value is None:
                self.incomplete[k] = True
            else:
                self.sums[k] += float(value)

    def merge(self, other: "_Acc") -> None:
        self.items += other.items
        for k in NUTRIENTS:
            self.sums[k] += other.sums[k]
            self.incomplete[k] = self.incomplete[k] or other.incomplete[k]

    def totals(self) -> dict[str, float]:
        return {k: _round1(v) for k, v in self.sums.items()}


def summarise(
    meals: Sequence[MealLog],
    limits: DailyLimits,
    period: str,
    end_date: date,
    tz: tzinfo,
    cfg: ScoringConfig | None = None,
    *,
    member_id: UUID,
) -> Summary:
    """Totals, incompleteness and bands for the ``period`` ending on ``end_date``.

    Days are calendar days in ``tz`` (IST); a week is the 7 days ending on ``end_date``,
    oldest first, zero-filled. Meals outside the period are ignored. Day bands compare with
    the daily limit, the period band with limit x days.
    """
    if period not in PERIOD_DAYS:
        raise ValueError(f"unknown period: {period}")
    n_days = PERIOD_DAYS[period]
    start = end_date - timedelta(days=n_days - 1)
    per_day = {start + timedelta(days=i): _Acc() for i in range(n_days)}
    for m in meals:
        day = m.eaten_at.astimezone(tz).date()
        if day in per_day:
            per_day[day].add(m.nutrients or {})

    days: list[DaySummary] = []
    whole = _Acc()
    for day, acc in per_day.items():
        totals = acc.totals()
        days.append(
            DaySummary(
                date=day,
                totals=Totals(**totals),
                items=acc.items,
                incomplete=IncompleteNutrients(**acc.incomplete),
                bands=NutrientBands(**_bands(totals, acc.incomplete, acc.items, limits, 1, cfg)),
            )
        )
        whole.merge(acc)

    totals = whole.totals()
    protein = limits.protein_target_g
    return Summary(
        member_id=member_id,
        period=SummaryPeriod(period),
        start=start,
        end=end_date,
        totals=Totals(**totals),
        incomplete=IncompleteNutrients(**whole.incomplete),
        limits=DailyLimitsOut(
            sugar_g=limits.sugar_g,
            salt_g=limits.salt_g,
            protein_target_g=None if protein is None else _round1(protein),
            kcal=None,
        ),
        bands=NutrientBands(**_bands(totals, whole.incomplete, whole.items, limits, n_days, cfg)),
        days=days,
    )
