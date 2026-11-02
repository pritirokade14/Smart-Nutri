from datetime import UTC, datetime
from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings, get_app_settings
from app.core.errors import ERROR_RESPONSES, ErrorEnvelope
from app.core.ratelimit import limit
from app.db.session import get_session
from app.features.analyze import service
from app.features.analyze.schemas import AnalyzeOut, AnalyzeRequest
from app.features.me.dependencies import CurrentAccount, current_account_row
from app.integrations.openfoodfacts import OffClient, get_off_client

router = APIRouter(prefix="/v1/analyze", tags=["analyze"])

_RESPONSES = {
    **ERROR_RESPONSES,
    503: {"model": ErrorEnvelope, "description": "Open Food Facts unavailable"},
}


@router.post(
    "",
    operation_id="analyze_create",
    response_model=AnalyzeOut,
    responses=_RESPONSES,
    dependencies=[Depends(limit("analyze"))],  # first: it commits the session
)
async def analyze_create(
    body: AnalyzeRequest,
    current: Annotated[CurrentAccount, Depends(current_account_row)],
    session: Annotated[AsyncSession, Depends(get_session)],
    off: Annotated[OffClient, Depends(get_off_client)],
    settings: Annotated[Settings, Depends(get_app_settings)],
) -> AnalyzeOut:
    return await service.analyze_for_account(
        session,
        off,
        current.ctx.account_id,
        body,
        settings=settings,
        today=datetime.now(UTC).date(),
    )
