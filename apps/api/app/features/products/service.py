"""Barcode lookup: own catalogue -> OFF cache -> Open Food Facts.

OFF payloads live only in ``off_product_cache`` (ODbL), never in ``products``.
"""

import math
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


# --- POST /v1/products: a confirmed label draft or a manual entry --------------------------

MANUAL_ENTRY_CONFIDENCE = 1.0  # a person typed every value


_UPPER_BOUND_WITHHELD = ("protein_g", "fiber_g")  # an upper bound is no evidence of protein
BARCODE_CONSTRAINT = "uq_products_barcode"


def _validation_error(field: str) -> ApiError:
    return ApiError("validation_error", 422, details={"fields": [f"body.{field}"]})


def _sodium_unit_unconfirmed(draft: ProductDraft, body: ProductCreate) -> bool:
    """The chosen column's sodium was printed without a unit (the user must pick one)."""
    return f"unit_unconfirmed:{body.basis}.sodium_mg" in draft.warnings


def _withheld(draft: ProductDraft, body: ProductCreate) -> set[str]:
    """Engine fields held back from storage until the user confirms them (R13/R14/R17).

    The draft's own list, except that on a basis mismatch the explicit `basis` answers the
    basis doubt; per-field doubts on the chosen column (an upper-bound protein/fibre, a
    unit-less sodium) still apply.
    """
    withheld = set() if "basis_mismatch" in draft.warnings else set(draft.engine_withheld)
    withheld |= {
        f for f in _UPPER_BOUND_WITHHELD if f"upper_bound:{body.basis}.{f}" in draft.warnings
    }
    if _sodium_unit_unconfirmed(draft, body):
        withheld.add("sodium_mg")
    return withheld


def _needs_serving_confirmation(draft: ProductDraft, body: ProductCreate) -> bool:
    """Per-100 g values that depend on the serving size (sent per serving, or derived from it
    by the normaliser) are trusted only when the user confirmed the serving size."""
    if body.basis == "per_serving":
        return True
    return draft.derived_from_serving and "basis_mismatch" not in draft.warnings


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


def _per_100g(body: ProductCreate, label: scans_service.LabelScan | None) -> dict[str, Any]:
    """The per-100 g values to store: the server's conversion of what the pack prints.

    Sodium unit, then basis (the normaliser's own helpers), then what the user did not
    confirm is set to None. Raises 422 for a missing or implausible serving size on a
    per-serving basis, or a sodium unit the user had to pick and did not.
    """
    values: dict[str, float | None] = body.nutrients.model_dump()
    if (
        label is not None
        and values["sodium_mg"] is not None
        and _sodium_unit_unconfirmed(label.draft, body)
        and body.sodium_unit is None
    ):
        raise _validation_error("sodium_unit")
    values["sodium_mg"] = sodium_to_mg(values["sodium_mg"], body.sodium_unit)

    if body.basis == "per_serving":
        serving = body.serving_size_g
        if serving is None:
            raise _validation_error("serving_size_g")
        if implausible_fields({}, serving_size_g=serving):
            raise ApiError(
                "implausible_value",
                422,
                details={"field": "serving_size_g", "fields": ["serving_size_g"]},
            )
        values = {k: per_100g_from_serving(v, serving) for k, v in values.items()}

    if label is not None:
        confirmed = set(body.confirmed_fields)
        if body.sodium_unit is not None:
            confirmed.add("sodium_mg")  # picking the unit is confirming sodium (R17)
        if _needs_serving_confirmation(label.draft, body) and "serving_size_g" not in confirmed:
            return dict.fromkeys(values)
        for field in _withheld(label.draft, body) - confirmed:
            values[field] = None
    return values


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

    per_100g = _per_100g(body, label)
    # R18: a scanned serving size is stored only when the user confirmed it (the engine's
    # per-serving reasons would otherwise rest on a possibly misread value). A manual entry
    # was typed by a person, so it is stored as given.
    serving_size_g = body.serving_size_g
    if label is not None and "serving_size_g" not in body.confirmed_fields:
        serving_size_g = None
    _check_plausible(per_100g, serving_size_g)  # only what will be stored (R16)
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
