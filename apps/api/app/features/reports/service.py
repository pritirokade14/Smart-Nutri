"""Product problem reports (F14). Stored for review; they never change a product or a verdict.

The note is user free text: it is stored, never logged.
"""

from uuid import UUID

from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import ApiError
from app.features.products import service as products_service
from app.features.reports.models import ProductReport
from app.features.reports.schemas import ReportCreate


async def create_report(
    session: AsyncSession, account_id: UUID, product_id: UUID, body: ReportCreate
) -> tuple[ProductReport, bool]:
    """(report, created). An open report with the same account, product and reason is
    returned as is (idempotent); a resolved one doesn't count. Commits."""
    if await products_service.lookup_by_id(session, product_id, account_id=account_id) is None:
        raise ApiError("product_not_found", 404)
    # Serialise concurrent identical reports so only one row is created.
    await session.execute(
        text("SELECT pg_advisory_xact_lock(hashtextextended(:key, 0))"),
        {"key": f"product_report:{account_id}:{product_id}:{body.reason}"},
    )
    existing = await session.scalar(
        select(ProductReport)
        .where(
            ProductReport.account_id == account_id,
            ProductReport.product_id == product_id,
            ProductReport.reason == body.reason,
            ProductReport.status == "open",
        )
        .order_by(ProductReport.created_at, ProductReport.id)
        .limit(1)
    )
    if existing is not None:
        await session.commit()
        return existing, False
    report = ProductReport(
        account_id=account_id, product_id=product_id, reason=body.reason, note=body.note
    )
    session.add(report)
    await session.flush()
    await session.refresh(report)
    await session.commit()
    return report, True
