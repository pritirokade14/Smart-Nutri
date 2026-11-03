from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings, get_app_settings
from app.core.errors import ERROR_RESPONSES, ErrorEnvelope
from app.core.ratelimit import limit
from app.core.time import today_ist
from app.db.session import get_session
from app.features.analyze import service
from app.features.analyze.schemas import AnalyzeOut, AnalyzeRequest
from app.features.me.dependencies import CurrentAccount, current_account_row
from app.integrations.callmissed import get_llm_provider
from app.integrations.openfoodfacts import OffClient, get_off_client
from app.integrations.providers import LLMProvider

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
    llm: Annotated[LLMProvider, Depends(get_llm_provider)],
) -> AnalyzeOut:
    return await service.analyze_for_account(
        session,
        off,
        current.ctx.account_id,
        body,
        settings=settings,
        today=today_ist(),
        llm=llm,
        email=current.ctx.email,
    )
