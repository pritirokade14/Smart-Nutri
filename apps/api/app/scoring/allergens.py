"""Tri-state allergen detection (safety-critical: unknown is never OK)."""

from __future__ import annotations

import re
from collections.abc import Iterable

from app.scoring.config import ScoringConfig
from app.scoring.ingredients import find_terms
from app.scoring.models import AllergenState, Member, Product, Reason, Status

# Common member-entered variants mapped to config keys (after _norm_key).
_ALIASES = {
    "dairy": "milk",
    "lactose": "milk",
    "nuts": "tree_nut",
    "tree_nuts": "tree_nut",
    "shellfish": "crustacean",
    "crustaceans": "crustacean",
    "wheat": "gluten",
    "groundnut": "peanut",
    "peanuts": "peanut",
    "soya": "soy",
    "sulfite": "sulphite",
    "sulfites": "sulphite",
    "sulphites": "sulphite",
    "eggs": "egg",
}


def _norm_key(key: str) -> str:
    k = re.sub(r"[\s\-]+", "_", key.strip().lower())
    return _ALIASES.get(k, k)


def ingredients_known(product: Product, cfg: ScoringConfig) -> bool:
    return any(i.strip() for i in product.ingredients) and (
        product.extraction_confidence >= cfg.thresholds["min_extraction_confidence"]
    )


def _detect_one(product: Product, entry: dict[str, list[str]]) -> AllergenState | None:
    contains = list(entry.get("contains", []))
    possible = list(entry.get("possible", []))
    exclude = list(entry.get("exclude", []))
    main = list(product.ingredients)
    if product.allergen_statement:
        main.append(product.allergen_statement)
    if main and find_terms(main, contains, exclude):
        return AllergenState.CONTAINS
    if possible and main and find_terms(main, possible, exclude):
        return AllergenState.MAY_CONTAIN
    if product.may_contain_statement and find_terms(
        [product.may_contain_statement], contains + possible, exclude
    ):
        return AllergenState.MAY_CONTAIN
    return None


def detect_allergens(
    product: Product, cfg: ScoringConfig, extra_keys: Iterable[str] = ()
) -> dict[str, AllergenState]:
    entries: dict[str, dict[str, list[str]]] = {k.lower(): dict(v) for k, v in cfg.allergens.items()}
    for key in extra_keys:
        k = _norm_key(key)
        if k and k not in entries:
            entries[k] = {"contains": [k.replace("_", " ")], "possible": [], "exclude": []}
    found: dict[str, AllergenState] = {}
    for key, entry in entries.items():
        state = _detect_one(product, entry)
        if state is not None:
            found[key] = state
    return found


def allergen_reasons(product: Product, member: Member, cfg: ScoringConfig) -> list[Reason]:
    keys = list(dict.fromkeys(_norm_key(a) for a in member.allergens if a.strip()))
    if not keys:
        return []
    detected = detect_allergens(product, cfg, keys)
    known = ingredients_known(product, cfg)
    may_status = Status(cfg.thresholds.get("allergen_may_contain_status", "avoid"))
    reasons: list[Reason] = []
    for key in keys:
        state = detected.get(key)
        if state == AllergenState.CONTAINS:
            reasons.append(Reason("allergen_contains", Status.AVOID, {"allergen": key}))
        elif state == AllergenState.MAY_CONTAIN:
            reasons.append(Reason("allergen_may_contain", may_status, {"allergen": key}))
        elif not known:
            reasons.append(Reason("allergen_unknown", Status.UNKNOWN, {"allergen": key}))
    return reasons
