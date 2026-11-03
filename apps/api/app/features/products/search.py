"""Product search: our own catalogue first, then Open Food Facts text search (F9).

Our products the caller may see (verified, plus their own pending ones; never another
account's pending or any rejected product) match on name or brand. OFF hits are de-duplicated
by barcode (ours win) and the OFF result is cached 24 h per normalised query. Grades come from
the rules engine. OFF being down is not an error: our hits are returned alone. Over the
process-wide OFF search budget (I4, `off_search_per_minute`), a cached result (even a stale
one) is served; with none, our own hits are returned with `off_degraded=true`, and only
with no hits of ours either is it 503 `off_unavailable` with Retry-After.

Plan 9 Task 6: every hit carries ``report.protein`` (per 100 g and per 100 kcal). With a
member, hits carry that member's status from the engine. ``sort="protein"`` (always with a
member: member_id or the primary) drops ``avoid`` hits and supplements (Plan 9 Task 7) and
orders by protein per 100 kcal, highest first, unknown last (stable otherwise).
``sort="relevance"`` keeps every hit, supplements included (ungraded).
"""

import unicodedata
from uuid import UUID

from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app import scoring
from app.core.config import Settings
from app.core.errors import ApiError
from app.features.products import service
from app.features.products.models import Product
from app.features.products.off_mapping import off_to_info, off_to_product
from app.features.products.schemas import SearchHit, SearchSort
from app.integrations.openfoodfacts import (
    InvalidBarcode,
    OffClient,
    OffThrottled,
    OffUnavailable,
    normalize_barcode,
)

# I4: at least 3 characters after normalising (clients search on submit, or from 3
# characters after a 600 ms pause).
MIN_QUERY, MAX_QUERY = 3, 80
OFF_PAGE_SIZE = 24


def normalise_query(q: str) -> str:
    """NFKC, collapse whitespace and casefold (also the OFF cache key), so that case,
    spacing and full-width or compatibility forms of the same query share one cache entry."""
    return " ".join(unicodedata.normalize("NFKC", q).split()).casefold()


def _like(q: str) -> str:
    escaped = q.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
    return f"%{escaped}%"


def _engine_fields(product: scoring.Product, member: scoring.Member | None) -> dict[str, object]:
    """Grade, protein and (with a member) the member's status, all from the rules engine."""
    result = scoring.analyze(product, [member] if member is not None else [])
    return {
        "grade": result.report.nutriscore.grade,
        "protein_g": result.report.protein.per_100g,
        "protein_per_100kcal": result.report.protein.per_100kcal,
        "member_status": result.verdicts[0].status.value if member is not None else None,
    }


def sort_by_protein(hits: list[SearchHit]) -> list[SearchHit]:
    """Drop ``avoid`` hits; most protein per 100 kcal first, unknown last (stable). Pure."""
    kept = [h for h in hits if h.member_status != "avoid"]
    return sorted(
        kept,
        key=lambda h: (
            h.protein_per_100kcal is None,
            -(h.protein_per_100kcal or 0.0),
        ),
    )


async def search_products(
    session: AsyncSession,
    off: OffClient,
    q: str,
    limit: int = 20,
    *,
    account_id: UUID,
    settings: Settings,
    member: scoring.Member | None = None,
    sort: SearchSort = SearchSort.RELEVANCE,
) -> list[SearchHit]:
    """Up to ``limit`` hits: ours first (by name), then OFF. Does not commit.

    ``sort="protein"`` needs ``member`` (the caller passes member_id's or the primary).
    """
    if sort == SearchSort.PROTEIN and member is None:
        raise ValueError("sort=protein needs a member (member_id or the primary member)")
    hits = await _search(
        session,
        off,
        q,
        limit,
        account_id=account_id,
        settings=settings,
        member=member,
        skip_supplements=sort == SearchSort.PROTEIN,
    )
    return sort_by_protein(hits) if sort == SearchSort.PROTEIN else hits


async def _search(
    session: AsyncSession,
    off: OffClient,
    q: str,
    limit: int,
    *,
    account_id: UUID,
    settings: Settings,
    member: scoring.Member | None,
    skip_supplements: bool = False,
) -> list[SearchHit]:
    query = normalise_query(q)
    pattern = _like(query)
    rows = await session.scalars(
        select(Product)
        .where(
            service.visible_to(account_id),
            or_(
                Product.name.ilike(pattern, escape="\\"), Product.brand.ilike(pattern, escape="\\")
            ),
        )
        .order_by(Product.name, Product.id)
        .limit(limit)
    )
    hits: list[SearchHit] = []
    seen: set[str] = set()
    for row in rows:
        if row.barcode:
            seen.add(row.barcode)  # ours wins even when skipped: no OFF duplicate
        product = service.record_to_product(row)
        if skip_supplements and product.category == scoring.Category.SUPPLEMENT:
            continue
        hits.append(
            SearchHit(
                product_id=row.id,
                barcode=row.barcode,
                name=row.name,
                brand=row.brand,
                source="ours",
                attribution=None,
                **_engine_fields(product, member),
            )
        )
    if len(hits) >= limit:
        return hits

    try:
        payloads = await service.cached_off_search(
            session, f"text:{query}", lambda: off.search_text(query, page_size=OFF_PAGE_SIZE)
        )
    except OffThrottled as exc:
        # I4: over the process-wide OFF search budget with nothing cached. Our own hits
        # are still useful: return them flagged. With none, it is not an empty result:
        # 503, so the client says "busy, try again" (Retry-After).
        if hits:
            return [h.model_copy(update={"off_degraded": True}) for h in hits]
        raise ApiError(
            "off_unavailable", 503, headers={"Retry-After": str(exc.retry_after)}
        ) from None
    except OffUnavailable:
        return hits
    for payload in payloads:
        if len(hits) >= limit:
            break
        info = off_to_info(payload)
        try:
            barcode = normalize_barcode(info.barcode) if info.barcode else None
        except InvalidBarcode:
            barcode = None
        if barcode is None or not info.name or barcode in seen:
            continue
        seen.add(barcode)
        product = off_to_product(payload, confidence=settings.off_data_confidence)
        if skip_supplements and product.category == scoring.Category.SUPPLEMENT:
            continue
        hits.append(
            SearchHit(
                product_id=None,
                barcode=barcode,
                name=info.name,
                brand=info.brand,
                source="off",
                attribution=service.OFF_ATTRIBUTION,
                **_engine_fields(product, member),
            )
        )
    return hits
