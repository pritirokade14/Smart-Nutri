"""Front-of-pack claim checking against label data."""

from __future__ import annotations

import re
from collections.abc import Callable, Mapping
from dataclasses import dataclass, field
from typing import Any

from app.scoring.allergens import ingredients_known
from app.scoring.config import ScoringConfig
from app.scoring.ingredients import normalize
from app.scoring.models import ClaimVerdict, Product
from app.scoring.warnings import added_sugar_terms


@dataclass(frozen=True, slots=True)
class ClaimCheck:
    claim: str
    verdict: ClaimVerdict
    reason_code: str
    params: Mapping[str, Any] = field(default_factory=dict)


# Ordered: first matching key wins.
_PATTERNS: tuple[tuple[str, tuple[str, ...]], ...] = (
    ("no_added_sugar", ("no added sugar",)),
    ("sugar_free", ("sugar free", "zero sugar", "no sugar")),
    ("low_sugar", ("low sugar",)),
    ("low_fat", ("low fat",)),
    ("low_sodium", ("low sodium", "low salt")),
    ("high_protein", ("high protein", "protein rich")),
    ("source_of_protein", ("source of protein", "protein")),
)
_COMPILED = tuple(
    (key, tuple(re.compile(rf"(?<!\w){re.escape(p)}(?:es|s)?(?!\w)") for p in pats))
    for key, pats in _PATTERNS
)


def _match(claim: str) -> str | None:
    text = normalize(claim)
    for key, pats in _COMPILED:
        if any(p.search(text) for p in pats):
            return key
    return None


def _num(v: float) -> float:
    return round(float(v), 2)


def _max_rule(key: str, value: float | None, limit: float) -> ClaimCheck:
    if value is None:
        return ClaimCheck(key, ClaimVerdict.UNVERIFIABLE, "nutrient_missing")
    if value <= limit:
        return ClaimCheck(key, ClaimVerdict.SUPPORTED, "ok")
    return ClaimCheck(
        key, ClaimVerdict.CONTRADICTED, "exceeds_limit", {"value": _num(value), "limit": _num(limit)}
    )


def _min_rule(key: str, value: float | None, limit: float) -> ClaimCheck:
    if value is None:
        return ClaimCheck(key, ClaimVerdict.UNVERIFIABLE, "nutrient_missing")
    if value >= limit:
        return ClaimCheck(key, ClaimVerdict.SUPPORTED, "ok")
    return ClaimCheck(
        key, ClaimVerdict.CONTRADICTED, "below_minimum", {"value": _num(value), "limit": _num(limit)}
    )


def _protein_pct(product: Product) -> float | None:
    n = product.per_100g
    if n.protein_g is None or not n.energy_kcal:
        return None
    return n.protein_g * 4 / n.energy_kcal * 100


def _sodium_mg(product: Product) -> float | None:
    n = product.per_100g
    if n.sodium_mg is not None:
        return n.sodium_mg
    return n.salt_g * 400 if n.salt_g is not None else None


def _no_added_sugar(product: Product, cfg: ScoringConfig) -> ClaimCheck:
    terms = added_sugar_terms(product, cfg)
    if terms:
        return ClaimCheck(
            "no_added_sugar",
            ClaimVerdict.CONTRADICTED,
            "added_sugar_ingredient",
            {"ingredients": list(terms)},
        )
    if not ingredients_known(product, cfg):
        return ClaimCheck("no_added_sugar", ClaimVerdict.UNVERIFIABLE, "ingredients_unknown")
    return ClaimCheck("no_added_sugar", ClaimVerdict.SUPPORTED, "ok")


def _evaluate(key: str, product: Product, cfg: ScoringConfig) -> ClaimCheck:
    c = cfg.thresholds["claims"]
    n = product.per_100g
    d = "drink" if product.is_drink else "food"
    rules: dict[str, Callable[[], ClaimCheck]] = {
        "no_added_sugar": lambda: _no_added_sugar(product, cfg),
        "sugar_free": lambda: _max_rule(key, n.sugars_g, c["sugar_free_max_g"]),
        "low_sugar": lambda: _max_rule(key, n.sugars_g, c["low_sugar_max_g"][d]),
        "low_fat": lambda: _max_rule(key, n.fat_g, c["low_fat_max_g"][d]),
        "low_sodium": lambda: _max_rule(key, _sodium_mg(product), c["low_sodium_max_mg"]),
        "high_protein": lambda: _min_rule(key, _protein_pct(product), c["high_protein_min_energy_pct"]),
        "source_of_protein": lambda: _min_rule(
            key, _protein_pct(product), c["source_of_protein_min_energy_pct"]
        ),
    }
    return rules[key]()


def check_claims(product: Product, cfg: ScoringConfig) -> tuple[ClaimCheck, ...]:
    out: list[ClaimCheck] = []
    for claim in product.claims:
        key = _match(claim)
        if key is not None:
            out.append(_evaluate(key, product, cfg))
    return tuple(out)
