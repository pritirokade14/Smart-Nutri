"""Product search: our own catalogue first, then Open Food Facts text search (F9).

Our products the caller may see (verified, plus their own pending ones; never another
account's pending or any rejected product) match on name or brand. OFF hits are de-duplicated
by barcode (ours win) and the OFF result is cached 24 h per normalised query. Grades come from
the rules engine. OFF being down is not an error: our hits are returned alone. Over the
process-wide OFF search budget (I4, `off_search_per_minute`), a cached result (even a stale
one) is served; with none, our own hits are returned with `off_degraded=true`, and only
with no hits of ours either is it 503 `off_unavailable` with Retry-After.
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
from app.features.products.schemas import SearchHit
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


def _grade(product: scoring.Product) -> str | None:
    return scoring.analyze(product, []).report.nutriscore.grade


async def search_products(
    session: AsyncSession,
    off: OffClient,
    q: str,
    limit: int = 20,
    *,
    account_id: UUID,
    settings: Settings,
) -> list[SearchHit]:
    """Up to ``limit`` hits: ours first (by name), then OFF. Does not commit."""
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
        hits.append(
            SearchHit(
                product_id=row.id,
                barcode=row.barcode,
                name=row.name,
                brand=row.brand,
                grade=_grade(service.record_to_product(row)),
                source="ours",
                attribution=None,
            )
        )
        if row.barcode:
            seen.add(row.barcode)
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
        hits.append(
            SearchHit(
                product_id=None,
                barcode=barcode,
                name=info.name,
                brand=info.brand,
                grade=_grade(product),
                source="off",
                attribution=service.OFF_ATTRIBUTION,
            )
        )
    return hits
