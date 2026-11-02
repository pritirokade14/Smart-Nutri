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
from app.core.config import Settings
from app.features.products.models import OffProductCache, Product
from app.features.products.off_mapping import (
    ProductInfo,
    off_to_info,
    off_to_product,
    split_ingredients,
)
from app.features.products.schemas import NutrientsOut, ProductOut, PublicProductOut
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


def lookup_from_record(record: Product) -> ProductLookup:
    """A ProductLookup for one of our own products (no DB access)."""
    return ProductLookup(
        source="smartnutri",
        product_id=record.id,
        info=record_to_info(record),
        product=record_to_product(record),
        attribution=None,
    )


async def lookup_by_id(session: AsyncSession, product_id: UUID) -> ProductLookup | None:
    """Own catalogue product by id; rejected products count as missing (as in barcode lookup)."""
    record = await session.scalar(
        select(Product).where(Product.id == product_id, Product.verification_status != "rejected")
    )
    return None if record is None else lookup_from_record(record)


def to_product_out(found: ProductLookup) -> ProductOut:
    p = found.product
    n = p.per_100g
    return ProductOut(
        source=found.source,
        product_id=found.product_id,
        barcode=found.info.barcode or None,
        name=found.info.name,
        brand=found.info.brand,
        image_url=found.info.image_url,
        category=p.category.value,
        per_100g=NutrientsOut(
            energy_kcal=n.energy_kcal,
            protein_g=n.protein_g,
            carbs_g=n.carbs_g,
            sugars_g=n.sugars_g,
            fat_g=n.fat_g,
            sat_fat_g=n.sat_fat_g,
            fiber_g=n.fiber_g,
            salt_g=n.salt_g,
            sodium_mg=n.sodium_mg,
        ),
        serving_size_g=p.serving_size_g,
        ingredients=list(p.ingredients),
        claims=list(p.claims),
        attribution=found.attribution,
    )


def to_public_out(found: ProductLookup) -> PublicProductOut:
    """Generic product facts only: the report comes from analyze(product, []), no members."""
    report = scoring.analyze(found.product, []).to_dict()["report"]
    return PublicProductOut(
        product=to_product_out(found), report=report, score_label="calculated_by_smartnutri"
    )


def _from_off(payload: dict, barcode: str, settings: Settings) -> ProductLookup:
    info = off_to_info(payload)
    if not info.barcode:
        info = ProductInfo(barcode, info.name, info.brand, info.image_url)
    return ProductLookup(
        source="openfoodfacts",
        product_id=None,
        info=info,
        product=off_to_product(payload, confidence=settings.off_data_confidence),
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
    session: AsyncSession, off: OffClient, barcode: str, *, settings: Settings
) -> ProductLookup | None:
    barcode = normalize_barcode(barcode)

    own = await session.scalar(
        select(Product).where(Product.barcode == barcode, Product.verification_status != "rejected")
    )
    if own is not None:
        return lookup_from_record(own)

    ttl = timedelta(hours=settings.off_cache_ttl_hours)
    cached = await session.scalar(
        select(OffProductCache)
        .where(OffProductCache.barcode == barcode)
        .execution_options(populate_existing=True)
    )
    if cached is not None and datetime.now(UTC) - cached.fetched_at < ttl:
        return _from_off(cached.payload, barcode, settings)

    try:
        payload = await off.get_product(barcode)
    except OffUnavailable:
        if cached is not None:
            return _from_off(cached.payload, barcode, settings)
        raise

    if payload is None:
        if cached is not None:
            await session.execute(delete(OffProductCache).where(OffProductCache.barcode == barcode))
            session.expire_all()
        return None

    await _write_cache(session, barcode, payload)
    return _from_off(payload, barcode, settings)
