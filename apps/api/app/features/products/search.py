"""Product search: our own catalogue first, then Open Food Facts text search (F9).

Our products the caller may see (verified, plus their own pending ones; never another
account's pending or any rejected product) match on name or brand. OFF hits are de-duplicated
by barcode (ours win) and the OFF result is cached 24 h per normalised query. Grades come from
the rules engine. OFF being down is not an error: our hits are returned alone.
"""

from uuid import UUID

from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app import scoring
from app.core.config import Settings
from app.features.products import service
from app.features.products.models import Product
from app.features.products.off_mapping import off_to_info, off_to_product
from app.features.products.schemas import SearchHit
from app.integrations.openfoodfacts import (
    InvalidBarcode,
    OffClient,
    OffUnavailable,
    normalize_barcode,
)

MIN_QUERY, MAX_QUERY = 2, 80
OFF_PAGE_SIZE = 24


def normalise_query(q: str) -> str:
    """Collapse whitespace and casefold (also the cache key)."""
    return " ".join(q.split()).casefold()


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
