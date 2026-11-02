"""Tri-state allergen detection (safety-critical: unknown is never OK)."""

from __future__ import annotations

from collections.abc import Collection, Iterable, Mapping
from dataclasses import dataclass

from app.scoring.config import ScoringConfig
from app.scoring.ingredients import (
    find_terms,
    has_ingredient_content,
    modifier_excludes,
    normalize,
)
from app.scoring.models import AllergenState, Member, Product, Reason, Status

# Words a member may add around an allergen name ("peanut allergy", "lactose intolerance").
_FILLER = frozenset(
    {"allergy", "allergies", "intolerance", "intolerant", "sensitivity", "sensitive"}
)

# Common member-entered variants mapped to config keys. Keys are normalised with
# _phrase() at import, so "cow's milk", "cows milk" and "Cows-Milk" all match.
# One variant may map to several canonical keys (R20).
_ALIASES: dict[str, tuple[str, ...]] = {
    "dairy": ("milk",),
    "dairy product": ("milk",),
    "milk product": ("milk",),
    "cow's milk": ("milk",),
    "cows milk": ("milk",),
    "lactose": ("milk",),
    "nut": ("tree_nut", "peanut"),
    "tree nuts": ("tree_nut",),
    "shellfish": ("crustacean",),
    "crustaceans": ("crustacean",),
    "prawn": ("crustacean",),
    "seafood": ("fish", "crustacean"),
    "wheat": ("gluten",),
    "celiac": ("gluten",),
    "coeliac": ("gluten",),
    "groundnut": ("peanut",),
    "peanut butter": ("peanut",),
    "soya": ("soy",),
    "sesame seed": ("sesame",),
    "sulfite": ("sulphite",),
    "eggs": ("egg",),
}


def _singular(word: str) -> str:
    if len(word) > 4 and word.endswith("ies"):
        return word[:-3] + "y"
    if word.endswith(("sses", "shes", "ches", "xes", "zes", "oes")):
        return word[:-2]
    if len(word) > 3 and word.endswith("s") and not word.endswith("ss"):
        return word[:-1]
    return word


def _words(key: str) -> list[str]:
    """Lowercased words of a member key with apostrophes and filler words removed."""
    text = normalize(key.replace("'", "").replace("’", "").replace("‘", ""))
    words = text.replace("_", " ").split()
    return [w for w in words if w not in _FILLER] or words


def _phrase(key: str) -> str:
    return "_".join(_singular(w) for w in _words(key))


_ALIAS_INDEX: dict[str, tuple[str, ...]] = {_phrase(k): v for k, v in _ALIASES.items()}


@dataclass(frozen=True, slots=True)
class _MemberKey:
    canonical: tuple[str, ...]  # config keys the member key maps to
    literal_key: str | None  # set when some words were not recognised
    literal_terms: tuple[str, ...]


def _lookup(phrase: str, known: Collection[str]) -> tuple[str, ...]:
    if phrase in known:
        return (phrase,)
    return tuple(k for k in _ALIAS_INDEX.get(phrase, ()) if k in known)


def _resolve(key: str, known: Collection[str]) -> _MemberKey | None:
    """Map free text to canonical keys: whole phrase, then longest word runs (R20)."""
    raw = _words(key)
    if not raw:
        return None
    words = [_singular(w) for w in raw]
    canonical: list[str] = []
    consumed = 0
    i = 0
    while i < len(words):
        for j in range(len(words), i, -1):
            hit = _lookup("_".join(words[i:j]), known)
            if hit:
                canonical.extend(hit)
                consumed += j - i
                i = j
                break
        else:
            i += 1
    if consumed == len(words):
        return _MemberKey(tuple(dict.fromkeys(canonical)), None, ())
    terms = tuple(dict.fromkeys((" ".join(raw), " ".join(words))))
    return _MemberKey(tuple(dict.fromkeys(canonical)), "_".join(words), terms)


def ingredients_known(product: Product, cfg: ScoringConfig) -> bool:
    return has_ingredient_content(product.ingredients) and (
        product.extraction_confidence >= cfg.thresholds["min_extraction_confidence"]
    )


def _partial_exclude(texts: list[str], exclude: list[str], triggers: list[str]) -> bool:
    """An exclude phrase that hides a trigger term modifies a following noun (R19, R30)."""
    return any(find_terms([hit], triggers) for hit in modifier_excludes(texts, exclude))


def _detect_one(product: Product, entry: Mapping[str, list[str]]) -> AllergenState | None:
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
    if exclude and main and _partial_exclude(main, exclude, contains + possible):
        return AllergenState.MAY_CONTAIN
    statement = product.may_contain_statement
    if statement and (
        find_terms([statement], contains + possible, exclude)
        or (exclude and _partial_exclude([statement], exclude, contains + possible))
    ):
        return AllergenState.MAY_CONTAIN
    return None


def detect_allergens(
    product: Product, cfg: ScoringConfig, extra_keys: Iterable[str] = ()
) -> dict[str, AllergenState]:
    entries: dict[str, Mapping[str, list[str]]] = {
        k.lower(): dict(v) for k, v in cfg.allergens.items()
    }
    known = set(entries)
    for key in extra_keys:
        mk = _resolve(key, known)
        if mk and mk.literal_key and mk.literal_key not in entries:
            entries[mk.literal_key] = {
                "contains": list(mk.literal_terms),
                "possible": [],
                "exclude": [],
            }
    found: dict[str, AllergenState] = {}
    for key, entry in entries.items():
        state = _detect_one(product, entry)
        if state is not None:
            found[key] = state
    return found


def _state_reasons(
    key: str, state: AllergenState | None, known: bool, may_status: Status
) -> list[Reason]:
    params = {"allergen": key}
    if state == AllergenState.CONTAINS:
        return [Reason("allergen_contains", Status.AVOID, params)]
    out: list[Reason] = []
    if state == AllergenState.MAY_CONTAIN:
        out.append(Reason("allergen_may_contain", may_status, params))
    if not known:
        out.append(Reason("allergen_unknown", Status.UNKNOWN, {"allergen": key}))
    return out


def allergen_reasons(product: Product, member: Member, cfg: ScoringConfig) -> list[Reason]:
    raw_keys = [a for a in member.allergens if a.strip()]
    known_keys = {k.lower() for k in cfg.allergens}
    resolved = [mk for mk in (_resolve(a, known_keys) for a in raw_keys) if mk]
    if not resolved:
        return []
    detected = detect_allergens(product, cfg, raw_keys)
    known = ingredients_known(product, cfg)
    may_status = Status(cfg.thresholds.get("allergen_may_contain_status", "avoid"))
    reasons: list[Reason] = []
    seen: set[str] = set()
    for mk in resolved:
        for key in mk.canonical:
            if key not in seen:
                seen.add(key)
                reasons.extend(_state_reasons(key, detected.get(key), known, may_status))
        lit = mk.literal_key
        if lit is None or lit in seen:
            continue
        seen.add(lit)
        state = detected.get(lit)
        if mk.canonical:
            # Word-level fallback ("coconut milk" -> milk): the literal phrase is an
            # extra check, reported only when it adds a hit the canonical keys missed.
            if state and not any(detected.get(k) == AllergenState.CONTAINS for k in mk.canonical):
                reasons.extend(_state_reasons(lit, state, True, may_status))
            continue
        reasons.extend(_state_reasons(lit, state, known, may_status))
        if state != AllergenState.CONTAINS:
            reasons.append(Reason("allergen_unrecognised", Status.UNKNOWN, {"allergen": lit}))
    return reasons
