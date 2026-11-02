"""Condition, goal, child and infant rules."""

from __future__ import annotations

from collections.abc import Sequence
from typing import Any

from app.scoring.claims import ClaimCheck
from app.scoring.config import ScoringConfig
from app.scoring.models import ClaimVerdict, Member, Product, Reason, Status
from app.scoring.nutriscore import NutriScoreResult
from app.scoring.warnings import (
    added_sugar_terms,
    hidden_sugars,
    high_in,
    ingredient_hits,
    sodium_additives,
)

_SUGAR_CLAIMS = frozenset({"sugar_free", "low_sugar", "no_added_sugar"})


def _r(n: float) -> float:
    return round(float(n), 2)


def _active_groups(member: Member, cond: dict[str, Any]) -> list[str]:
    groups: list[str] = []
    for name, rule in cond.items():
        applies = rule.get("applies_to")
        if not applies:
            continue
        if any(c in applies for c in member.conditions) or (
            member.goal is not None and member.goal in applies
        ):
            groups.append(name)
    age = member.age
    if age is not None:
        if age < cond["infant"]["max_age"]:
            groups.append("infant")
        elif age < cond["child"]["max_age"]:
            groups.append("child")
    return groups


def _child_limit(age: int, bands: dict[int, float]) -> float | None:
    eligible = [k for k in bands if int(k) <= age]
    return bands[max(eligible)] if eligible else None


def condition_reasons(
    product: Product,
    member: Member,
    nutriscore: NutriScoreResult,
    claims: Sequence[ClaimCheck],
    cfg: ScoringConfig,
) -> list[Reason]:
    cond = cfg.thresholds["conditions"]
    groups = _active_groups(member, cond)
    n = product.per_100g
    out: list[Reason] = []
    missing: set[tuple[str, str]] = set()

    def need(name: str, value: float | None, group: str) -> float | None:
        if value is None and (name, group) not in missing:
            missing.add((name, group))
            out.append(Reason("nutrient_missing", Status.UNKNOWN, {"nutrient": name, "rule": group}))
        return value

    if "blood_sugar" in groups:
        c = cond["blood_sugar"]
        sugars = need("sugars_g", n.sugars_g, "blood_sugar")
        if sugars is not None:
            if sugars > c["avoid_sugars_g"]:
                out.append(Reason("sugar_high", Status.AVOID, {"sugars_g": _r(sugars)}))
            elif sugars > c["caution_sugars_g"]:
                out.append(Reason("sugar_moderate", Status.CAUTION, {"sugars_g": _r(sugars)}))
        for ck in claims:
            if ck.claim in _SUGAR_CLAIMS and ck.verdict == ClaimVerdict.CONTRADICTED:
                out.append(Reason("misleading_sugar_claim", Status.AVOID, {"claim": ck.claim}))
        hs = hidden_sugars(product, cfg)
        if hs:
            out.append(Reason("hidden_sugars", Status.CAUTION, {"ingredients": list(hs)}))
        carbs = need("carbs_g", n.carbs_g, "blood_sugar")
        per_serv = product.per_serving(carbs)
        if per_serv is not None and per_serv > c["caution_carbs_per_serving_g"]:
            out.append(Reason("carbs_per_serving_high", Status.CAUTION, {"carbs_g": _r(per_serv)}))

    if "hypertension" in groups:
        c = cond["hypertension"]
        salt = need("salt", n.salt(), "hypertension")
        if salt is not None:
            if salt > c["avoid_salt_g"]:
                out.append(Reason("salt_high", Status.AVOID, {"salt_g": _r(salt)}))
            elif salt > c["caution_salt_g"]:
                out.append(Reason("salt_moderate", Status.CAUTION, {"salt_g": _r(salt)}))
        sa = sodium_additives(product, cfg)
        if sa:
            out.append(Reason("sodium_additives", Status.CAUTION, {"ingredients": list(sa)}))

    if "weight_loss" in groups:
        c = cond["weight_loss"]
        kcal = need("energy_kcal", n.energy_kcal, "weight_loss")
        if kcal is not None and kcal > c["caution_energy_kcal"]:
            out.append(Reason("energy_dense", Status.CAUTION, {"energy_kcal": _r(kcal)}))
        if nutriscore.grade in c["caution_nutriscore"]:
            out.append(Reason("nutriscore_low", Status.CAUTION, {"grade": nutriscore.grade}))
        protein = need("protein_g", n.protein_g, "weight_loss")
        if kcal and protein is not None:
            density = protein / kcal * 100
            if density >= c["good_protein_g_per_100kcal"]:
                out.append(
                    Reason("good_protein_density", Status.OK, {"protein_g_per_100kcal": _r(density)})
                )

    if "child" in groups and member.age is not None:
        c = cond["child"]
        sugars = need("sugars_g", n.sugars_g, "child")
        limit = _child_limit(member.age, c["free_sugar_daily_limit_g"])
        if sugars is not None and limit:
            amount = product.per_serving(sugars) if product.serving_size_g is not None else sugars
            pct = amount / limit * 100
            params = {"pct": _r(pct), "limit_g": _r(limit)}
            if pct > c["avoid_pct_of_limit"]:
                out.append(Reason("child_sugar_high", Status.AVOID, params))
            elif pct > c["caution_pct_of_limit"]:
                out.append(Reason("child_sugar_moderate", Status.CAUTION, params))
        caf = ingredient_hits(product, cfg, "caffeine")
        if caf:
            out.append(Reason("child_caffeine", Status.AVOID, {"ingredients": list(caf)}))
        if "salt" in high_in(product, cfg):
            out.append(Reason("salt_high", Status.CAUTION, {}))

    if "infant" in groups:
        sugar_terms = added_sugar_terms(product, cfg)
        if sugar_terms:
            out.append(Reason("infant_added_sugar", Status.AVOID, {"ingredients": list(sugar_terms)}))
        salt_hits = ingredient_hits(product, cfg, "salt")
        if salt_hits:
            out.append(Reason("infant_added_salt", Status.AVOID, {"ingredients": list(salt_hits)}))
        if "honey" in sugar_terms:
            out.append(Reason("infant_honey", Status.AVOID, {}))

    return out
