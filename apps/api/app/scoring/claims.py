"""Front-of-pack claim checking against label data."""

from __future__ import annotations

import re
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass, field
from typing import Any

from app.scoring.allergens import ingredients_known
from app.scoring.config import ScoringConfig
from app.scoring.ingredients import find_terms, normalize
from app.scoring.models import ClaimVerdict, Product
from app.scoring.warnings import added_sugar_terms


@dataclass(frozen=True, slots=True)
class ClaimCheck:
    claim: str
    verdict: ClaimVerdict
    reason_code: str
    params: Mapping[str, Any] = field(default_factory=dict)


# Ordered: first matching key wins. Patterns are normalised like the claim text
# (so "0% sugar" matches as "0 sugar").
_PATTERNS: tuple[tuple[str, tuple[str, ...]], ...] = (
    (
        "no_added_sugar",
        (
            "no added sugar",
            "no sugar added",
            "zero added sugar",
            "without added sugar",
            "added sugar free",
            "0% added sugar",
            "no added sugar or sweeteners",
        ),
    ),
    ("no_refined_sugar", ("no refined sugar", "no refined sugar added")),
    (
        "sugar_free",
        (
            "sugar free",
            "zero sugar",
            "no sugar",
            "sugarfree",
            "sugarless",
            "0% sugar",
            "0g sugar",
            "0 g sugar",
        ),
    ),
    ("low_sugar", ("low sugar",)),
    ("low_fat", ("low fat",)),
    ("low_sodium", ("low sodium", "low salt")),
    (
        "diabetic_friendly",
        (
            "diabetic friendly",
            "diabetes friendly",
            "suitable for diabetics",
            "low gi",
            "low glycemic",
        ),
    ),
    (
        "high_protein",
        ("high protein", "high in protein", "protein rich", "rich in protein"),
    ),
    ("source_of_protein", ("source of protein", "protein")),
)
_COMPILED = tuple(
    (key, tuple(re.compile(rf"(?<!\w){re.escape(normalize(p))}(?:es|s)?(?!\w)") for p in pats))
    for key, pats in _PATTERNS
)


def _match(claim: str) -> str | None:
    text = normalize(claim)
    for key, pats in _COMPILED:
        if any(p.search(text) for p in pats):
            return key
    return None


def _num(v: float) -> float:
    return round(float(v), 3)


def _missing(key: str, nutrient: str) -> ClaimCheck:
    return ClaimCheck(key, ClaimVerdict.UNVERIFIABLE, "nutrient_missing", {"nutrient": nutrient})


def _max_rule(key: str, value: float | None, limit: float, nutrient: str) -> ClaimCheck:
    if value is None:
        return _missing(key, nutrient)
    if value <= limit:
        return ClaimCheck(key, ClaimVerdict.SUPPORTED, "ok")
    return ClaimCheck(
        key,
        ClaimVerdict.CONTRADICTED,
        "exceeds_limit",
        {"value": _num(value), "limit": _num(limit)},
    )


def _min_rule(key: str, value: float | None, limit: float, nutrient: str) -> ClaimCheck:
    if value is None:
        return _missing(key, nutrient)
    if value >= limit:
        return ClaimCheck(key, ClaimVerdict.SUPPORTED, "ok")
    return ClaimCheck(
        key,
        ClaimVerdict.CONTRADICTED,
        "below_minimum",
        {"value": _num(value), "limit": _num(limit)},
    )


def _protein_pct(product: Product) -> float | None:
    n = product.per_100g
    if n.protein_g is None or not n.energy_kcal:
        return None
    return n.protein_g * 4 / n.energy_kcal * 100


def _protein_nutrient(product: Product) -> str:
    return "protein_g" if product.per_100g.protein_g is None else "energy_kcal"


def _sodium_mg(product: Product) -> float | None:
    """Sodium in mg; the higher of sodium and salt-derived sodium wins (consistent with R22)."""
    n = product.per_100g
    candidates = [
        v for v in (n.sodium_mg, None if n.salt_g is None else n.salt_g * 400) if v is not None
    ]
    return max(candidates) if candidates else None


def _ingredient_rule(
    key: str, product: Product, cfg: ScoringConfig, terms: Sequence[str], reason_code: str
) -> ClaimCheck:
    if terms:
        return ClaimCheck(key, ClaimVerdict.CONTRADICTED, reason_code, {"ingredients": list(terms)})
    if not ingredients_known(product, cfg):
        return ClaimCheck(key, ClaimVerdict.UNVERIFIABLE, "ingredients_unknown")
    return ClaimCheck(key, ClaimVerdict.SUPPORTED, "ok")


def _no_added_sugar(product: Product, cfg: ScoringConfig) -> ClaimCheck:
    terms = added_sugar_terms(product, cfg)
    return _ingredient_rule("no_added_sugar", product, cfg, terms, "added_sugar_ingredient")


def _no_refined_sugar(product: Product, cfg: ScoringConfig) -> ClaimCheck:
    c = cfg.thresholds["claims"]
    terms = find_terms(
        product.ingredients, c["refined_sugar_terms"], c.get("unrefined_sugar_excludes", ())
    )
    return _ingredient_rule("no_refined_sugar", product, cfg, terms, "refined_sugar_ingredient")


def _evaluate(key: str, product: Product, cfg: ScoringConfig) -> ClaimCheck:
    c = cfg.thresholds["claims"]
    n = product.per_100g
    d = "drink" if product.is_drink else "food"
    rules: dict[str, Callable[[], ClaimCheck]] = {
        "no_added_sugar": lambda: _no_added_sugar(product, cfg),
        "no_refined_sugar": lambda: _no_refined_sugar(product, cfg),
        "sugar_free": lambda: _max_rule(key, n.sugars_g, c["sugar_free_max_g"], "sugars_g"),
        "low_sugar": lambda: _max_rule(key, n.sugars_g, c["low_sugar_max_g"][d], "sugars_g"),
        "low_fat": lambda: _max_rule(key, n.fat_g, c["low_fat_max_g"][d], "fat_g"),
        "low_sodium": lambda: _max_rule(
            key, _sodium_mg(product), c["low_sodium_max_mg"], "sodium_mg"
        ),
        # No legal standard for these phrases: never verifiable from the label.
        "diabetic_friendly": lambda: ClaimCheck(key, ClaimVerdict.UNVERIFIABLE, "no_standard"),
        "high_protein": lambda: _min_rule(
            key, _protein_pct(product), c["high_protein_min_energy_pct"], _protein_nutrient(product)
        ),
        "source_of_protein": lambda: _min_rule(
            key,
            _protein_pct(product),
            c["source_of_protein_min_energy_pct"],
            _protein_nutrient(product),
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
