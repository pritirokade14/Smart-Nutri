"""Scan rows and the label-photo extraction flow (Plan 4 Task 4).

Label extraction never invents a value and never decides a verdict: it returns an
unconfirmed `ProductDraft`, or an error with no draft.
"""

import hashlib
import logging
import re
from dataclasses import dataclass
from datetime import datetime
from typing import Any
from uuid import UUID, uuid4

import anyio
import sentry_sdk
from pydantic import ValidationError
from sqlalchemy import func, select, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings
from app.core.errors import ApiError
from app.core.ratelimit import consume, refund
from app.features.scans.api_schemas import LabelScanIn, ScanDraftOut
from app.features.scans.images import InvalidImage, prepare_for_extraction, sniff_image_mime
from app.features.scans.models import SCAN_PATH_INDEX, Scan
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
# A label scan stores its normalised draft and the raw model output in ``scans.analysis`` as
#   {"draft": ProductDraft.model_dump(mode="json"),
#    "extraction": NutritionExtraction.model_dump(mode="json"),
#    "prompt_version": "...", "model": "<the model that produced the extraction>"}
# Build it with ``label_scan_analysis``; read it back with ``get_label_scan``. The raw
# extraction is the cache entry (R16): every reuse re-runs ``to_draft`` on it, so normaliser
# safety fixes apply to old extractions too.


def label_scan_analysis(
    draft: ProductDraft,
    *,
    extraction: NutritionExtraction,
    prompt_version: str,
    model: str,
) -> dict[str, Any]:
    """The ``scans.analysis`` value for a label scan (no member data: a label has none)."""
    return {
        "draft": draft.model_dump(mode="json"),
        "extraction": extraction.model_dump(mode="json"),
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
    another account's, or not a label scan (unknown and foreign look the same).

    The draft is re-normalised from the stored raw extraction (``to_draft``) when there is
    one (R19), so a save always applies the current normaliser's safety rules; scans stored
    without a raw extraction (before R16) fall back to their stored draft.
    """
    scan = await session.scalar(
        select(Scan)
        .where(Scan.id == scan_id, Scan.account_id == account_id)
        .with_for_update()
        .execution_options(populate_existing=True)
    )
    analysis = scan.analysis if scan is not None else None
    if not isinstance(analysis, dict) or not isinstance(analysis.get("draft"), dict):
        return None
    if "extraction" in analysis:
        extraction = _extraction_of(analysis, str(analysis.get("prompt_version")))
        if extraction is not None:
            return LabelScan(
                scan_id=scan.id, product_id=scan.product_id, draft=to_draft(extraction)
            )
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


def _violated_constraint(exc: IntegrityError) -> str | None:
    diag = getattr(exc.orig, "diag", None)
    return getattr(diag, "constraint_name", None)


def new_upload_path(account_id: UUID, ext: str) -> str:
    """`<account_id>/<uuid4>.<ext>` in the private label-photo bucket."""
    if ext not in _EXTS:
        raise ValueError(f"unsupported extension: {ext}")
    return f"{account_id}/{uuid4()}.{ext}"


def owns_path(account_id: UUID, path: str) -> bool:
    """True only for exactly `<account_id>/<uuid4>.<jpg|png|webp>` (no nesting, no `..`)."""
    pattern = rf"{re.escape(str(account_id))}/{_UUID4}\.(?:{'|'.join(_EXTS)})"
    return re.fullmatch(pattern, path) is not None


def _cache_key(image_sha256: str, prompt_version: str, model: str) -> list[Any]:
    """Rows whose raw extraction came from these exact bytes, prompt version and model.

    Rows without a raw extraction (stored before R16) never match: they are a cache miss.
    """
    return [
        Scan.image_sha256 == image_sha256,
        Scan.analysis.has_key("extraction"),
        Scan.analysis["prompt_version"].astext == prompt_version,
        Scan.analysis["model"].astext == model,
    ]


def _extraction_of(analysis: Any, prompt_version: str) -> NutritionExtraction | None:
    try:
        return NutritionExtraction.model_validate(analysis["extraction"])
    except (ValidationError, KeyError, TypeError):
        logger.warning("label_extraction cache_entry_invalid prompt_version=%s", prompt_version)
        return None


async def _cached_extraction(
    session: AsyncSession, image_sha256: str, prompt_version: str, model: str
) -> NutritionExtraction | None:
    """The newest raw extraction of these exact image bytes (any account), for this prompt
    version and model. Only the extraction is reused: never another account's scan id, path
    or product."""
    analysis = await session.scalar(
        select(Scan.analysis)
        .where(*_cache_key(image_sha256, prompt_version, model))
        .order_by(Scan.created_at.desc())
        .limit(1)
    )
    return None if analysis is None else _extraction_of(analysis, prompt_version)


async def _scan_at_path(session: AsyncSession, account_id: UUID, path: str) -> Scan | None:
    """The caller's scan of this upload path, if any (at most one: R21d unique index)."""
    return await session.scalar(
        select(Scan)
        .where(Scan.account_id == account_id, Scan.image_path == path)
        .with_for_update()
        .execution_options(populate_existing=True)
    )


async def _existing_scan_out(session: AsyncSession, scan: Scan) -> ScanDraftOut:
    """Answer with an existing scan of this path (a client retry, or the winner of a race):
    its raw extraction re-normalised (current rules), no new row and no paid call. Commits."""
    analysis = scan.analysis if isinstance(scan.analysis, dict) else {}
    prompt_version = str(analysis.get("prompt_version") or load_extraction_prompt()[1])
    extraction = _extraction_of(analysis, prompt_version) if "extraction" in analysis else None
    if extraction is not None:
        draft = to_draft(extraction)
        if scan.product_id is None:  # keep the stored draft (what a save reads) current
            scan.analysis = {**analysis, "draft": draft.model_dump(mode="json")}
    else:
        try:
            draft = ProductDraft.model_validate(analysis.get("draft"))
        except ValidationError:
            logger.warning("label scan has an unreadable draft", extra={"scan_id": str(scan.id)})
            raise ApiError("extraction_failed", 502) from None
    await session.commit()
    logger.info("label_extraction cached=true repeat=true prompt_version=%s", prompt_version)
    return ScanDraftOut(scan_id=scan.id, draft=draft, cached=True, prompt_version=prompt_version)


async def _extract(
    llm: LLMProvider, image: bytes, *, prompt: str, prompt_version: str, model: str
) -> NutritionExtraction:
    """One paid extraction. ProviderUnavailable (no paid call happened) propagates."""
    try:
        extraction = await llm.extract_label(
            image=image,
            mime=EXTRACTION_MIME,
            prompt=prompt,
            prompt_version=prompt_version,
            schema=NutritionExtraction,
            model=model,
        )
    except ExtractionFailed:
        raise ApiError("extraction_failed", 502) from None
    if not isinstance(extraction, NutritionExtraction):
        raise ApiError("extraction_failed", 502)
    return extraction


async def create_label_scan(
    session: AsyncSession,
    *,
    storage: StorageClient,
    llm: LLMProvider,
    settings: Settings,
    account_id: UUID,
    body: LabelScanIn,
) -> ScanDraftOut:
    """Download the caller's photo, extract (or reuse a cached extraction), store a scan row.

    Only a paid extraction counts toward the `label_scans` limit; a cache hit is free, and a
    provider refusal (no paid call happened) is refunded. The same account posting the same
    path again gets its existing scan back (no download, no paid call, no new row): R21d
    makes (account_id, image_path) unique, and a concurrent first post that loses the race
    to insert gets the winner's scan.
    """
    if not owns_path(account_id, body.path):
        raise ApiError("scan_image_not_found", 404)
    barcode: str | None = None
    if body.barcode is not None:
        try:
            barcode = normalize_barcode(body.barcode)
        except InvalidBarcode:
            raise ApiError("invalid_barcode", 422) from None

    # One scan per upload path (R21d): a repeat post gets its scan back without a download.
    existing = await _scan_at_path(session, account_id, body.path)
    if existing is not None:
        return await _existing_scan_out(session, existing)

    # Release the DB connection (ensure_account's read) before the slow storage download.
    await session.commit()
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
    model = settings.callmissed_extraction_model

    extraction = await _cached_extraction(session, image_sha256, prompt_version, model)
    cached = extraction is not None
    if extraction is None:
        # Count before decode (R15): undecodable uploads cost a scan too. Nothing is staged
        # yet, so the limiter's commit only persists the counter.
        await consume(session, settings, account_id=account_id, bucket="label_scans")
        try:
            prepared = await anyio.to_thread.run_sync(prepare_for_extraction, data)
        except InvalidImage:
            raise ApiError("unsupported_image", 415) from None
        logger.info(
            "label_extraction cached=false prompt_version=%s model=%s", prompt_version, model
        )
        try:
            extraction = await _extract(
                llm, prepared, prompt=prompt, prompt_version=prompt_version, model=model
            )
        except ProviderUnavailable as exc:
            # Refused before any paid call: give the scan back (R16). Nothing is staged.
            await refund(session, settings, account_id=account_id, bucket="label_scans")
            logger.error("label_extraction unavailable reason=%s", exc.reason)
            if exc.reason == "insufficient_credits":
                # Ops alert. No image, label content or account data in the event.
                sentry_sdk.capture_message("callmissed insufficient_credits", level="error")
            raise ApiError("extraction_unavailable", 503) from None
    else:
        logger.info("label_extraction cached=true prompt_version=%s", prompt_version)

    draft = to_draft(extraction)  # always the current normaliser, cached or not
    scan_id = uuid4()
    scan = Scan(
        id=scan_id,
        account_id=account_id,
        product_id=None,
        image_path=body.path,
        image_sha256=image_sha256,
        analysis={
            # The cache key includes the model, so on a hit this is still the model
            # that produced the extraction.
            **label_scan_analysis(
                draft, extraction=extraction, prompt_version=prompt_version, model=model
            ),
            "cached": cached,
            "barcode": barcode,
        },
    )
    try:
        async with session.begin_nested():
            session.add(scan)
            await session.flush()
    except IntegrityError as exc:
        # A concurrent post of the same path stored its scan first (R21d): answer with that
        # one. This request's extraction was paid for and still counts toward the limit.
        if _violated_constraint(exc) != SCAN_PATH_INDEX:
            raise
        winner = await _scan_at_path(session, account_id, body.path)
        if winner is None:
            raise
        return await _existing_scan_out(session, winner)
    await session.commit()
    return ScanDraftOut(scan_id=scan_id, draft=draft, cached=cached, prompt_version=prompt_version)


async def count_analyses(
    session: AsyncSession, account_id: UUID, start: datetime, end: datetime
) -> int:
    """Products checked (``POST /v1/analyze`` scans, whose analysis holds ``verdicts``) with
    start <= created_at < end. Label-photo scans are not checks and are not counted."""
    count = await session.scalar(
        select(func.count())
        .select_from(Scan)
        .where(
            Scan.account_id == account_id,
            Scan.analysis.has_key("verdicts"),
            Scan.created_at >= start,
            Scan.created_at < end,
        )
    )
    return int(count or 0)
