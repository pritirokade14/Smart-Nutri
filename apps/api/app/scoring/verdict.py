from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import asdict, dataclass
from decimal import ROUND_HALF_UP, Decimal
from enum import Enum
from typing import Any

from app.scoring.allergens import allergen_reasons, detect_allergens, ingredients_known
from app.scoring.claims import ClaimCheck, check_claims
from app.scoring.conditions import condition_reasons
from app.scoring.config import ScoringConfig, load_config
from app.scoring.custom_alerts import custom_alert_reasons
from app.scoring.diet import diet_reasons, diet_violations, veg_mark_mismatch
from app.scoring.ingredients import find_terms
from app.scoring.models import (
    AllergenState,
    Diet,
    Member,
    Product,
    ProteinFacts,
    Reason,
    Status,
)
from app.scoring.nutriscore import NutriScoreResult, compute_nutriscore
from app.scoring.warnings import hidden_sugars, high_in, ingredient_hits, sodium_additives

# Listed in `sweeteners` when only the Open Food Facts flag (no ingredient term) says so.
SWEETENER_FLAG = "contains_sweeteners"


@dataclass(frozen=True, slots=True)
class ProductReport:
    nutriscore: NutriScoreResult
    high_in: tuple[str, ...]
    allergens: Mapping[str, AllergenState]
    ingredients_known: bool
    diet_violations: Mapping[Diet, tuple[str, ...]]
    veg_mark_mismatch: bool
    hidden_sugars: tuple[str, ...]
    sodium_additives: tuple[str, ...]
    claims: tuple[ClaimCheck, ...]
    dropped_fields: tuple[str, ...]
    # Protein guide (Plan 9 Task 4, P9-R12): information only, never a verdict input.
    protein: ProteinFacts
    sweeteners: tuple[str, ...]  # custom_alerts.artificial_sweetener terms, or SWEETENER_FLAG
    caffeine: tuple[str, ...]  # ingredients.yaml `caffeine` terms


@dataclass(frozen=True, slots=True)
class MemberVerdict:
    member_id: str
    status: Status
    reasons: tuple[Reason, ...]


def _jsonable(value: Any) -> Any:
    if isinstance(value, Enum):
        return value.value
    if isinstance(value, Mapping):
        return {str(_jsonable(k)): _jsonable(v) for k, v in value.items()}
    if isinstance(value, (list, tuple, set, frozenset)):
        return [_jsonable(v) for v in value]
    return value


@dataclass(frozen=True, slots=True)
class AnalysisResult:
    report: ProductReport
    verdicts: tuple[MemberVerdict, ...]

    def to_dict(self) -> dict[str, Any]:
        return _jsonable(
            {"report": asdict(self.report), "verdicts": [asdict(v) for v in self.verdicts]}
        )


def round1(value: float | None) -> float | None:
    """1 dp, half up (6.25 -> 6.3), so every client shows the same number."""
    if value is None:
        return None
    return float(Decimal(repr(float(value))).quantize(Decimal("0.1"), rounding=ROUND_HALF_UP))


def protein_facts(product: Product) -> ProteinFacts:
    """Protein per 100 g, per serving and per 100 kcal from a SANITISED product."""
    n = product.per_100g
    protein, kcal = n.protein_g, n.energy_kcal
    per_100kcal = None if protein is None or not kcal else protein * 100 / kcal
    return ProteinFacts(
        per_100g=round1(protein),
        per_serving=round1(product.per_serving(protein)),
        per_100kcal=round1(per_100kcal),
        serving_size_g=round1(product.serving_size_g),
    )


def sweeteners(product: Product, cfg: ScoringConfig) -> tuple[str, ...]:
    """Sweetener terms in the ingredients; SWEETENER_FLAG when only the OFF flag says so."""
    entry = cfg.ingredient_lists["custom_alerts"]["artificial_sweetener"]
    terms = find_terms(product.ingredients, entry["terms"], entry.get("exclude") or ())
    if terms:
        return tuple(sorted(terms))
    return (SWEETENER_FLAG,) if product.contains_sweeteners else ()


def _sanitize(product: Product) -> tuple[Product, tuple[str, ...]]:
    return product.sanitized()


def _build(
    product: Product, cfg: ScoringConfig, dropped: tuple[str, ...], extra_keys: Sequence[str]
) -> ProductReport:
    return ProductReport(
        nutriscore=compute_nutriscore(product),
        high_in=high_in(product, cfg),
        allergens=detect_allergens(product, cfg, extra_keys),
        ingredients_known=ingredients_known(product, cfg),
        diet_violations=diet_violations(product, cfg),
        veg_mark_mismatch=veg_mark_mismatch(product, cfg),
        hidden_sugars=hidden_sugars(product, cfg),
        sodium_additives=sodium_additives(product, cfg),
        claims=check_claims(product, cfg),
        dropped_fields=dropped,
        protein=protein_facts(product),
        sweeteners=sweeteners(product, cfg),
        caffeine=ingredient_hits(product, cfg, "caffeine"),
    )


def build_report(product: Product, cfg: ScoringConfig) -> ProductReport:
    clean, dropped = _sanitize(product)
    return _build(clean, cfg, dropped, ())


def _freeze(value: Any) -> Any:
    if isinstance(value, Mapping):
        return tuple(sorted(((str(k), _freeze(v)) for k, v in value.items()), key=lambda kv: kv[0]))
    if isinstance(value, (list, tuple)):
        return tuple(_freeze(v) for v in value)
    if isinstance(value, (set, frozenset)):
        return frozenset(_freeze(v) for v in value)
    return value


def _dedupe(reasons: Sequence[Reason]) -> tuple[Reason, ...]:
    ordered = sorted(reasons, key=lambda r: (-r.severity.rank, r.code))
    seen: set[tuple[Any, ...]] = set()
    out: list[Reason] = []
    for r in ordered:
        key = (r.code, r.severity, _freeze(r.params))
        if key in seen:
            continue
        seen.add(key)
        out.append(r)
    return tuple(out)


def evaluate_member(
    product: Product, report: ProductReport, member: Member, cfg: ScoringConfig
) -> MemberVerdict:
    product, _ = _sanitize(product)
    reasons = _dedupe(
        [
            *allergen_reasons(product, member, cfg),
            *diet_reasons(product, member, cfg),
            *condition_reasons(product, member, report.nutriscore, report.claims, cfg),
            *custom_alert_reasons(product, member, cfg),
        ]
    )
    status = Status.worst(r.severity for r in reasons)
    return MemberVerdict(member_id=member.id, status=status, reasons=reasons)


def analyze(
    product: Product, members: Sequence[Member], cfg: ScoringConfig | None = None
) -> AnalysisResult:
    if cfg is None:
        cfg = load_config()
    clean, dropped = _sanitize(product)
    extra = [a for m in members for a in m.allergens]
    report = _build(clean, cfg, dropped, extra)
    verdicts = tuple(evaluate_member(clean, report, m, cfg) for m in members)
    return AnalysisResult(report=report, verdicts=verdicts)
