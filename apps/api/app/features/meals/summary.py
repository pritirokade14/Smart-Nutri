"""Daily and weekly nutrient summaries (pure; no I/O).

Missing stays missing: a meal whose snapshot has no value for a nutrient adds nothing to the
total and marks that nutrient ``incomplete``; when NO meal has a value the total is null, never
0.0. The total is then a lower bound, so its band is ``unknown`` unless the lower bound alone is
already over the limit. Nothing logged is ``unknown``, never "fine".

Ruling M1 (nutrition-safety review):
- The period band compares the total with the daily limit x the number of days with logged
  items (empty days are not "under the limit"), and is ``over`` whenever any day is ``over``.
- Protein is a target, not a limit: ``ok`` once the (lower-bound) total meets it, otherwise
  ``unknown`` (no band; clients show "x g of a y g target").
- ``protein_left_g`` (Plan 9 Task 6): for a day only, the target minus the protein eaten, never
  below 0. Null without a target or when the day's protein is incomplete (the total is only a
  lower bound, so "left" would be over-stated); nothing logged leaves the whole target.

Bands come from the engine's ``nutrient_band`` and daily limits from ``app.scoring``
(thresholds.yaml, pending clinician review); clients only render them.
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
    NutrientBand,
    NutrientBands,
    Summary,
    SummaryPeriod,
    Totals,
)
from app.features.targets.schemas import NumbersHidden
from app.scoring import DailyLimits, nutrient_band
from app.scoring.config import ScoringConfig

NUTRIENTS = ("energy_kcal", "sugars_g", "salt_g", "protein_g")
PERIOD_DAYS = {"day": 1, "week": 7}


def _round1(value: float) -> float:
    return float(Decimal(repr(value)).quantize(Decimal("0.1"), rounding=ROUND_HALF_UP))


def _limit_band(
    total: float | None,
    limit: float | None,
    incomplete: bool,
    items: int,
    cfg: ScoringConfig | None,
) -> Band:
    if items == 0 or total is None:
        return "unknown"
    band = nutrient_band(total, limit, cfg)
    if incomplete and band != "over":
        return "unknown"
    return band


def _target_band(total: float | None, target: float | None, items: int) -> Band:
    """A target, not a limit: met (even by a lower bound) is ``ok``; anything else has no band
    (``unknown``), never ``near`` or ``ok`` far below it (Ruling M1 S2)."""
    if items == 0 or total is None or target is None:
        return "unknown"
    return "ok" if total >= target else "unknown"


def _bands(
    totals: dict[str, float | None],
    incomplete: dict[str, bool],
    items: int,
    limits: DailyLimits,
    factor: int,
    cfg: ScoringConfig | None,
) -> dict[str, Band]:
    """Bands against the daily limits x ``factor`` (1 for a day; days with logged items for a
    period)."""

    def times(v: float | None) -> float | None:
        return None if v is None else v * factor

    return {
        "sugar_g": _limit_band(
            totals["sugars_g"], times(limits.sugar_g), incomplete["sugars_g"], items, cfg
        ),
        "salt_g": _limit_band(
            totals["salt_g"], times(limits.salt_g), incomplete["salt_g"], items, cfg
        ),
        "protein_g": _target_band(totals["protein_g"], times(limits.protein_target_g), items),
        "kcal": "unknown",  # no personal energy target in v1
    }


def _period_bands(
    whole: "_Acc", days: Sequence[DaySummary], limits: DailyLimits, cfg: ScoringConfig | None
) -> dict[str, Band]:
    """Ruling M1 B1: limit x days with logged items, and ``over`` if any day is ``over``."""
    logged_days = sum(1 for d in days if d.items > 0)
    bands = _bands(whole.raw_totals(), whole.incomplete, whole.items, limits, logged_days, cfg)
    for key in ("sugar_g", "salt_g"):
        if any(getattr(d.bands, key) == NutrientBand.OVER for d in days):
            bands[key] = "over"
    return bands


class _Acc:
    def __init__(self) -> None:
        # Decimal sums of the stored values: exact, so 0.1 + 16.1 + 8.8 is 25, not 25.000…04.
        self.sums = dict.fromkeys(NUTRIENTS, Decimal(0))
        self.known = dict.fromkeys(NUTRIENTS, 0)  # meals with a value, per nutrient
        self.incomplete = dict.fromkeys(NUTRIENTS, False)
        self.items = 0

    def add(self, nutrients: dict[str, Any]) -> None:
        self.items += 1
        for k in NUTRIENTS:
            value = nutrients.get(k)
            if value is None:
                self.incomplete[k] = True
            else:
                self.sums[k] += Decimal(repr(float(value)))
                self.known[k] += 1

    def merge(self, other: "_Acc") -> None:
        self.items += other.items
        for k in NUTRIENTS:
            self.sums[k] += other.sums[k]
            self.known[k] += other.known[k]
            self.incomplete[k] = self.incomplete[k] or other.incomplete[k]

    def raw_totals(self) -> dict[str, float | None]:
        """Unrounded sums, used for the bands (cleanup c1: 25.04 g is over a 25 g limit even
        though it displays as 25.0 g); None when no meal had a value."""
        return {k: float(v) if self.known[k] else None for k, v in self.sums.items()}

    def totals(self) -> dict[str, float | None]:
        """Rounded sums for display; None when no meal had a value (Ruling M1 S1: never 0.0)."""
        return {k: None if v is None else _round1(v) for k, v in self.raw_totals().items()}


def _protein_left(acc: "_Acc", target: float | None) -> float | None:
    if target is None or acc.incomplete["protein_g"]:
        return None
    eaten = acc.raw_totals()["protein_g"] or 0.0  # None here only when nothing was logged
    return _round1(max(0.0, target - eaten))


def annotate_protein(summary: Summary, basis: str | None, status: str | None) -> Summary:
    """Record on ``summary.limits`` which weight the protein target used and the daily-targets
    status (null = the legacy rule). Returns the same summary, for the endpoint and the
    fixture generator to share."""
    summary.limits.protein_basis = basis  # type: ignore[assignment]
    summary.limits.protein_target_status = status  # type: ignore[assignment]
    return summary


def redact(summary: Summary, hidden: NumbersHidden) -> Summary:
    """The summary with the numbers the user hid set to null (Plan 10, Ruling D11). Pure: the
    input is not changed. Bands and ``incomplete`` are untouched, and the result says what was
    hidden in ``numbers_hidden``.

    - ``energy``: ``totals.energy_kcal`` and every day's ``energy_kcal``.
    - ``macros``: every total (all four nutrients, the period and each day), the protein
      target, its g/kg and ``protein_left_g``.
    """
    out = summary.model_copy(deep=True)
    out.numbers_hidden = hidden.model_copy()
    if not (hidden.energy or hidden.macros):
        return out
    groups = [out.totals, *(d.totals for d in out.days)]
    for totals in groups:
        if hidden.energy:
            totals.energy_kcal = None
        if hidden.macros:
            totals.energy_kcal = totals.sugars_g = totals.salt_g = totals.protein_g = None
    if hidden.macros:
        out.limits.protein_target_g = None
        out.limits.protein_g_per_kg = None
        out.protein_left_g = None
    return out


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
    oldest first, one entry per day (an empty day has null totals). Meals outside the period
    are ignored. Day bands compare with the daily limit; the period band with the daily limit
    x the days with logged items, and is ``over`` if any day is (Ruling M1 B1).
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
        raw = acc.raw_totals()
        days.append(
            DaySummary(
                date=day,
                totals=Totals(**acc.totals()),
                items=acc.items,
                incomplete=IncompleteNutrients(**acc.incomplete),
                bands=NutrientBands(**_bands(raw, acc.incomplete, acc.items, limits, 1, cfg)),
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
            protein_g_per_kg=limits.protein_g_per_kg,
        ),
        bands=NutrientBands(**_period_bands(whole, days, limits, cfg)),
        days=days,
        protein_left_g=_protein_left(whole, protein) if period == "day" else None,
    )
