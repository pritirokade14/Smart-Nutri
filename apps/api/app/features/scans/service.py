import logging
from dataclasses import dataclass
from typing import Any
from uuid import UUID

from pydantic import ValidationError
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.features.scans.models import Scan
from app.features.scans.normalize import ProductDraft

logger = logging.getLogger(__name__)


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
