"""Barcode lookup: own catalogue -> OFF cache -> Open Food Facts.

OFF payloads live only in ``off_product_cache`` (ODbL), never in ``products``.
"""

import math
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from typing import Any, Literal
from uuid import UUID

from sqlalchemy import delete, select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from app import scoring
from app.core.config import get_settings
from app.features.products.models import OffProductCache, Product
from app.features.products.off_mapping import (
    ProductInfo,
    off_to_info,
    off_to_product,
    split_ingredients,
)
from app.integrations.openfoodfacts import OffClient, OffUnavailable, normalize_barcode

OFF_ATTRIBUTION = "attribution.off"
# Own products with no recorded extraction confidence that are not verified stay below
# the 0.7 floor, so an allergic member never gets `ok` from them.
UNVERIFIED_DEFAULT_CONFIDENCE = 0.5


@dataclass(frozen=True, slots=True)
class ProductLookup:
    source: Literal["smartnutri", "openfoodfacts"]
    product_id: UUID | None  # None for OFF products
    info: ProductInfo
    product: scoring.Product
    attribution: str | None  # "attribution.off" for OFF, else None


def _num(value: Any) -> float | None:
    if value is None or isinstance(value, bool):
        return None
    try:
        v = float(value)
    except (TypeError, ValueError):
        return None
    return v if math.isfinite(v) else None


def _nutrients(per_100g: dict[str, Any] | None) -> scoring.Nutrients:
    raw = per_100g if isinstance(per_100g, dict) else {}
    names = scoring.Nutrients.__dataclass_fields__
    return scoring.Nutrients(**{k: _num(raw.get(k)) for k in names})


def _category(value: str | None) -> scoring.Category:
    try:
        return scoring.Category(value)
    except ValueError:
        return scoring.Category.GENERAL


def record_to_product(record: Product) -> scoring.Product:
    confidence = record.extraction_confidence
    if confidence is None:
        confidence = (
            1.0 if record.verification_status == "verified" else UNVERIFIED_DEFAULT_CONFIDENCE
        )
    veg = record.veg_mark if record.veg_mark in ("veg", "non_veg") else None
    return scoring.Product(
        name=record.name,
        category=_category(record.category),
        per_100g=_nutrients(record.per_100g),
        serving_size_g=record.serving_size_g,
        ingredients=split_ingredients(record.ingredients_text),
        allergen_statement=record.allergen_statement,
        may_contain_statement=record.may_contain_statement,
        claims=tuple(record.claims or ()),
        veg_mark=veg,
        extraction_confidence=confidence,
    )


def record_to_info(record: Product) -> ProductInfo:
    return ProductInfo(
        barcode=record.barcode or "",
        name=record.name,
        brand=record.brand,
        image_url=None,
    )


def _from_off(payload: dict, barcode: str) -> ProductLookup:
    info = off_to_info(payload)
    if not info.barcode:
        info = ProductInfo(barcode, info.name, info.brand, info.image_url)
    return ProductLookup(
        source="openfoodfacts",
        product_id=None,
        info=info,
        product=off_to_product(payload, confidence=get_settings().off_data_confidence),
        attribution=OFF_ATTRIBUTION,
    )


async def _write_cache(session: AsyncSession, barcode: str, payload: dict) -> None:
    stmt = insert(OffProductCache).values(
        barcode=barcode, payload=payload, fetched_at=datetime.now(UTC)
    )
    stmt = stmt.on_conflict_do_update(
        index_elements=[OffProductCache.barcode],
        set_={"payload": stmt.excluded.payload, "fetched_at": stmt.excluded.fetched_at},
    )
    await session.execute(stmt)


async def lookup_by_barcode(
    session: AsyncSession, off: OffClient, barcode: str
) -> ProductLookup | None:
    barcode = normalize_barcode(barcode)

    own = await session.scalar(
        select(Product).where(Product.barcode == barcode, Product.verification_status != "rejected")
    )
    if own is not None:
        return ProductLookup(
            source="smartnutri",
            product_id=own.id,
            info=record_to_info(own),
            product=record_to_product(own),
            attribution=None,
        )

    ttl = timedelta(hours=get_settings().off_cache_ttl_hours)
    cached = await session.scalar(
        select(OffProductCache)
        .where(OffProductCache.barcode == barcode)
        .execution_options(populate_existing=True)
    )
    if cached is not None and datetime.now(UTC) - cached.fetched_at < ttl:
        return _from_off(cached.payload, barcode)

    try:
        payload = await off.get_product(barcode)
    except OffUnavailable:
        if cached is not None:
            return _from_off(cached.payload, barcode)
        raise

    if payload is None:
        if cached is not None:
            await session.execute(delete(OffProductCache).where(OffProductCache.barcode == barcode))
            session.expire_all()
        return None

    await _write_cache(session, barcode, payload)
    return _from_off(payload, barcode)
