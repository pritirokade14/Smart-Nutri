"""Day and week aggregation for the diary (Plan 11 Task 5). Pure: no I/O.

Rules (Rulings E13, E14, E15, E16; spec 1.1 "unknown is never 0"):

- A total is the sum of the KNOWN values; a nutrient unknown on any entry is `incomplete` and
  the total is a lower bound. Nothing logged leaves the total null, never 0.
- `remaining = target - eaten` (1 dp half-up; negative means over) is null as a whole unless the
  day's target is `ready`, and null per nutrient when that nutrient is incomplete or hidden.
  Nothing logged: `remaining` equals the target.
- `progress = eaten / target` (2 dp half-up; 0 with nothing logged), null under the same rules,
  except that a hidden nutrient keeps a shape rounded to the nearest 0.25.
- The week average is over days with items that are not marked partial. A day without a frozen
  row has no target. Nothing here reads or changes a verdict.

Hidden numbers (Q7): `hide_energy` nulls every energy number; `hide_all` also nulls every macro,
sugar, salt and fibre number. Portions, slot structure, bands and incompleteness stay.
"""

from collections.abc import Mapping, Sequence
from datetime import date, timedelta
from decimal import ROUND_HALF_UP, Decimal
from uuid import UUID

from app.features.diary.schemas import (
    DayTile,
    DayTileTargets,
    DiaryDayOut,
    DiaryWeekOut,
    Macro4,
    SlotDayOut,
    TargetsStatusOut,
)
from app.features.meal_slots.models import MealSlot
from app.features.meals.models import MealLog
from app.features.meals.schemas import IncompleteNutrients, NutrientBands, Totals
from app.features.meals.service import to_meal_out
from app.features.meals.summary import NUTRIENTS, _Acc, _bands, redact_totals
from app.features.targets.mapping import hidden_for, to_targets_out
from app.features.targets.schemas import NumbersDisplay, NumbersHidden
from app.scoring import DailyLimits
from app.scoring import targets as engine
from app.scoring.config import ScoringConfig

MACRO4 = ("energy_kcal", "protein_g", "fat_g", "carbs_g")
_TARGET_FIELD = {
    "energy_kcal": "energy_kcal",
    "protein_g": "protein_g",
    "fat_g": "fat_g",
    "carbs_g": "carbs_g",
}


def _dp(value: Decimal, places: int) -> float:
    return float(value.quantize(Decimal(1).scaleb(-places), rounding=ROUND_HALF_UP))


def _quarter(value: Decimal) -> float:
    return float((value * 4).quantize(Decimal(1), rounding=ROUND_HALF_UP) / 4)


def _is_hidden(key: str, hidden: NumbersHidden) -> bool:
    return hidden.macros or (hidden.energy and key == "energy_kcal")


def _target(result: engine.TargetResult | None, key: str) -> Decimal | None:
    if result is None or result.status != "ready":
        return None
    value = getattr(result, _TARGET_FIELD[key])
    return None if value is None else Decimal(value)


def remaining(
    target: engine.TargetResult | None, acc: _Acc, hidden: NumbersHidden
) -> Macro4 | None:
    """target - eaten per nutrient, 1 dp half-up. None as a whole without a ready target."""
    if target is None or target.status != "ready":
        return None
    out: dict[str, float | None] = {}
    for key in MACRO4:
        goal = _target(target, key)
        if goal is None or acc.incomplete[key] or _is_hidden(key, hidden):
            out[key] = None
        else:
            out[key] = _dp(goal - acc.sums[key], 1)
    return Macro4(**out)


def progress(target: engine.TargetResult | None, acc: _Acc, hidden: NumbersHidden) -> Macro4 | None:
    """eaten / target, 2 dp half-up (0 with nothing logged); a hidden value is rounded to the
    nearest 0.25. None as a whole without a ready target; null per nutrient when incomplete or
    when the target is not above 0."""
    if target is None or target.status != "ready":
        return None
    out: dict[str, float | None] = {}
    for key in MACRO4:
        goal = _target(target, key)
        if goal is None or goal <= 0 or acc.incomplete[key]:
            out[key] = None
            continue
        ratio = acc.sums[key] / goal
        out[key] = _quarter(ratio) if _is_hidden(key, hidden) else _dp(ratio, 2)
    return Macro4(**out)


def _acc_of(entries: Sequence[MealLog]) -> _Acc:
    acc = _Acc()
    for e in entries:
        acc.add(e.nutrients or {})
    return acc


def _totals(acc: _Acc, hidden: NumbersHidden) -> Totals:
    return redact_totals(Totals(**acc.totals()), hidden)


def _limits_for(limits: DailyLimits, result: engine.TargetResult | None) -> DailyLimits:
    """The protein band compares with that day's frozen protein target when it is ready."""
    if result is not None and result.status == "ready" and result.protein_g is not None:
        from dataclasses import replace

        return replace(limits, protein_target_g=float(result.protein_g))
    return limits


def _sorted(entries: Sequence[MealLog]) -> list[MealLog]:
    return sorted(entries, key=lambda e: (e.eaten_at, str(e.id)))


def build_day(
    *,
    member_id: UUID,
    day: date,
    today: date,
    timezone: str,
    slots: Sequence[MealSlot],
    entries: Sequence[MealLog],
    result: engine.TargetResult | None,
    targets_status: TargetsStatusOut,
    limits: DailyLimits,
    partial_logged: bool,
    numbers_display: NumbersDisplay,
    cfg: ScoringConfig | None = None,
) -> DiaryDayOut:
    hidden = hidden_for(numbers_display)
    by_slot: dict[UUID, list[MealLog]] = {}
    for e in entries:
        by_slot.setdefault(e.meal_slot_id, []).append(e)
    slot_rows = sorted(
        (s for s in slots if s.archived_at is None or by_slot.get(s.id)),
        key=lambda s: (s.position, str(s.id)),
    )
    slot_outs: list[SlotDayOut] = []
    for s in slot_rows:
        mine = _sorted(by_slot.get(s.id, []))
        acc = _acc_of(mine)
        slot_outs.append(
            SlotDayOut(
                slot_id=s.id,
                label_key=s.label_key,
                custom_label=s.custom_label,
                position=s.position,
                archived=s.archived_at is not None,
                entries=[to_meal_out(e, hidden) for e in mine],
                totals=_totals(acc, hidden),
                incomplete=IncompleteNutrients(**acc.incomplete),
            )
        )
    whole = _acc_of(entries)
    consent_required = targets_status == "consent_required"
    effective = None if consent_required else result
    return DiaryDayOut(
        member_id=member_id,
        date=day,
        today=today,
        timezone=timezone,
        slots=slot_outs,
        totals=_totals(whole, hidden),
        incomplete=IncompleteNutrients(**whole.incomplete),
        targets=None
        if consent_required
        else to_targets_out(member_id, day, result, numbers_display, cfg=cfg),
        targets_status=targets_status,
        remaining=remaining(effective, whole, hidden),
        progress=progress(effective, whole, hidden),
        limits_bands=NutrientBands(
            **_bands(
                whole.raw_totals(),
                whole.incomplete,
                whole.items,
                _limits_for(limits, effective),
                1,
                cfg,
            )
        ),
        partial_logged=partial_logged,
        numbers_hidden=hidden,
    )


def _average(accs: Sequence[_Acc], key: str, hidden: NumbersHidden) -> tuple[float | None, bool]:
    """(average per averaged day, incomplete). The sum covers the KNOWN values only, so with an
    unknown value on any averaged day the average is a lower bound and flagged."""
    incomplete = any(a.incomplete[key] for a in accs)
    known = [a for a in accs if a.known[key]]
    if not accs or not known or _is_hidden(key, hidden):
        return None, incomplete
    return _dp(sum((a.sums[key] for a in known), Decimal(0)) / len(accs), 1), incomplete


def build_week(
    *,
    member_id: UUID,
    end: date,
    today: date,
    entries: Sequence[MealLog],
    results: Mapping[date, engine.TargetResult | None],
    partial: Mapping[date, bool],
    limits: DailyLimits,
    numbers_display: NumbersDisplay,
    cfg: ScoringConfig | None = None,
) -> DiaryWeekOut:
    hidden = hidden_for(numbers_display)
    start = end - timedelta(days=6)
    per_day: dict[date, list[MealLog]] = {start + timedelta(days=i): [] for i in range(7)}
    for e in entries:
        if e.local_date in per_day:
            per_day[e.local_date].append(e)

    tiles: list[DayTile] = []
    averaged: list[_Acc] = []
    protein_met = 0
    for day, mine in per_day.items():
        acc = _acc_of(mine)
        result = results.get(day)
        ready = result is not None and result.status == "ready"
        is_partial = bool(partial.get(day, False))
        tiles.append(
            DayTile(
                date=day,
                items=acc.items,
                totals=_totals(acc, hidden),
                incomplete=IncompleteNutrients(**acc.incomplete),
                targets=DayTileTargets(
                    energy_kcal=None if hidden.energy else result.energy_kcal,  # type: ignore[union-attr]
                    protein_g=None if hidden.macros else result.protein_g,  # type: ignore[union-attr]
                )
                if ready
                else None,
                progress=progress(result, acc, hidden),
                partial_logged=is_partial,
                bands=NutrientBands(
                    **_bands(
                        acc.raw_totals(),
                        acc.incomplete,
                        acc.items,
                        _limits_for(limits, result),
                        1,
                        cfg,
                    )
                ),
            )
        )
        if acc.items > 0 and not is_partial:
            averaged.append(acc)
            goal = _target(result, "protein_g")
            if goal is not None and acc.known["protein_g"] and acc.sums["protein_g"] >= goal:
                protein_met += 1

    means: dict[str, float | None] = {}
    flags: dict[str, bool] = {}
    for key in NUTRIENTS:
        means[key], flags[key] = _average(averaged, key, hidden)
    return DiaryWeekOut(
        member_id=member_id,
        start=start,
        end=end,
        today=today,
        days=tiles,
        averages=Macro4(**{k: means[k] for k in MACRO4}),
        averages_incomplete=IncompleteNutrients(**flags),
        averaged_days=len(averaged),
        protein_met_days=protein_met,
        numbers_hidden=hidden,
    )


__all__ = ["build_day", "build_week", "progress", "remaining"]
