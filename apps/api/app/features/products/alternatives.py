"""Healthier alternatives from the same Open Food Facts category (F9).

Every grade, ``high_in`` list and member status comes from ``app.scoring.analyze`` (never an
LLM). Only products with a Nutri-Score grade STRICTLY better than the source are suggested,
never an ungraded one, ranked by grade, then sugars per 100 g (unknown last), then name; at
most 5. Price-aware ranking is v2.

For a member (Ruling M1 B2), every better-graded candidate is analysed for that member BEFORE
the top-5 cut: an ``avoid`` is never suggested, and the rest rank ok > caution > unknown, then
as above. If nothing is left the reason is ``no_better_found``.
"""

from collections.abc import Sequence
from dataclasses import dataclass
from datetime import date
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app import scoring
from app.core.config import Settings
from app.core.errors import ApiError
from app.features.members.models import Member
from app.features.members.service import to_scoring_member
from app.features.products import service
from app.features.products.off_mapping import off_to_info, off_to_product
from app.features.products.schemas import AlternativeOut, AlternativesOut
from app.features.products.service import ProductLookup
from app.integrations.openfoodfacts import (
    InvalidBarcode,
    OffClient,
    OffUnavailable,
    normalize_barcode,
)

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
    better = [c for c in candidates if c.grade in _GRADES and _GRADES.index(c.grade) < bar]
    if member is None:
        return sorted(better, key=_sort_key)[:MAX_ALTERNATIVES]
    rated = [(_member_status(c, member), c) for c in better]
    safe = [(status, c) for status, c in rated if status in _STATUS_RANK]  # drops avoid
    safe.sort(key=lambda sc: (_STATUS_RANK[sc[0]], *_sort_key(sc[1])))
    return [c for _, c in safe[:MAX_ALTERNATIVES]]


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
    return AlternativeOut(
        barcode=_barcode(c.payload),
        product_id=None,
        name=info.name or c.product.name,
        brand=info.brand,
        image_url=info.image_url,
        grade=c.grade,  # type: ignore[arg-type]  (ranked candidates are always graded)
        sugars_g=c.product.per_100g.sugars_g,
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
) -> AlternativesOut:
    """Alternatives for ``found`` (does not commit; the caller commits the cache write).

    The category comes from the cached OFF payload for the product's barcode, so a label-only
    product (no barcode, or one OFF does not know) returns ``no_category``.
    """
    payload = await service.off_payload(session, found.info.barcode or None)
    category = source_category(payload)
    if category is None:
        return AlternativesOut(items=[], reason="no_category")
    source_grade = scoring.analyze(found.product, []).report.nutriscore.grade
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
    ranked = rank_alternatives(
        source_grade,
        _candidates(payloads, found.info.barcode or None, settings),
        scoring_member,
    )
    if not ranked:
        return AlternativesOut(items=[], reason="no_better_found")
    return AlternativesOut(items=[_to_out(c, scoring_member) for c in ranked], reason="ok")
