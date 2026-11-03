"""Front-of-pack claim checking against label data."""

from __future__ import annotations

import re
import unicodedata
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
    # Plan 9 Task 4: matched before high_protein and source_of_protein. protein_amount has
    # no phrases: it is matched by _PROTEIN_AMOUNT (a number + g + protein).
    ("protein_amount", ()),
    ("whey_only", ("100% whey", "pure whey")),
    ("whey_protein", ("whey", "whey protein")),
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


_NUM = r"(\d+(?:[.,]\d+)?)"
_GRAMS = r"(?:g|gm|gms|gram|grams)"
# "24g protein", "24 g of protein", "24g whey protein", "protein: 24 g". Matched on the
# lower-cased NFKC text (normalize() would turn "24.5" into "24 5").
_PROTEIN_AMOUNT = (
    re.compile(rf"(?<![\d.,]){_NUM}\s*{_GRAMS}\s+(?:of\s+)?(?:whey\s+)?protein(?![a-z])"),
    re.compile(rf"(?<![a-z])protein\s*[:\-]?\s*{_NUM}\s*{_GRAMS}(?![a-z])"),
)
_PER_SERVING = re.compile(r"(?<![a-z])(?:serving|servings|scoop|scoops|serve|serves)(?![a-z])")
# A package unit (P9 safety S2) is read per serving too, but the serving may be only part of a
# bar or pack, so a shortfall there is `basis_unknown` (unverifiable), never a contradiction.
_PER_UNIT = re.compile(
    r"(?<![a-z])(?:bars?|packs?|packets?|sachets?|bottles?|pieces?|pcs|cups?)(?![a-z])"
)
_PER_100 = re.compile(r"(?:per|/|every|each|in)\s*100\s*(?:g|gm|gms|grams?|ml)(?![a-z])")


def _claim_text(claim: str) -> str:
    return unicodedata.normalize("NFKC", claim).lower()


def _protein_amount(claim: str) -> float | None:
    """The claimed grams of protein, or None when the claim states no amount."""
    text = _claim_text(claim)
    for pattern in _PROTEIN_AMOUNT:
        m = pattern.search(text)
        if m:
            return float(m.group(1).replace(",", "."))
    return None


# A negated whey phrase (P9 safety S3) is not a whey claim: "whey free", "whey-free", "no whey",
# "free from whey", "without whey", "0% whey", "whey protein free". Matched on the normalised
# text (punctuation and "%" become spaces) and removed before matching, so the rest of the claim
# ("whey-free high protein") is still checked.
_NEGATED_WHEY = re.compile(
    r"(?<!\w)(?:(?:contains\s+)?no|zero|0|without|free\s+(?:from|of))\s+whey(?:\s+protein)?(?!\w)"
    r"|(?<!\w)whey(?:\s+protein)?\s+free(?!\w)"
)


def _match(claim: str) -> str | None:
    text = _NEGATED_WHEY.sub(" ", normalize(claim))
    for key, pats in _COMPILED:
        if key == "protein_amount":
            if _protein_amount(claim) is not None:
                return key
            continue
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


def _protein_amount_check(claim: str, product: Product, cfg: ScoringConfig) -> ClaimCheck:
    """The claimed grams vs the table, on the basis the claim names (P9 safety S2):

    - serving / scoop / serve: per serving; contradicted when short.
    - "per 100 g" (or "/100g", "in 100 g"): per 100 g; contradicted when short.
    - a package unit (bar, pack, sachet, bottle, piece, cup): per serving, but the serving
      may be part of the unit, so a shortfall is unverifiable (`basis_unknown`).
    - no basis: supported when the per-100 g or the per-serving value meets the claim, else
      unverifiable (`basis_unknown`). Never contradicted.

    "Short" means more than `protein_amount_shortfall_pct` % below the claim.
    """
    key = "protein_amount"
    claimed = _protein_amount(claim)
    protein = product.per_100g.protein_g
    if claimed is None or protein is None:
        return _missing(key, "protein_g")
    text = _claim_text(claim)
    floor = claimed * (1 - cfg.thresholds["claims"]["protein_amount_shortfall_pct"] / 100)
    serving = product.serving_size_g
    per_serving = None if serving is None else protein * serving / 100
    unclear = ClaimCheck(key, ClaimVerdict.UNVERIFIABLE, "basis_unknown")
    if _PER_SERVING.search(text) or _PER_UNIT.search(text):
        if per_serving is None:
            return _missing(key, "serving_size_g")
        if per_serving >= floor:
            return ClaimCheck(key, ClaimVerdict.SUPPORTED, "ok")
        if not _PER_SERVING.search(text):
            return unclear
        value, basis = per_serving, "per_serving"
    elif _PER_100.search(text):
        if protein >= floor:
            return ClaimCheck(key, ClaimVerdict.SUPPORTED, "ok")
        value, basis = protein, "per_100g"
    else:
        if protein >= floor or (per_serving is not None and per_serving >= floor):
            return ClaimCheck(key, ClaimVerdict.SUPPORTED, "ok")
        return unclear
    return ClaimCheck(
        key,
        ClaimVerdict.CONTRADICTED,
        "below_claimed",
        {"value": _num(value), "claimed": _num(claimed), "basis": basis},
    )


def _whey_listed(product: Product, cfg: ScoringConfig) -> bool:
    return bool(find_terms(product.ingredients, cfg.thresholds["claims"]["whey_terms"]))


def _whey_only(product: Product, cfg: ScoringConfig) -> ClaimCheck:
    """The "100% whey" claim: no other protein source, and whey listed. A found term is
    evidence at any confidence; a supported verdict needs known ingredients."""
    key = "whey_only"
    others = find_terms(product.ingredients, cfg.thresholds["claims"]["other_protein_terms"])
    if others:
        return ClaimCheck(
            key, ClaimVerdict.CONTRADICTED, "other_protein_source", {"ingredients": others}
        )
    if not ingredients_known(product, cfg):
        return ClaimCheck(key, ClaimVerdict.UNVERIFIABLE, "ingredients_unknown")
    if not _whey_listed(product, cfg):
        return ClaimCheck(key, ClaimVerdict.CONTRADICTED, "whey_not_listed")
    return ClaimCheck(key, ClaimVerdict.SUPPORTED, "ok")


def _whey_protein(product: Product, cfg: ScoringConfig) -> ClaimCheck:
    key = "whey_protein"
    if not ingredients_known(product, cfg):
        return ClaimCheck(key, ClaimVerdict.UNVERIFIABLE, "ingredients_unknown")
    if not _whey_listed(product, cfg):
        return ClaimCheck(key, ClaimVerdict.CONTRADICTED, "whey_not_listed")
    return ClaimCheck(key, ClaimVerdict.SUPPORTED, "ok")


def _evaluate(key: str, claim: str, product: Product, cfg: ScoringConfig) -> ClaimCheck:
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
        "protein_amount": lambda: _protein_amount_check(claim, product, cfg),
        "whey_only": lambda: _whey_only(product, cfg),
        "whey_protein": lambda: _whey_protein(product, cfg),
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
            out.append(_evaluate(key, claim, product, cfg))
    return tuple(out)
