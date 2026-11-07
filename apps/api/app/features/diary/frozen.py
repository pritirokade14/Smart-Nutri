"""A `TargetResult` to and from a `diary_days` row (Plan 11 Task 3; Ruling E6; ADR 0023). Pure.

The target numbers go in columns. The unrounded explanation decimals go into `inputs` as
strings (a float would lose digits), plus `rate_kg_per_week`, `missing_fields` and
`yaml_version`. `from_row` rebuilds a `TargetResult`, so `targets.mapping.to_targets_out` stays
the only mapping to the API shape and redaction always uses the CURRENT numbers display.
`rate_options` are not frozen: a past day offers no choices.
"""

from dataclasses import fields
from decimal import Decimal
from typing import Any

from app.features.diary.models import DiaryDay
from app.scoring import targets
from app.scoring.config import ScoringConfig, load_config

_EXPLANATION_FIELDS = tuple(f.name for f in fields(targets.Explanation))
_DECIMAL_FIELDS = tuple(
    f for f in _EXPLANATION_FIELDS if f not in ("protein_basis", "weight_source")
)


def _s(value: Decimal | None) -> str | None:
    return None if value is None else str(value)


def _d(value: str | None) -> Decimal | None:
    return None if value is None else Decimal(value)


def _dec(value: int | None) -> Decimal | None:
    return None if value is None else Decimal(value)


def _int(value: Decimal | None) -> int | None:
    return None if value is None else int(value)


def to_row_values(result: targets.TargetResult | None, cfg: ScoringConfig | None = None) -> dict:
    """Column values for a `diary_days` row. None is status `none`: no numbers at all."""
    if result is None:
        return {
            "status": "none",
            "energy_kcal": None,
            "protein_g": None,
            "fat_g": None,
            "carbs_g": None,
            "basis": None,
            "direction": None,
            "rate_pct_bw_per_week": None,
            "inputs": {},
            "flags": [],
        }
    cfg = cfg or load_config()
    inputs: dict[str, Any] = {
        "missing_fields": list(result.missing_fields),
        "yaml_version": cfg.targets.get("version"),
        "rate_kg_per_week": None if result.rate is None else _s(result.rate.kg_per_week),
    }
    e = result.explanation
    if e is not None:
        for name in _DECIMAL_FIELDS:
            inputs[name] = _s(getattr(e, name))
        inputs["protein_basis"] = e.protein_basis
        inputs["weight_source"] = e.weight_source
    return {
        "status": result.status,
        "energy_kcal": _dec(result.energy_kcal),
        "protein_g": _dec(result.protein_g),
        "fat_g": _dec(result.fat_g),
        "carbs_g": _dec(result.carbs_g),
        "basis": "formula" if result.status == "ready" else None,
        "direction": result.direction,
        "rate_pct_bw_per_week": None if result.rate is None else result.rate.pct_bw_per_week,
        "inputs": inputs,
        "flags": list(result.flags),
    }


def from_row(row: DiaryDay) -> targets.TargetResult | None:
    """The frozen result, with no `rate_options`. Status `none` is None."""
    if row.status == "none":
        return None
    inputs = row.inputs or {}
    rate = None
    if row.rate_pct_bw_per_week is not None and inputs.get("rate_kg_per_week") is not None:
        rate = targets.RateOption(
            pct_bw_per_week=Decimal(row.rate_pct_bw_per_week),
            kg_per_week=Decimal(inputs["rate_kg_per_week"]),
        )
    explanation = None
    if "bmr_kcal" in inputs:
        explanation = targets.Explanation(
            **{name: _d(inputs.get(name)) for name in _DECIMAL_FIELDS},
            protein_basis=inputs["protein_basis"],
            weight_source=inputs.get("weight_source"),  # absent in rows frozen before slice 6
        )
    return targets.TargetResult(
        status=row.status,  # type: ignore[arg-type]  (checked by ck_diary_days_status)
        missing_fields=tuple(inputs.get("missing_fields", ())),
        energy_kcal=_int(row.energy_kcal),
        protein_g=_int(row.protein_g),
        fat_g=_int(row.fat_g),
        carbs_g=_int(row.carbs_g),
        direction=row.direction,  # type: ignore[arg-type]
        rate=rate,
        rate_options=(),
        explanation=explanation,
        flags=tuple(row.flags or ()),
    )
