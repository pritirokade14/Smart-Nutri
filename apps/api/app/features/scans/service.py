"""Scan rows and the label-photo extraction flow (Plan 4 Task 4).

Label extraction never invents a value and never decides a verdict: it returns an
unconfirmed `ProductDraft`, or an error with no draft.
"""

import hashlib
import logging
import re
from dataclasses import dataclass
from typing import Any
from uuid import UUID, uuid4

import anyio
import sentry_sdk
from pydantic import ValidationError
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings
from app.core.errors import ApiError
from app.core.ratelimit import consume
from app.features.scans.api_schemas import LabelScanIn, ScanDraftOut
from app.features.scans.images import InvalidImage, prepare_for_extraction, sniff_image_mime
from app.features.scans.models import Scan
from app.features.scans.normalize import ProductDraft, to_draft
from app.features.scans.schemas import NutritionExtraction
from app.integrations.openfoodfacts import InvalidBarcode, normalize_barcode
from app.integrations.providers import ExtractionFailed, LLMProvider, ProviderUnavailable
from app.integrations.storage import StorageClient, StorageNotFound, StorageUnavailable
from app.prompts import load_extraction_prompt

logger = logging.getLogger(__name__)

MAX_IMAGE_BYTES = 8 * 1024 * 1024
EXTRACTION_MIME = "image/jpeg"  # prepare_for_extraction always re-encodes to JPEG
_UUID4 = r"[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}"
_EXTS = ("jpg", "png", "webp")


async def add_scan(
    session: AsyncSession,
    *,
    scan_id: UUID,
    account_id: UUID,
    product_id: UUID | None,
    analysis: dict[str, Any],
) -> None:
    """Stage a scan row (the caller commits). ``analysis`` must hold no member names."""
    session.add(Scan(id=scan_id, account_id=account_id, product_id=product_id, analysis=analysis))
    await session.flush()


# --- Label scans: the stored draft (contract between POST /v1/scans/label and POST /v1/products)
#
# A label scan stores its normalised draft in ``scans.analysis`` as
#   {"draft": ProductDraft.model_dump(mode="json"), "prompt_version": "...", "model": "..."}
# Build it with ``label_scan_analysis``; read it back with ``get_label_scan``.


def label_scan_analysis(draft: ProductDraft, *, prompt_version: str, model: str) -> dict[str, Any]:
    """The ``scans.analysis`` value for a label scan (no member data: a label has none)."""
    return {
        "draft": draft.model_dump(mode="json"),
        "prompt_version": prompt_version,
        "model": model,
    }


@dataclass(frozen=True, slots=True)
class LabelScan:
    scan_id: UUID
    product_id: UUID | None  # the product already saved from this scan, if any
    draft: ProductDraft


async def get_label_scan(
    session: AsyncSession, account_id: UUID, scan_id: UUID
) -> LabelScan | None:
    """The caller's label scan with its draft, locked for update; None if it is unknown,
    another account's, or not a label scan (unknown and foreign look the same)."""
    scan = await session.scalar(
        select(Scan)
        .where(Scan.id == scan_id, Scan.account_id == account_id)
        .with_for_update()
        .execution_options(populate_existing=True)
    )
    analysis = scan.analysis if scan is not None else None
    if not isinstance(analysis, dict) or not isinstance(analysis.get("draft"), dict):
        return None
    try:
        draft = ProductDraft.model_validate(analysis["draft"])
    except ValidationError:
        logger.warning("label scan has an unreadable draft", extra={"scan_id": str(scan_id)})
        return None
    return LabelScan(scan_id=scan.id, product_id=scan.product_id, draft=draft)


async def link_product(
    session: AsyncSession, *, account_id: UUID, scan_id: UUID, product_id: UUID
) -> None:
    """Record the product saved from a label scan (the caller commits)."""
    await session.execute(
        update(Scan)
        .where(Scan.id == scan_id, Scan.account_id == account_id)
        .values(product_id=product_id)
    )


def new_upload_path(account_id: UUID, ext: str) -> str:
    """`<account_id>/<uuid4>.<ext>` in the private label-photo bucket."""
    if ext not in _EXTS:
        raise ValueError(f"unsupported extension: {ext}")
    return f"{account_id}/{uuid4()}.{ext}"


def owns_path(account_id: UUID, path: str) -> bool:
    """True only for exactly `<account_id>/<uuid4>.<jpg|png|webp>` (no nesting, no `..`)."""
    pattern = rf"{re.escape(str(account_id))}/{_UUID4}\.(?:{'|'.join(_EXTS)})"
    return re.fullmatch(pattern, path) is not None


async def _cached_draft(
    session: AsyncSession, image_sha256: str, prompt_version: str
) -> ProductDraft | None:
    """The newest stored draft for these exact image bytes and prompt version, any account.

    Only the draft is reused: never another account's scan id, path or product.
    """
    analysis = await session.scalar(
        select(Scan.analysis)
        .where(
            Scan.image_sha256 == image_sha256,
            Scan.analysis.has_key("draft"),
            Scan.analysis["prompt_version"].astext == prompt_version,
        )
        .order_by(Scan.created_at.desc())
        .limit(1)
    )
    if analysis is None:
        return None
    try:
        return ProductDraft.model_validate(analysis["draft"])
    except ValidationError:
        logger.warning("label_extraction cache_entry_invalid prompt_version=%s", prompt_version)
        return None


async def _extract(
    llm: LLMProvider, image: bytes, *, prompt: str, prompt_version: str, model: str
) -> ProductDraft:
    try:
        extraction = await llm.extract_label(
            image=image,
            mime=EXTRACTION_MIME,
            prompt=prompt,
            prompt_version=prompt_version,
            schema=NutritionExtraction,
            model=model,
        )
    except ProviderUnavailable as exc:
        logger.error("label_extraction unavailable reason=%s", exc.reason)
        if exc.reason == "insufficient_credits":
            # Ops alert. No image, label content or account data in the event.
            sentry_sdk.capture_message("callmissed insufficient_credits", level="error")
        raise ApiError("extraction_unavailable", 503) from None
    except ExtractionFailed:
        raise ApiError("extraction_failed", 502) from None
    if not isinstance(extraction, NutritionExtraction):
        raise ApiError("extraction_failed", 502)
    return to_draft(extraction)


async def create_label_scan(
    session: AsyncSession,
    *,
    storage: StorageClient,
    llm: LLMProvider,
    settings: Settings,
    account_id: UUID,
    body: LabelScanIn,
) -> ScanDraftOut:
    """Download the caller's photo, extract (or reuse a cached draft), store a scan row.

    Only a paid extraction counts toward the `label_scans` limit; a cache hit is free.
    """
    if not owns_path(account_id, body.path):
        raise ApiError("scan_image_not_found", 404)
    barcode: str | None = None
    if body.barcode is not None:
        try:
            barcode = normalize_barcode(body.barcode)
        except InvalidBarcode:
            raise ApiError("invalid_barcode", 422) from None

    try:
        data = await storage.download(body.path)
    except StorageNotFound:
        raise ApiError("scan_image_not_found", 404) from None
    except StorageUnavailable:
        raise ApiError("storage_unavailable", 503) from None
    if len(data) > MAX_IMAGE_BYTES:
        raise ApiError("image_too_large", 413)
    if sniff_image_mime(data) is None:
        raise ApiError("unsupported_image", 415)

    image_sha256 = hashlib.sha256(data).hexdigest()
    prompt, prompt_version = load_extraction_prompt()
    draft = await _cached_draft(session, image_sha256, prompt_version)
    cached = draft is not None
    if draft is None:
        # Count before decode (R15): undecodable uploads cost a scan too. Nothing is staged
        # yet, so the limiter's commit only persists the counter.
        await consume(session, settings, account_id=account_id, bucket="label_scans")
        try:
            prepared = await anyio.to_thread.run_sync(prepare_for_extraction, data)
        except InvalidImage:
            raise ApiError("unsupported_image", 415) from None
        model = settings.callmissed_extraction_model
        logger.info(
            "label_extraction cached=false prompt_version=%s model=%s", prompt_version, model
        )
        draft = await _extract(
            llm, prepared, prompt=prompt, prompt_version=prompt_version, model=model
        )
    else:
        logger.info("label_extraction cached=true prompt_version=%s", prompt_version)

    scan_id = uuid4()
    session.add(
        Scan(
            id=scan_id,
            account_id=account_id,
            product_id=None,
            image_path=body.path,
            image_sha256=image_sha256,
            analysis={
                **label_scan_analysis(
                    draft,
                    prompt_version=prompt_version,
                    model=settings.callmissed_extraction_model,
                ),
                "cached": cached,
                "barcode": barcode,
            },
        )
    )
    await session.flush()
    await session.commit()
    return ScanDraftOut(scan_id=scan_id, draft=draft, cached=cached, prompt_version=prompt_version)
