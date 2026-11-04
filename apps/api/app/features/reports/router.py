from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Response
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.ratelimit import limit
from app.db.session import get_session
from app.features.me.dependencies import CurrentAccount, current_account_row
from app.features.reports import service
from app.features.reports.schemas import ReportCreate, ReportOut

# Mounted under /v1/products, but owned by the reports feature (tag `reports`).
router = APIRouter(prefix="/v1/products", tags=["reports"])


@router.post(
    "/{product_id}/reports",
    operation_id="reports_create",
    status_code=201,
    response_model=ReportOut,
    responses={200: {"model": ReportOut, "description": "Same open report already exists"}},
    dependencies=[Depends(limit("reports"))],  # first: it commits the session
)
async def reports_create(
    product_id: UUID,
    body: ReportCreate,
    response: Response,
    current: Annotated[CurrentAccount, Depends(current_account_row)],
    session: Annotated[AsyncSession, Depends(get_session)],
) -> ReportOut:
    """Report a problem with a product's data, for review. 201 with the new report, or 200
    with the existing one when the same reason is already open (idempotent). Rate-limited
    per account per day."""
    report, created = await service.create_report(session, current.ctx.account_id, product_id, body)
    if not created:
        response.status_code = 200
    return ReportOut.model_validate(report, from_attributes=True)
