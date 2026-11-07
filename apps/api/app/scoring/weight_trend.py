"""Pure weight-trend maths (Plan 12 Task 22, rulings G24-G28).

No I/O. Constants come from targets.yaml (`trend`, `projection`, `safety`, `goal_rates.taper`,
`plausible`), PENDING CLINICIAN REVIEW. Read by the weights feature and the daily-guide
service only; the verdict rules and the analyze service never import this module.

The trend is a time-aware exponential average on calendar days (`alpha_per_day`). A weigh-in
more than `outlier_pct_from_trend` from the trend is an outlier: kept for display, left out
of the trend. A second out-of-band weigh-in in a row on the same side is a real change, and
both are then accepted.
"""

from __future__ import annotations

import math
from collections.abc import Sequence
from dataclasses import dataclass
from datetime import date, timedelta
from decimal import ROUND_HALF_UP, Decimal
from typing import Literal

from app.scoring.config import ScoringConfig, load_config

_HUNDRED = Decimal(100)
_ZERO = Decimal(0)

ProjectionReason = Literal[
    "ready", "too_few_weigh_ins", "moving_away", "no_target", "too_far", "reached"
]


@dataclass(frozen=True, slots=True)
class WeighIn:
    day: date
    kg: Decimal


@dataclass(frozen=True, slots=True)
class TrendPoint:
    day: date
    kg: Decimal
    outlier: bool


@dataclass(frozen=True, slots=True)
class TrendResult:
    points: tuple[TrendPoint, ...]  # every weigh-in, oldest first
    trend: tuple[tuple[date, Decimal], ...]  # one per non-outlier weigh-in date (unrounded)

    def at(self, day: date) -> Decimal | None:
        """Trend at the latest non-outlier weigh-in on or before ``day``."""
        found: Decimal | None = None
        for d, t in self.trend:
            if d > day:
                break
            found = t
        return found

    def count_until(self, day: date) -> int:
        return sum(1 for d, _ in self.trend if d <= day)


def _d(x: object) -> Decimal:
    return x if isinstance(x, Decimal) else Decimal(str(x))


def _cfg(cfg: ScoringConfig | None) -> ScoringConfig:
    return cfg if cfg is not None else load_config()


def _sign(x: Decimal) -> int:
    return (x > 0) - (x < 0)


def compute_trend(weigh_ins: Sequence[WeighIn], cfg: ScoringConfig | None = None) -> TrendResult:
    t = _cfg(cfg).targets["trend"]
    alpha = _d(t["alpha_per_day"])
    band = _d(t["outlier_pct_from_trend"])
    ordered = sorted(weigh_ins, key=lambda w: w.day)

    outlier: dict[int, bool] = {}
    accepted: list[tuple[int, Decimal]] = []  # (index into ordered, trend after it)
    level: Decimal | None = None
    last_day: date | None = None
    pending: int | None = None

    def step(idx: int) -> None:
        nonlocal level, last_day
        w = ordered[idx]
        assert level is not None and last_day is not None
        gap = max(1, (w.day - last_day).days)
        level = level + (1 - (1 - alpha) ** gap) * (w.kg - level)
        last_day = w.day
        accepted.append((idx, level))
        outlier[idx] = False

    for i, w in enumerate(ordered):
        if level is None:
            level, last_day = w.kg, w.day
            accepted.append((i, level))
            outlier[i] = False
            continue
        out = abs(w.kg - level) / level * _HUNDRED > band
        if not out:
            pending = None
            step(i)
        elif pending is not None and _sign(w.kg - level) == _sign(ordered[pending].kg - level):
            step(pending)  # a real change: both are accepted
            step(i)
            pending = None
        else:
            outlier[i] = True
            pending = i

    points = tuple(TrendPoint(w.day, w.kg, outlier[i]) for i, w in enumerate(ordered))
    trend = tuple((ordered[i].day, v) for i, v in accepted)
    return TrendResult(points, trend)


def weight_for_targets(
    weigh_ins: Sequence[WeighIn], day: date, cfg: ScoringConfig | None = None
) -> Decimal | None:
    """Trend on ``day`` with at least `min_weigh_ins_for_trend` non-outliers up to it, else None."""
    c = _cfg(cfg)
    result = compute_trend([w for w in weigh_ins if w.day <= day], c)
    if result.count_until(day) < int(c.targets["trend"]["min_weigh_ins_for_trend"]):
        return None
    return result.at(day)


def _rate(result: TrendResult, end: date, c: ScoringConfig) -> tuple[Decimal, Decimal] | None:
    t = c.targets["trend"]
    if result.count_until(end) < int(t["min_weigh_ins_for_rate"]):
        return None
    now = result.at(end)
    before = result.at(end - timedelta(days=int(t["rate_window_days"])))
    if now is None or before is None:
        return None
    kg = now - before
    return kg, kg / now * _HUNDRED


def _last(result: TrendResult) -> date | None:
    return result.trend[-1][0] if result.trend else None


def weekly_rate(
    result: TrendResult, cfg: ScoringConfig | None = None, *, end: date | None = None
) -> tuple[Decimal, Decimal] | None:
    """(kg, % of T(end)) for the window ending at ``end`` (default: the latest non-outlier)."""
    end = end or _last(result)
    if end is None:
        return None
    return _rate(result, end, _cfg(cfg))


def rapid_loss(result: TrendResult, cfg: ScoringConfig | None = None) -> bool:
    c = _cfg(cfg)
    last = _last(result)
    if last is None:
        return False
    limit = -_d(c.targets["safety"]["rapid_loss_pct_bw_per_week"])
    window = int(c.targets["trend"]["rate_window_days"])
    for i in range(int(c.targets["safety"]["rapid_loss_weeks"])):
        r = _rate(result, last - timedelta(days=window * i), c)
        if r is None or r[1] > limit:
            return False
    return True


def projection(
    result: TrendResult, target_kg: Decimal | None, cfg: ScoringConfig | None = None
) -> tuple[ProjectionReason, date | None]:
    c = _cfg(cfg)
    last = _last(result)
    if target_kg is None:
        return "no_target", None
    if last is None:
        return "too_few_weigh_ins", None
    now = result.at(last)
    assert now is not None
    if abs(now - target_kg) <= _d(c.targets["goal_rates"]["taper"]["maintenance_band_kg"]):
        return "reached", None
    p = c.targets["projection"]
    span = (last - result.trend[0][0]).days
    if len(result.trend) < int(p["min_weigh_ins"]) or span < int(p["min_span_days"]):
        return "too_few_weigh_ins", None
    rate = _rate(result, last, c)
    gap = target_kg - now
    if rate is None or rate[0] == 0 or _sign(rate[0]) != _sign(gap):
        return "moving_away", None
    days = math.ceil(gap / (rate[0] / _d(c.targets["trend"]["rate_window_days"])))
    if days > int(p["max_horizon_days"]):
        return "too_far", None
    return "ready", last + timedelta(days=days)


def max_change_kg_per_day(cfg: ScoringConfig | None = None) -> Decimal:
    """Largest plausible change between two weigh-ins per day, before the API asks to confirm."""
    return _d(_cfg(cfg).targets["plausible"]["weight_change_kg_per_day"])


def shape(values: Sequence[Decimal | None]) -> list[Decimal | None]:
    """(v - min) / (max - min), 2 dp half-up; all equal -> 0.5; None stays None."""
    present = [v for v in values if v is not None]
    if not present:
        return [None for _ in values]
    lo, hi = min(present), max(present)
    out: list[Decimal | None] = []
    for v in values:
        if v is None:
            out.append(None)
        elif hi == lo:
            out.append(Decimal("0.50"))
        else:
            out.append(((v - lo) / (hi - lo)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP))
    return out
