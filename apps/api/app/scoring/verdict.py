from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import asdict, dataclass, replace
from enum import Enum
from typing import Any

from app.scoring.allergens import allergen_reasons, detect_allergens, ingredients_known
from app.scoring.claims import ClaimCheck, check_claims
from app.scoring.conditions import condition_reasons
from app.scoring.config import ScoringConfig, load_config
from app.scoring.diet import diet_reasons, diet_violations, veg_mark_mismatch
from app.scoring.models import AllergenState, Diet, Member, Product, Reason, Status
from app.scoring.nutriscore import NutriScoreResult, compute_nutriscore
from app.scoring.warnings import hidden_sugars, high_in, sodium_additives


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


def _sanitize(product: Product) -> tuple[Product, tuple[str, ...]]:
    clean, dropped = product.per_100g.sanitized()
    return replace(product, per_100g=clean), dropped


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
    )


def build_report(product: Product, cfg: ScoringConfig) -> ProductReport:
    clean, dropped = _sanitize(product)
    return _build(clean, cfg, dropped, ())


def _dedupe(reasons: Sequence[Reason]) -> tuple[Reason, ...]:
    ordered = sorted(reasons, key=lambda r: (-r.severity.rank, r.code))
    seen: set[tuple[Any, ...]] = set()
    out: list[Reason] = []
    for r in ordered:
        key = (
            r.code,
            r.severity,
            r.params.get("nutrient"),
            r.params.get("allergen"),
            r.params.get("diet"),
        )
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
        ]
    )
    status = max((r.severity for r in reasons), key=lambda s: s.rank, default=Status.OK)
    return MemberVerdict(member_id=member.id, status=status, reasons=reasons)


def analyze(
    product: Product, members: Sequence[Member], cfg: ScoringConfig | None = None
) -> AnalysisResult:
    cfg = cfg or load_config()
    clean, dropped = _sanitize(product)
    extra = [a for m in members for a in m.allergens]
    report = _build(clean, cfg, dropped, extra)
    verdicts = tuple(evaluate_member(clean, report, m, cfg) for m in members)
    return AnalysisResult(report=report, verdicts=verdicts)
