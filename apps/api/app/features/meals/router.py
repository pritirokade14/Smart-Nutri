from datetime import datetime
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query, Response
from pydantic import AwareDatetime
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings, get_app_settings
from app.core.errors import ERROR_RESPONSES, ErrorEnvelope
from app.core.ratelimit import limit
from app.db.session import get_session
from app.features.me.dependencies import CurrentAccount, current_account_row
from app.features.meals import service
from app.features.meals.schemas import MealIn, MealOut
from app.integrations.openfoodfacts import OffClient, get_off_client

router = APIRouter(prefix="/v1/meals", tags=["meals"])

Current = Annotated[CurrentAccount, Depends(current_account_row)]
Session = Annotated[AsyncSession, Depends(get_session)]

_LOG_RESPONSES = {
    **ERROR_RESPONSES,
    200: {"model": MealOut, "description": "Already logged with this client_id (no new row)"},
    503: {"model": ErrorEnvelope, "description": "Open Food Facts unavailable"},
}


@router.post(
    "",
    operation_id="meals_log",
    response_model=MealOut,
    status_code=201,
    responses=_LOG_RESPONSES,
    dependencies=[Depends(limit("meal_logs"))],  # first: it commits the session
)
async def meals_log(
    body: MealIn,
    response: Response,
    current: Current,
    session: Session,
    off: Annotated[OffClient, Depends(get_off_client)],
    settings: Annotated[Settings, Depends(get_app_settings)],
) -> MealOut:
    """Log "I ate this" for a member: 201 for a new log, 200 with the stored log when
    ``client_id`` was already used (offline retries never duplicate)."""
    row, created = await service.log_meal(
        session, current.account.id, body, off=off, settings=settings
    )
    if not created:
        response.status_code = 200
    return service.to_meal_out(row)


@router.get("", operation_id="meals_list", response_model=list[MealOut])
async def meals_list(
    current: Current,
    session: Session,
    member_id: Annotated[UUID, Query()],
    from_: Annotated[AwareDatetime | None, Query(alias="from")] = None,
    to: Annotated[AwareDatetime | None, Query()] = None,
) -> list[MealOut]:
    """A member's logs, newest first (at most 200). Default range: the last 7 IST days."""
    default_start, default_end = service.default_range()
    start: datetime = from_ or default_start
    end: datetime = to or default_end
    rows = await service.list_meals(session, current.account.id, member_id, start, end)
    return [service.to_meal_out(r) for r in rows]


@router.delete("/{meal_id}", operation_id="meals_delete", status_code=204)
async def meals_delete(meal_id: UUID, current: Current, session: Session) -> Response:
    await service.delete_meal(session, current.account.id, meal_id)
    return Response(status_code=204)
