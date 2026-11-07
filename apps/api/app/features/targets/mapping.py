"""Engine result -> `TargetsOut` (Plan 10 Task 4). Pure: the fixture generator imports it.

Display rounding (Ruling D12): kcal in the explanation are whole kcal, half-up; weights 1 dp;
`rate` and `rate_options` 2 dp. Hidden numbers (Ruling D11):

- `hide_energy` nulls every energy number (the target and the explanation's kcal values).
- `hide_all` also nulls protein, fat, carbs and every explanation number except
  `protein_basis`.
- The pace (`rate`, `rate_options`) stays visible under `hide_all`: the user must choose it.
- Flags and the status are not numbers and are never hidden.
"""

from datetime import date
from decimal import ROUND_HALF_UP, Decimal
from uuid import UUID

from app.features.targets.schemas import (
    NumbersDisplay,
    NumbersHidden,
    RateOut,
    TargetsExplanation,
    TargetsOut,
)
from app.scoring import targets
from app.scoring.config import ScoringConfig


def _dp(value: Decimal, places: int) -> float:
    return float(value.quantize(Decimal(1).scaleb(-places), rounding=ROUND_HALF_UP))


def _kcal(value: Decimal) -> int:
    return int(value.quantize(Decimal(1), rounding=ROUND_HALF_UP))


def _rate(option: targets.RateOption) -> RateOut:
    return RateOut(
        pct_bw_per_week=_dp(option.pct_bw_per_week, 2), kg_per_week=_dp(option.kg_per_week, 2)
    )


def _explanation(e: targets.Explanation, hidden: NumbersHidden) -> TargetsExplanation:
    if hidden.macros:
        return TargetsExplanation(
            bmr_kcal=None,
            activity_factor=None,
            maintenance_kcal=None,
            adjustment_kcal=None,
            weight_kg_used=None,
            protein_basis=e.protein_basis,
            protein_g_per_kg=None,
            protein_reference_weight_kg=None,
            body_fat_pct_used=None,
            ibw_kg=None,
            floor_kcal=None,
        )

    def energy(value: Decimal | None) -> int | None:
        return None if hidden.energy or value is None else _kcal(value)

    return TargetsExplanation(
        bmr_kcal=energy(e.bmr_kcal),
        activity_factor=float(e.activity_factor),
        maintenance_kcal=energy(e.maintenance_kcal),
        adjustment_kcal=energy(e.adjustment_kcal),
        weight_kg_used=_dp(e.weight_kg_used, 1),
        protein_basis=e.protein_basis,
        protein_g_per_kg=float(e.protein_g_per_kg),
        protein_reference_weight_kg=_dp(e.protein_reference_weight_kg, 1),
        body_fat_pct_used=None if e.body_fat_pct_used is None else float(e.body_fat_pct_used),
        ibw_kg=None if e.ibw_kg is None else _dp(e.ibw_kg, 1),
        floor_kcal=energy(e.floor_kcal),
    )


def hidden_for(numbers_display: NumbersDisplay) -> NumbersHidden:
    return NumbersHidden(
        energy=numbers_display in ("hide_energy", "hide_all"),
        macros=numbers_display == "hide_all",
    )


def to_targets_out(
    member_id: UUID,
    day: date,
    result: targets.TargetResult | None,
    numbers_display: NumbersDisplay,
    *,
    unusual: tuple[str, ...] = (),
    cfg: ScoringConfig | None = None,
) -> TargetsOut:
    """``result=None`` is status `none` (no settings, or a past day)."""
    hidden = hidden_for(numbers_display)
    common = {
        "member_id": member_id,
        "date": day,
        "numbers_hidden": hidden,
        "sources": list(targets.sources(cfg)),
        "unusual_fields": list(unusual),
    }
    if result is None:
        return TargetsOut(
            status="none",
            missing_fields=[],
            energy_kcal=None,
            protein_g=None,
            fat_g=None,
            carbs_g=None,
            basis=None,
            direction=None,
            rate=None,
            rate_options=[],
            explanation=None,
            flags=[],
            **common,
        )
    ready = result.status == "ready"
    return TargetsOut(
        status=result.status,
        missing_fields=list(result.missing_fields),
        energy_kcal=None if hidden.energy else result.energy_kcal,
        protein_g=None if hidden.macros else result.protein_g,
        fat_g=None if hidden.macros else result.fat_g,
        carbs_g=None if hidden.macros else result.carbs_g,
        basis="formula" if ready else None,
        direction=result.direction,
        rate=None if result.rate is None else _rate(result.rate),
        rate_options=[_rate(o) for o in result.rate_options],
        explanation=None
        if result.explanation is None
        else _explanation(result.explanation, hidden),
        flags=list(result.flags),
        **common,
    )
