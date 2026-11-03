"""Healthier alternatives from the same Open Food Facts category (F9).

Every grade, ``high_in`` list and member status comes from ``app.scoring.analyze`` (never an
LLM). Only products with a Nutri-Score grade STRICTLY better than the source are suggested,
never an ungraded one, ranked by grade, then sugars per 100 g (unknown last), then name; at
most 5. Price-aware ranking is v2.

For a member (Ruling M1 B2), every better-graded candidate is analysed for that member BEFORE
the top-5 cut: an ``avoid`` is never suggested, and the rest rank ok > caution > unknown, then
as above. If nothing is left the reason is ``no_better_found``.

``sort=protein`` (Plan 9 Task 6, P9-R11): candidates with STRICTLY more protein per 100 kcal
than the source (``report.protein.per_100kcal``, known on both) and a grade no worse than the
source's. Always for a member (``member_id``, else the primary member): ``avoid`` is dropped,
then ok > caution > unknown, most protein per 100 kcal, grade, name; at most 5.

Supplements (Plan 9 Task 7, P9-R10) are never suggested: a supplement source returns
``source_supplement`` (no search), and supplement candidates are dropped by both sorts.
"""

from collections.abc import Sequence
from dataclasses import dataclass
from datetime import date
from typing import Any, Literal

from sqlalchemy.ext.asyncio import AsyncSession

from app import scoring
from app.core.config import Settings
from app.core.errors import ApiError
from app.features.members.models import Member
from app.features.members.service import to_scoring_member
from app.features.products import service
from app.features.products.off_mapping import off_to_info, off_to_product
from app.features.products.schemas import AlternativeOut, AlternativesOut, AlternativesSort
from app.features.products.service import ProductLookup
from app.integrations.openfoodfacts import (
    InvalidBarcode,
    OffClient,
    OffUnavailable,
    normalize_barcode,
)

ProteinRankReason = Literal["ok", "no_better_found", "source_ungraded", "source_protein_unknown"]

MAX_ALTERNATIVES = 5
CATEGORY_PAGE_SIZE = 24
_GRADES = ("A", "B", "C", "D", "E")


@dataclass(frozen=True, slots=True)
class Candidate:
    """A product to rank; ``grade`` is the engine's (``None`` = not enough data)."""

    product: scoring.Product
    grade: str | None
    payload: dict[str, Any]


def _sort_key(c: Candidate) -> tuple[int, int, float, str]:
    sugars = c.product.per_100g.sugars_g
    return (
        _GRADES.index(c.grade or "E"),
        1 if sugars is None else 0,
        0.0 if sugars is None else sugars,
        c.product.name.casefold(),
    )


_STATUS_RANK = {"ok": 0, "caution": 1, "unknown": 2}


def _is_supplement(c: Candidate) -> bool:
    return c.product.category == scoring.Category.SUPPLEMENT


def _member_status(c: Candidate, member: scoring.Member) -> str:
    return scoring.analyze(c.product, [member]).verdicts[0].status.value


def rank_alternatives(
    source_grade: str | None,
    candidates: Sequence[Candidate],
    member: scoring.Member | None = None,
) -> list[Candidate]:
    """Strictly better graded candidates, best first, at most 5. Pure.

    A source with no grade has nothing to compare against: no candidates. With ``member``,
    candidates the engine rates ``avoid`` for that member are dropped before the cut, and the
    rest are ordered ok > caution > unknown first.
    """
    if source_grade not in _GRADES:
        return []
    bar = _GRADES.index(source_grade)
    better = [
        c
        for c in candidates
        if not _is_supplement(c) and c.grade in _GRADES and _GRADES.index(c.grade) < bar
    ]
    if member is None:
        return sorted(better, key=_sort_key)[:MAX_ALTERNATIVES]
    rated = [(_member_status(c, member), c) for c in better]
    safe = [(status, c) for status, c in rated if status in _STATUS_RANK]  # drops avoid
    safe.sort(key=lambda sc: (_STATUS_RANK[sc[0]], *_sort_key(sc[1])))
    return [c for _, c in safe[:MAX_ALTERNATIVES]]


def _per_100kcal(product: scoring.Product) -> float | None:
    """The engine's ``report.protein.per_100kcal`` (no second calculation)."""
    return scoring.analyze(product, []).report.protein.per_100kcal


def rank_alternatives_by_protein(
    source: scoring.Product,
    candidates: Sequence[Candidate],
    member: scoring.Member,
) -> tuple[list[Candidate], ProteinRankReason]:
    """Higher-protein candidates for ``member``, best first, at most 5, and the reason. Pure.

    The source needs a protein per 100 kcal (else ``source_protein_unknown``) and a grade
    (else ``source_ungraded``). Candidates need a known protein per 100 kcal strictly above
    the source's and a known grade no worse than the source's; ``avoid`` for ``member`` is
    dropped. Order: ok > caution > unknown, protein per 100 kcal (high first), grade, name.
    """
    report = scoring.analyze(source, []).report
    bar_protein = report.protein.per_100kcal
    if bar_protein is None:
        return [], "source_protein_unknown"
    source_grade = report.nutriscore.grade
    if source_grade not in _GRADES:
        return [], "source_ungraded"
    bar_grade = _GRADES.index(source_grade)
    ranked: list[tuple[tuple[int, float, int, str], Candidate]] = []
    for c in candidates:
        if _is_supplement(c):
            continue
        if c.grade not in _GRADES or _GRADES.index(c.grade) > bar_grade:
            continue
        per_100kcal = _per_100kcal(c.product)
        if per_100kcal is None or per_100kcal <= bar_protein:
            continue
        status = _member_status(c, member)
        if status not in _STATUS_RANK:  # avoid
            continue
        key = (
            _STATUS_RANK[status],
            -per_100kcal,
            _GRADES.index(c.grade),
            c.product.name.casefold(),
        )
        ranked.append((key, c))
    ranked.sort(key=lambda kc: kc[0])
    items = [c for _, c in ranked[:MAX_ALTERNATIVES]]
    return items, ("ok" if items else "no_better_found")


def source_category(payload: dict[str, Any] | None) -> str | None:
    """The most specific OFF category: the LAST ``categories_tags`` entry (None if absent)."""
    if not isinstance(payload, dict):
        return None
    product = payload.get("product") if isinstance(payload.get("product"), dict) else payload
    tags = product.get("categories_tags")
    if not isinstance(tags, list):
        return None
    tags = [t for t in tags if isinstance(t, str) and t.strip()]
    return tags[-1].strip() if tags else None


def _barcode(payload: dict[str, Any]) -> str | None:
    info = off_to_info(payload)
    try:
        return normalize_barcode(info.barcode) if info.barcode else None
    except InvalidBarcode:
        return None


def _candidates(
    payloads: Sequence[dict[str, Any]], exclude: str | None, settings: Settings
) -> list[Candidate]:
    """OFF search payloads -> candidates. Products with no valid barcode (cannot be opened or
    checked) or no name are skipped, and so is the source itself (``exclude``)."""
    out: list[Candidate] = []
    seen: set[str] = set()
    for payload in payloads:
        barcode = _barcode(payload)
        name = off_to_info(payload).name
        if barcode is None or not name or barcode == exclude or barcode in seen:
            continue
        seen.add(barcode)
        product = off_to_product(payload, confidence=settings.off_data_confidence)
        clean, _ = product.sanitized()  # rank on the values the engine grades
        grade = scoring.analyze(product, []).report.nutriscore.grade
        out.append(Candidate(product=clean, grade=grade, payload=payload))
    return out


def _to_out(c: Candidate, member: scoring.Member | None) -> AlternativeOut:
    info = off_to_info(c.payload)
    result = scoring.analyze(c.product, [member] if member is not None else [])
    protein = result.report.protein
    return AlternativeOut(
        barcode=_barcode(c.payload),
        product_id=None,
        name=info.name or c.product.name,
        brand=info.brand,
        image_url=info.image_url,
        grade=c.grade,  # type: ignore[arg-type]  (ranked candidates are always graded)
        sugars_g=c.product.per_100g.sugars_g,
        protein_g=protein.per_100g,
        protein_per_100kcal=protein.per_100kcal,
        high_in=list(result.report.high_in),
        member_status=result.verdicts[0].status.value if member is not None else None,
        attribution=service.OFF_ATTRIBUTION,
    )


async def find_alternatives(
    session: AsyncSession,
    off: OffClient,
    found: ProductLookup,
    *,
    member: Member | None,
    settings: Settings,
    today: date,
    sort: AlternativesSort = AlternativesSort.GRADE,
) -> AlternativesOut:
    """Alternatives for ``found`` (does not commit; the caller commits the cache write).

    The category comes from the cached OFF payload for the product's barcode, so a label-only
    product (no barcode, or one OFF does not know) returns ``no_category``. With
    ``sort="protein"`` the caller passes the member to rank for (member_id or the primary).
    """
    if found.product.category == scoring.Category.SUPPLEMENT:
        return AlternativesOut(items=[], reason="source_supplement")
    payload = await service.off_payload(session, found.info.barcode or None)
    category = source_category(payload)
    if category is None:
        return AlternativesOut(items=[], reason="no_category")
    report = scoring.analyze(found.product, []).report
    if sort == AlternativesSort.PROTEIN and report.protein.per_100kcal is None:
        return AlternativesOut(items=[], reason="source_protein_unknown")
    source_grade = report.nutriscore.grade
    if source_grade is None:
        return AlternativesOut(items=[], reason="source_ungraded")

    try:
        payloads = await service.cached_off_search(
            session,
            f"category:{category}",
            lambda: off.search_by_category(category, page_size=CATEGORY_PAGE_SIZE),
        )
    except OffUnavailable as exc:
        raise ApiError("off_unavailable", 503) from exc

    scoring_member = to_scoring_member(member, today=today) if member is not None else None
    candidates = _candidates(payloads, found.info.barcode or None, settings)
    if sort == AlternativesSort.PROTEIN:
        if scoring_member is None:
            raise ValueError("sort=protein needs a member (member_id or the primary member)")
        ranked, reason = rank_alternatives_by_protein(found.product, candidates, scoring_member)
        return AlternativesOut(items=[_to_out(c, scoring_member) for c in ranked], reason=reason)
    ranked = rank_alternatives(source_grade, candidates, scoring_member)
    if not ranked:
        return AlternativesOut(items=[], reason="no_better_found")
    return AlternativesOut(items=[_to_out(c, scoring_member) for c in ranked], reason="ok")
