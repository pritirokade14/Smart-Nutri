"""Daily energy and macro targets (Food Diary slice 1).

A pure engine: no I/O, no database, no LLM. Every constant is read from ``targets.yaml``
(PENDING CLINICIAN REVIEW). Targets are information, never verdicts: ``verdict.py`` and the
verdict modules never import this module, and it is deliberately not re-exported from
``app.scoring``. All arithmetic is ``Decimal`` with half-up rounding, so a float never decides a
boundary (BMI exactly 30.0, .5 roundings).
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import ROUND_CEILING, ROUND_HALF_UP, Decimal
from typing import Any, Literal

from app.scoring.config import ScoringConfig, load_config

Direction = Literal["lose", "maintain", "gain"]
ActivityLevel = Literal["sedentary", "light", "moderate", "very"]
SexReference = Literal["male", "female", "average"]
TargetsStatus = Literal["ready", "needs_body_data", "not_available_minor", "paused_pregnancy"]
ProteinBasis = Literal["lean_mass", "adjusted_weight", "actual_weight"]

# Emitted in this order (deterministic fixtures).
FLAG_ORDER: tuple[str, ...] = (
    "underweight_maintenance",
    "rate_capped",
    "deficit_capped",
    "taper_active",
    "goal_weight_reached",
    "floor_applied",
    "floor_limits_deficit",
    "protein_capped",
    "carbs_below_reference",
    "average_sex_reference",
    "outside_equation_age_range",
)

_HUNDRED = Decimal(100)
_CM_PER_INCH = Decimal("2.54")


def _d(x: Any) -> Decimal:
    return x if isinstance(x, Decimal) else Decimal(str(x))


@dataclass(frozen=True, slots=True)
class BodyData:
    """age = youngest_age(birth_year, today) (Ruling D2); None when the birth year is unknown."""

    age: int | None
    sex: Literal["female", "male", "other"] | None
    height_cm: Decimal | None
    weight_kg: Decimal | None
    body_fat_pct: Decimal | None
    goal: str | None


@dataclass(frozen=True, slots=True)
class GoalSettings:
    direction: Direction
    activity_level: ActivityLevel
    rate_pct_bw_per_week: Decimal | None = None  # None = YAML default for the direction
    target_weight_kg: Decimal | None = None
    sex_reference: SexReference | None = None
    pregnant_or_breastfeeding: bool = False
    fat_pct_energy: Decimal | None = None  # None = macros.fat_pct_energy.default


@dataclass(frozen=True, slots=True)
class RateOption:
    """Unsigned (Ruling D5), unrounded."""

    pct_bw_per_week: Decimal
    kg_per_week: Decimal


@dataclass(frozen=True, slots=True)
class Explanation:
    """Unrounded; display rounding belongs to the API mapping (Task 4)."""

    bmr_kcal: Decimal
    activity_factor: Decimal
    maintenance_kcal: Decimal
    adjustment_kcal: Decimal
    weight_kg_used: Decimal
    protein_basis: ProteinBasis
    protein_g_per_kg: Decimal
    protein_reference_weight_kg: Decimal
    body_fat_pct_used: Decimal | None
    ibw_kg: Decimal | None
    floor_kcal: Decimal | None  # lose only: max(floor_by_sex, BMR x min_bmr_multiple)


@dataclass(frozen=True, slots=True)
class TargetResult:
    status: TargetsStatus
    missing_fields: tuple[str, ...] = ()
    energy_kcal: int | None = None
    protein_g: int | None = None
    fat_g: int | None = None
    carbs_g: int | None = None
    direction: Direction | None = None
    rate: RateOption | None = None  # after clamp and taper; None for maintain
    rate_options: tuple[RateOption, ...] = ()  # every YAML option for the direction at W
    explanation: Explanation | None = None
    flags: tuple[str, ...] = ()


class SettingsRuleError(Exception):
    def __init__(self, code: str, details: dict[str, Any] | None = None) -> None:
        super().__init__(code)
        self.code = code
        self.details = details or {}


def _round(x: Decimal, step: Decimal = Decimal(1)) -> Decimal:
    """Half-up to a multiple of ``step``."""
    return (x / step).quantize(Decimal(1), rounding=ROUND_HALF_UP) * step


def _num(x: Decimal) -> int | float:
    return int(x) if x == x.to_integral_value() else float(x)


def _h2(height_cm: Decimal) -> Decimal:
    h = height_cm / _HUNDRED
    return h * h


def _cfg(cfg: ScoringConfig | None) -> ScoringConfig:
    return cfg if cfg is not None else load_config()


def _goal_key(goal: str | None, table: Any, fallback: str | None) -> Any:
    """``table[goal]`` when the goal has an entry, else ``fallback`` (a key or None)."""
    if goal is not None:
        try:
            return table[goal]
        except KeyError:
            pass
    return table[fallback] if fallback is not None else None


def protein_g_per_kg(goal: str | None, cfg: ScoringConfig | None = None) -> Decimal:
    """Protein g per kg of body weight for a goal (the one source, also used by the summary)."""
    p = _cfg(cfg).targets["protein"]
    by_goal = p["g_per_kg_by_goal"]
    if goal is not None:
        try:
            return _d(by_goal[goal])
        except KeyError:
            pass
    return _d(p["default_g_per_kg"])


def _lean_factor(goal: str | None, cfg: ScoringConfig) -> Decimal:
    table = cfg.targets["protein"]["lean_mass_g_per_kg_by_goal"]
    if goal is not None:
        try:
            return _d(table[goal])
        except KeyError:
            pass
    return _d(table["default"])


def default_direction(goal: str | None) -> Direction:
    if goal in ("build_muscle", "weight_gain"):
        return "gain"
    if goal == "weight_loss":
        return "lose"
    return "maintain"


def sources(cfg: ScoringConfig | None = None) -> tuple[str, ...]:
    """Source keys for the methodology link (section_sources.energy_targets); () until it exists."""
    section = (_cfg(cfg).thresholds.get("section_sources") or {}).get("energy_targets")
    if not section:
        return ()
    keys: list[str] = []
    for k in [*section.get("thresholds", []), *section.get("rationale", [])]:
        if k not in keys:
            keys.append(k)
    return tuple(keys)


def check_body_fat(value: Decimal | None, cfg: ScoringConfig | None = None) -> None:
    if value is None:
        return
    bf = _cfg(cfg).targets["body_fat"]
    lo, hi = _d(bf["min_pct"]), _d(bf["max_pct"])
    if value < lo or value > hi:
        raise SettingsRuleError("body_fat_out_of_range", {"min": _num(lo), "max": _num(hi)})


def unusual_fields(body: BodyData, cfg: ScoringConfig | None = None) -> tuple[str, ...]:
    pl = _cfg(cfg).targets["plausible"]
    out: list[str] = []
    if body.height_cm is not None:
        h = pl["height_cm"]
        if body.height_cm < _d(h["min"]) or body.height_cm > _d(h["max"]):
            out.append("height_cm")
    if body.weight_kg is not None:
        w = pl["weight_kg"]
        if body.weight_kg < _d(w["min"]) or body.weight_kg > _d(w["max"]):
            out.append("weight_kg")
    return tuple(out)


def check_settings(
    body: BodyData, settings: GoalSettings, cfg: ScoringConfig | None = None
) -> None:
    """Rules a SAVE must pass; compute() never raises these (stored settings can stop validating)."""
    cfg = _cfg(cfg)
    t = cfg.targets
    fat = settings.fat_pct_energy
    if fat is not None:
        fp = t["macros"]["fat_pct_energy"]
        lo, hi = _d(fp["min"]), _d(fp["max"])
        if fat < lo or fat > hi:
            raise SettingsRuleError("fat_pct_out_of_range", {"min": _num(lo), "max": _num(hi)})
    rate = settings.rate_pct_bw_per_week
    if rate is not None:
        options: list[Decimal] = (
            []
            if settings.direction == "maintain"
            else [_d(o) for o in t["goal_rates"][settings.direction]["options_pct_bw_per_week"]]
        )
        if rate not in options:
            raise SettingsRuleError("rate_not_allowed", {"options": [float(o) for o in options]})
    if (
        body.age is not None
        and body.age < t["minors"]["min_age_for_targets"]
        and settings.direction != "maintain"
    ):
        raise SettingsRuleError("goal_not_allowed_minor")
    gr = t["goal_rates"]
    h, w = body.height_cm, body.weight_kg
    if (
        settings.direction == "lose"
        and h is not None
        and w is not None
        and w < _d(gr["lose_min_current_bmi"]) * _h2(h)
    ):
        raise SettingsRuleError("goal_not_allowed_underweight")
    if settings.target_weight_kg is not None and h is not None:
        min_kg = _d(gr["target_weight_min_bmi"]) * _h2(h)
        if settings.target_weight_kg < min_kg:
            raise SettingsRuleError(
                "target_weight_too_low",
                {"min_kg": float(min_kg.quantize(Decimal("0.1"), rounding=ROUND_CEILING))},
            )


def _devine_ibw(height_cm: Decimal, sex_key: str, cfg: ScoringConfig) -> Decimal:
    p = cfg.targets["protein"]["ibw"]
    if p["formula"] != "devine":
        raise ValueError(f"unknown protein.ibw.formula: {p['formula']!r}")
    dv = p["devine"]
    inches_over = max(Decimal(0), height_cm / _CM_PER_INCH - 60)
    return _d(dv["base_kg"][sex_key]) + _d(dv["kg_per_inch_over_60"]) * inches_over


@dataclass(frozen=True, slots=True)
class ProteinReference:
    """The protein reference weight and the g/kg-capped daily grams (before the energy cap)."""

    basis: ProteinBasis
    factor: Decimal
    weight_kg: Decimal
    ibw_kg: Decimal | None
    bf: Decimal | None
    capped_g: Decimal


def protein_reference(
    body: BodyData, sex_key: str, cfg: ScoringConfig | None = None
) -> ProteinReference:
    """Spec 4.7: lean mass when body fat is known, else the adjusted body weight at BMI >= 30
    (Devine, 0.25), else the actual weight; then the g/kg-of-actual-weight cap. The one source,
    also used by the summary's no-settings fallback. Needs height and weight (BMI)."""
    cfg = _cfg(cfg)
    pr = cfg.targets["protein"]
    assert body.weight_kg is not None
    W, H = body.weight_kg, body.height_cm
    ibw: Decimal | None = None
    bf_used: Decimal | None = None
    if body.body_fat_pct is not None:
        basis: ProteinBasis = "lean_mass"
        w_ref = W * (1 - body.body_fat_pct / _HUNDRED)
        factor = _lean_factor(body.goal, cfg)
        bf_used = body.body_fat_pct
    else:
        factor = protein_g_per_kg(body.goal, cfg)
        if H is not None and W >= _d(pr["adjusted_weight"]["min_bmi"]) * _h2(H):
            basis = "adjusted_weight"
            ibw = _devine_ibw(H, sex_key, cfg)
            w_ref = ibw + _d(pr["adjusted_weight"]["excess_fraction"]) * (W - ibw)
        else:
            basis = "actual_weight"
            w_ref = W
    capped = min(factor * w_ref, _d(pr["max_g_per_kg"]) * W)
    return ProteinReference(basis, factor, w_ref, ibw, bf_used, capped)


def _missing(body: BodyData, settings: GoalSettings) -> tuple[str, ...]:
    out: list[str] = []
    if body.age is None:
        out.append("birth_year")
    if body.sex is None and settings.sex_reference is None:
        out.append("sex")
    if body.height_cm is None:
        out.append("height_cm")
    if body.weight_kg is None:
        out.append("weight_kg")
    return tuple(out)


def _sex_key(body: BodyData, settings: GoalSettings) -> str:
    if body.sex in ("male", "female"):
        return body.sex
    return settings.sex_reference or "average"


def compute(
    body: BodyData, settings: GoalSettings, cfg: ScoringConfig | None = None
) -> TargetResult:
    cfg = _cfg(cfg)
    t = cfg.targets
    if body.age is not None and body.age < t["minors"]["min_age_for_targets"]:
        return TargetResult(status="not_available_minor")
    if settings.pregnant_or_breastfeeding:
        return TargetResult(status="paused_pregnancy")
    missing = _missing(body, settings)
    if missing:
        return TargetResult(status="needs_body_data", missing_fields=missing)

    assert body.age is not None and body.height_cm is not None and body.weight_kg is not None
    flags: set[str] = set()
    age, H, W = body.age, body.height_cm, body.weight_kg
    sex_key = _sex_key(body, settings)
    if sex_key == "average":
        flags.add("average_sex_reference")
    va = t["energy"]["mifflin"]["valid_age"]
    if age < va["min"] or age > va["max"]:
        flags.add("outside_equation_age_range")

    # Energy at rest and maintenance (spec 4.2, 4.3)
    mif = t["energy"]["mifflin"]
    bmr = (
        _d(mif["weight_kcal_per_kg"]) * W
        + _d(mif["height_kcal_per_cm"]) * H
        - _d(mif["age_kcal_per_year"]) * age
        + _d(mif["sex_constant"][sex_key])
    )
    f_act = _d(t["energy"]["activity_factor"][settings.activity_level])
    e_m = bmr * f_act

    # Direction: a stored "lose" below the BMI floor is computed as maintenance (Ruling D8)
    gr = t["goal_rates"]
    direction: Direction = settings.direction
    if direction == "lose" and W < _d(gr["lose_min_current_bmi"]) * _h2(H):
        direction = "maintain"
        flags.add("underweight_maintenance")

    rate_options: tuple[RateOption, ...] = ()
    rate: RateOption | None = None
    delta = Decimal(0)
    rho = _d(t["energy"]["kcal_per_kg_body_weight"])
    if direction != "maintain":
        pcts = [_d(o) for o in gr[direction]["options_pct_bw_per_week"]]
        rate_options = tuple(RateOption(p, p / _HUNDRED * W) for p in pcts)
        pct = (
            settings.rate_pct_bw_per_week
            if settings.rate_pct_bw_per_week is not None
            else _d(gr[direction]["default_pct_bw_per_week"])
        )
        lo, hi = min(pcts), max(pcts)
        if pct < lo or pct > hi:
            pct = min(max(pct, lo), hi)
            flags.add("rate_capped")
        r_kg = pct / _HUNDRED * W
        if direction == "lose":
            max_kg = _d(gr["lose"]["max_kg_per_week"])
            if r_kg > max_kg:
                r_kg = max_kg
                pct = r_kg / W * _HUNDRED
                flags.add("rate_capped")

        # Taper near the target weight (spec 4.5); W is the weight in use (Ruling D18)
        reached = False
        tw = settings.target_weight_kg
        if tw is not None:
            min_kg = _d(gr["target_weight_min_bmi"]) * _h2(H)
            tw = max(tw, min_kg)  # Ruling D8
            band = _d(gr["taper"]["maintenance_band_kg"])
            weeks = _d(gr["taper"]["weeks"])
            if (direction == "lose" and W <= tw + band) or (direction == "gain" and W >= tw - band):
                reached = True
                flags.add("goal_weight_reached")
            else:
                d = abs(W - tw)
                if r_kg * weeks > d:
                    r_kg = d / weeks
                    pct = r_kg / W * _HUNDRED
                    flags.add("taper_active")
        if not reached:
            rate = RateOption(pct, r_kg)
            delta = r_kg * rho / 7
            if direction == "lose":
                cap_pct = _d(gr["max_deficit_pct_of_maintenance"]) / _HUNDRED * e_m
                cap_abs = _d(gr["max_deficit_kcal_per_day"])
                cap = min(cap_pct, cap_abs)
                if delta > cap:
                    delta = cap
                    flags.add("deficit_capped")
                delta = -delta

    # Floors apply to loss only and never turn a loss into a surplus (spec 4.6)
    e_raw = e_m + delta
    floor_kcal: Decimal | None = None
    e_t = e_raw
    floor_bound = False
    if direction == "lose":
        fl = t["floors"]
        # Q11b: sex "other" or not given always gets the higher floor, whichever estimate is used
        floor_sex = sex_key if body.sex in ("male", "female") else "average"
        floor_kcal = max(_d(fl["kcal_by_sex"][floor_sex]), bmr * _d(fl["min_bmr_multiple"]))
        bar = min(floor_kcal, e_m)
        if e_raw < bar:
            e_t = bar
            flags.add("floor_applied" if floor_kcal <= e_m else "floor_limits_deficit")
            # only when the floor itself binds: maintenance (floor_limits_deficit) must not
            # round up into a surplus, and the activity factor keeps it above BMR anyway
            floor_bound = floor_kcal <= e_m
    kcal_step = _d(t["rounding"]["kcal_step"])
    if floor_bound:
        # round UP so a binding floor (which can be the BMR) is never undercut
        energy = int((e_t / kcal_step).quantize(Decimal(1), rounding=ROUND_CEILING) * kcal_step)
    else:
        energy = int(_round(e_t, kcal_step))

    # Protein: reference weight, then the two caps (spec 4.7, 4.7.1)
    pr = t["protein"]
    ref = protein_reference(body, sex_key, cfg)
    basis, factor, w_ref, ibw, bf_used = ref.basis, ref.factor, ref.weight_kg, ref.ibw_kg, ref.bf
    kcal_g = t["macros"]["kcal_per_g"]
    p_kcal, c_kcal, f_kcal = _d(kcal_g["protein"]), _d(kcal_g["carbs"]), _d(kcal_g["fat"])
    p_raw = ref.capped_g
    p_energy_cap = _d(pr["max_energy_pct"]) / _HUNDRED * energy / p_kcal
    if p_raw > p_energy_cap:
        p_raw = p_energy_cap
        flags.add("protein_capped")
    g_step = _d(t["rounding"]["macro_g_step"])
    protein = int(_round(p_raw, g_step))

    fp = t["macros"]["fat_pct_energy"]
    fat_pct = settings.fat_pct_energy if settings.fat_pct_energy is not None else _d(fp["default"])
    fat_pct = max(fat_pct, _d(fp["min"]))
    fat = int(_round(fat_pct / _HUNDRED * energy / f_kcal, g_step))
    carbs = int(_round((Decimal(energy) - p_kcal * protein - f_kcal * fat) / c_kcal, g_step))
    if carbs < _d(t["macros"]["carbs_reference_min_g"]):
        flags.add("carbs_below_reference")

    return TargetResult(
        status="ready",
        energy_kcal=energy,
        protein_g=protein,
        fat_g=fat,
        carbs_g=carbs,
        direction=direction,
        rate=rate,
        rate_options=rate_options,
        explanation=Explanation(
            bmr_kcal=bmr,
            activity_factor=f_act,
            maintenance_kcal=e_m,
            adjustment_kcal=delta,
            weight_kg_used=W,
            protein_basis=basis,
            protein_g_per_kg=factor,
            protein_reference_weight_kg=w_ref,
            body_fat_pct_used=bf_used,
            ibw_kg=ibw,
            floor_kcal=floor_kcal,
        ),
        flags=tuple(f for f in FLAG_ORDER if f in flags),
    )
