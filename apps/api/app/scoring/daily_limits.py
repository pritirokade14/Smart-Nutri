"""Per-member DAILY limits for the meal-log summaries (Plan 6 T1).

Every number is read from ``thresholds.yaml`` (``daily_limits`` plus the child and infant ages
and the child free-sugar bands under ``conditions``), all PENDING CLINICIAN REVIEW. These
limits never affect a verdict: the verdict rules do not read them.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any, Literal

from app.scoring.config import ScoringConfig, load_config
from app.scoring.models import Member

Band = Literal["ok", "near", "over", "unknown"]


@dataclass(frozen=True, slots=True)
class DailyLimits:
    sugar_g: float | None  # free/added-sugar limit (adult WHO 25 g; child and infant bands)
    salt_g: float | None
    # weight_kg x protein_g_per_kg for adults only; None without a weight or below the adult age
    protein_target_g: float | None
    kcal: None = None  # informational only in v1: no personal energy target


def _by_min_age(age: int, bands: Mapping[Any, float]) -> float | None:
    """The value of the band with the highest min age <= ``age`` (None below every band)."""
    norm = {int(k): v for k, v in bands.items()}
    eligible = [k for k in norm if k <= age]
    return norm[max(eligible)] if eligible else None


def daily_limits_for(
    member: Member, weight_kg: float | None, cfg: ScoringConfig | None = None
) -> DailyLimits:
    """Daily sugar and salt limits by age band, and a protein target from body weight.

    ``age=None`` gets adult sugar and salt limits: the summary is information, and the verdicts
    already treat an unknown age protectively (``age_unknown``). The protein target is the
    ADULT safe level, so it needs a weight AND a known age of at least
    ``daily_limits.protein_min_age``; anyone younger, or of unknown age, gets None.
    """
    if cfg is None:
        cfg = load_config()
    dl = cfg.thresholds["daily_limits"]
    cond = cfg.thresholds["conditions"]
    adult = dl["adult"]
    age = member.age

    sugar: float | None = adult["sugar_g"]
    salt: float | None = adult["salt_g"]
    if age is not None and age < cond["infant"]["max_age"]:
        sugar, salt = dl["infant"]["sugar_g"], dl["infant"]["salt_g"]
    elif age is not None and age < cond["child"]["max_age"]:
        sugar = _by_min_age(age, cond["child"]["free_sugar_daily_limit_g"])
        salt = _by_min_age(age, dl["child_salt_g_by_min_age"])

    protein = None
    is_adult = age is not None and age >= dl["protein_min_age"]
    if is_adult and weight_kg is not None and weight_kg > 0:
        protein = weight_kg * adult["protein_g_per_kg"]
    return DailyLimits(sugar_g=sugar, salt_g=salt, protein_target_g=protein, kcal=None)


def nutrient_band(
    value: float | None, limit: float | None, cfg: ScoringConfig | None = None
) -> Band:
    """unknown if either is None; a 0 limit: over if value > 0 else ok; otherwise over above
    the limit, near from ``near_pct`` % of it, else ok."""
    if value is None or limit is None:
        return "unknown"
    if cfg is None:
        cfg = load_config()
    if limit == 0:
        return "over" if value > 0 else "ok"
    if value > limit:
        return "over"
    if value >= limit * cfg.thresholds["daily_limits"]["near_pct"] / 100:
        return "near"
    return "ok"
