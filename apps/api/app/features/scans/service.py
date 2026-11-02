from typing import Any
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.features.scans.models import Scan


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
