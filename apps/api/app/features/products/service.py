"""Barcode lookup: own catalogue -> OFF cache -> Open Food Facts.

OFF payloads live only in ``off_product_cache`` (ODbL), never in ``products``.
"""

import math
from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from typing import Any, Literal
from uuid import UUID

from sqlalchemy import ColumnElement, and_, delete, or_, select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app import scoring
from app.core.config import Settings
from app.core.errors import ApiError
from app.features.products import confirm_rules as rules
from app.features.products.models import OffProductCache, Product
from app.features.products.off_mapping import (
    ProductInfo,
    off_to_info,
    off_to_product,
    split_ingredients,
)
from app.features.products.schemas import (
    NutrientsOut,
    ProductCreate,
    ProductOut,
    PublicProductOut,
)
from app.features.scans import service as scans_service
from app.features.scans.normalize import (
    ProductDraft,
    implausible_fields,
    per_100g_from_serving,
    sodium_to_mg,
)
from app.integrations.openfoodfacts import (
    InvalidBarcode,
    OffClient,
    OffUnavailable,
    normalize_barcode,
)

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


def _visible_to(account_id: UUID | None) -> ColumnElement[bool]:
    """Which own-catalogue products a caller may be served (Ruling R6 / CROSS-PLAN 18).

    Verified products: everyone. Pending (user-submitted, unreviewed) products: only the
    account that created them. Rejected products: nobody. ``account_id=None`` (the public
    route) therefore sees verified products only.
    """
    verified = Product.verification_status == "verified"
    if account_id is None:
        return verified
    own_pending = and_(Product.verification_status == "pending", Product.created_by == account_id)
    return or_(verified, own_pending)


def _is_visible(record: Product, account_id: UUID | None) -> bool:
    """Python twin of ``_visible_to`` for a loaded row."""
    if record.verification_status == "verified":
        return True
    return (
        account_id is not None
        and record.verification_status == "pending"
        and record.created_by == account_id
    )


async def lookup_by_id(
    session: AsyncSession, product_id: UUID, *, account_id: UUID | None = None
) -> ProductLookup | None:
    """Own catalogue product by id, if the caller may see it (see ``_visible_to``)."""
    record = await session.scalar(
        select(Product).where(Product.id == product_id, _visible_to(account_id))
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
    session: AsyncSession,
    off: OffClient,
    barcode: str,
    *,
    settings: Settings,
    account_id: UUID | None = None,
) -> ProductLookup | None:
    """Own catalogue (if visible to ``account_id``, see ``_visible_to``) -> OFF cache -> OFF.

    Pass the caller's account id on authenticated routes; leave it None on public routes.
    """
    barcode = normalize_barcode(barcode)

    own = await session.scalar(
        select(Product).where(Product.barcode == barcode, _visible_to(account_id))
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


SEARCH_CACHE_TTL = timedelta(hours=24)  # OFF rate-limits search; never re-ask within a day
SEARCH_CACHE_PREFIX = "search:"  # off_product_cache keys; barcodes are digits, so no clash


async def cached_off_search(
    session: AsyncSession,
    key: str,
    fetch: Callable[[], Awaitable[list[dict]]],
) -> list[dict]:
    """An OFF search result, cached in ``off_product_cache`` under ``search:<key>`` for 24 h.

    OFF data stays in ``off_product_cache`` (ODbL). A stale entry is served when OFF is down;
    with no entry, ``OffUnavailable`` propagates. The cache write is left for the caller to
    commit.
    """
    cache_key = f"{SEARCH_CACHE_PREFIX}{key}"
    cached = await session.scalar(
        select(OffProductCache)
        .where(OffProductCache.barcode == cache_key)
        .execution_options(populate_existing=True)
    )
    if cached is not None and datetime.now(UTC) - cached.fetched_at < SEARCH_CACHE_TTL:
        return list(cached.payload.get("products") or [])
    try:
        products = await fetch()
    except OffUnavailable:
        if cached is not None:
            return list(cached.payload.get("products") or [])
        raise
    await _write_cache(session, cache_key, {"products": products})
    return products


async def off_payload(session: AsyncSession, barcode: str | None) -> dict | None:
    """The cached OFF payload for a barcode (any age), or None. Never calls OFF."""
    if not barcode:
        return None
    cached = await session.scalar(select(OffProductCache).where(OffProductCache.barcode == barcode))
    return None if cached is None else cached.payload


async def resolve_ref(
    session: AsyncSession,
    off: OffClient,
    *,
    product_id: UUID | None,
    barcode: str | None,
    settings: Settings,
    account_id: UUID,
) -> ProductLookup:
    """Exactly one product reference (own ``product_id`` or a ``barcode``) -> ProductLookup.

    The same resolution ``POST /v1/analyze`` uses: another account's pending product is never
    served (CROSS-PLAN 18). Errors: ``invalid_product_ref`` (422), ``invalid_barcode`` (422),
    ``off_unavailable`` (503), ``product_not_found`` (404). A stale OFF cache delete is
    committed before the 404; an OFF cache write is left for the caller to commit.
    """
    if (product_id is None) == (barcode is None):
        raise ApiError("invalid_product_ref", 422)
    if product_id is not None:
        found = await lookup_by_id(session, product_id, account_id=account_id)
    else:
        try:
            found = await lookup_by_barcode(
                session, off, barcode or "", settings=settings, account_id=account_id
            )
        except InvalidBarcode as exc:
            raise ApiError("invalid_barcode", 422) from exc
        except OffUnavailable as exc:
            raise ApiError("off_unavailable", 503) from exc
        if found is None:
            await session.commit()  # persist a stale OFF cache delete
    if found is None:
        raise ApiError("product_not_found", 404)
    return found


# --- POST /v1/products: a confirmed label draft or a manual entry --------------------------

MANUAL_ENTRY_CONFIDENCE = 1.0  # a person typed every value


BARCODE_CONSTRAINT = "uq_products_barcode"


def _validation_error(field: str) -> ApiError:
    return ApiError("validation_error", 422, details={"fields": [f"body.{field}"]})


def _draft_confidence(draft: ProductDraft) -> float:
    """The extraction confidence from the stored draft (user edits never raise it)."""
    value = draft.confidence
    return min(max(value, 0.0), 1.0) if math.isfinite(value) else 0.0


def _check_plausible(values: dict[str, float | None], serving_size_g: float | None) -> None:
    """The engine's own plausibility rule (the one the normaliser flags in drafts), on the
    per-100 g values that will be stored."""
    dropped = implausible_fields(values, serving_size_g=serving_size_g)
    if dropped:
        raise ApiError(
            "implausible_value", 422, details={"field": dropped[0], "fields": list(dropped)}
        )


def _ingredients_text(items: list[str]) -> str | None:
    """Join items so the engine's splitter reads back exactly these items.

    An item with a top-level "," or ";" becomes the items the engine would read anyway.
    Unbalanced brackets that would merge items on read-back are rejected.
    """
    parts = [part for item in items for part in split_ingredients(item)]
    if not parts:
        return None
    text = ", ".join(parts)
    if list(split_ingredients(text)) != parts:
        raise ApiError("validation_error", 422, details={"fields": ["body.ingredients"]})
    return text


def stored_values(
    body: ProductCreate, draft: ProductDraft | None
) -> tuple[dict[str, float | None], float | None]:
    """(per-100 g values, serving size) to store: the server's conversion of what the pack
    prints, gated by the confirm rules. Pure; ``draft`` is the scan's draft (None = manual).

    Sodium unit, then basis (the normaliser's own helpers), then what the user did not
    confirm is set to None (``confirm_rules``, the helpers that also compute
    ``ProductDraft.confirm``). Raises 422 for a missing serving size on a per-serving basis,
    an implausible serving size that will be used for conversion (R19), a sodium unit the
    user had to pick and did not (R19), or an implausible stored value (R16).
    """
    values: dict[str, float | None] = body.nutrients.model_dump()
    if (
        draft is not None
        and values["sodium_mg"] is not None
        and rules.sodium_unit_unconfirmed(draft)
        and body.sodium_unit is None
    ):
        raise _validation_error("sodium_unit")
    values["sodium_mg"] = sodium_to_mg(values["sodium_mg"], body.sodium_unit)

    serving = body.serving_size_g
    if body.basis == "per_serving" and serving is None:
        raise _validation_error("serving_size_g")

    confirmed = set(body.confirmed_fields)
    if body.sodium_unit is not None:
        confirmed.add("sodium_mg")  # picking the unit is confirming sodium (R17)
    # R18: a scanned serving size is stored only when the user confirmed it (the engine's
    # per-serving reasons would otherwise rest on a possibly misread value). A manual entry
    # was typed by a person, so it is stored as given.
    stored_serving = serving if draft is None or "serving_size_g" in confirmed else None
    if (
        draft is not None
        and rules.needs_serving_confirmation(draft, body.basis)
        and "serving_size_g" not in confirmed
    ):
        # Nothing is stored, so the (unconfirmed) serving is neither used nor checked (R19).
        return dict.fromkeys(values), None

    if body.basis == "per_serving" and serving is not None:  # None was rejected above
        if implausible_fields({}, serving_size_g=serving):
            raise ApiError(
                "implausible_value",
                422,
                details={"field": "serving_size_g", "fields": ["serving_size_g"]},
            )
        values = {k: per_100g_from_serving(v, serving) for k, v in values.items()}

    if draft is not None:
        for field in rules.withheld_fields(draft) - confirmed:
            values[field] = None
    _check_plausible(values, stored_serving)  # only what will be stored (R16)
    return values, stored_serving


def _violated_constraint(exc: IntegrityError) -> str | None:
    diag = getattr(exc.orig, "diag", None)
    return getattr(diag, "constraint_name", None)


async def _barcode_for_new_product(
    session: AsyncSession, account_id: UUID, barcode: str | None
) -> str | None:
    """The barcode to store, or 409 if the caller can already see a product with it.

    A barcode held by a product the caller cannot see (another account's pending product,
    or a rejected one) is not stored: the caller's own confirmed product is saved without
    it, and the other product is not revealed.
    """
    if barcode is None:
        return None
    holder = await session.scalar(select(Product).where(Product.barcode == barcode))
    if holder is None:
        return barcode
    if _is_visible(holder, account_id):
        raise ApiError("product_exists", 409, details={"product_id": str(holder.id)})
    return None


async def _insert(session: AsyncSession, account_id: UUID, record: Product) -> None:
    """Insert ``record``; a concurrent save that took its barcode is handled like the
    pre-check (visible holder -> 409 with its id, invisible holder -> saved without the
    barcode). Any other integrity error is a bug and propagates (500)."""
    for _ in range(2):
        try:
            async with session.begin_nested():
                session.add(record)
                await session.flush()
            return
        except IntegrityError as exc:
            if record.barcode is None or _violated_constraint(exc) != BARCODE_CONSTRAINT:
                raise
            record.barcode = await _barcode_for_new_product(session, account_id, record.barcode)
    raise ApiError("product_exists", 409)  # the barcode changed hands twice in one request


async def create_product(
    session: AsyncSession, account_id: UUID, body: ProductCreate
) -> ProductOut:
    """Save a confirmed draft (``scan_id``) or a manual entry as a pending product; commits."""
    barcode = None
    if body.barcode is not None:
        try:
            barcode = normalize_barcode(body.barcode)
        except InvalidBarcode as exc:
            raise ApiError("invalid_barcode", 422) from exc

    label = None
    if body.scan_id is not None:
        label = await scans_service.get_label_scan(session, account_id, body.scan_id)
        if label is None:  # unknown, foreign and non-label scans look the same
            raise ApiError("scan_not_found", 404)
        if label.product_id is not None:
            saved = await lookup_by_id(session, label.product_id, account_id=account_id)
            if saved is not None:  # already saved from this scan (e.g. a client retry)
                raise ApiError("product_exists", 409, details={"product_id": str(saved.product_id)})

    per_100g, serving_size_g = stored_values(body, label.draft if label is not None else None)
    ingredients_text = _ingredients_text(body.ingredients)
    barcode = await _barcode_for_new_product(session, account_id, barcode)

    record = Product(
        barcode=barcode,
        name=body.name,
        brand=body.brand,
        category=body.category,
        per_100g=per_100g,
        serving_size_g=serving_size_g,
        ingredients_text=ingredients_text,
        allergen_statement=body.allergen_statement,
        may_contain_statement=body.may_contain_statement,
        claims=list(body.claims),
        veg_mark=body.veg_mark,
        source="label" if label is not None else "user",
        extraction_confidence=(
            _draft_confidence(label.draft) if label is not None else MANUAL_ENTRY_CONFIDENCE
        ),
        verification_status="pending",
        created_by=account_id,
    )
    await _insert(session, account_id, record)

    if label is not None:
        await scans_service.link_product(
            session, account_id=account_id, scan_id=label.scan_id, product_id=record.id
        )
    out = to_product_out(lookup_from_record(record))
    await session.commit()
    return out
