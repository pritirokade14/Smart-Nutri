from datetime import date, datetime
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query, Response
from pydantic import AwareDatetime
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings, get_app_settings
from app.core.errors import ERROR_RESPONSES, ErrorEnvelope
from app.core.ratelimit import limit
from app.core.time import today_ist
from app.db.session import get_session
from app.features.me.dependencies import CurrentAccount, current_account_row
from app.features.meals import copy as copy_service
from app.features.meals import service
from app.features.meals.schemas import (
    CopyIn,
    CopyOut,
    MealIn,
    MealOut,
    MealPatch,
    Summary,
    SummaryPeriod,
    WeekCounts,
)
from app.features.members import service as members_service
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
    """Log "I ate this" for a member (default: the primary): 201 for a new log, 200 with the
    stored log when ``client_id`` was already used (offline retries never duplicate).

    The slot defaults to the server's pick for the local time; ``local_date`` logs onto a past
    day; ``quick`` logs typed kcal and macros (blanks stay unknown). The response is redacted
    with the member's numbers display."""
    row, created = await service.log_meal(
        session, current.account.id, body, off=off, settings=settings
    )
    if not created:
        response.status_code = 200
    member = await members_service.get_member(session, current.account.id, row.member_id)
    return service.to_meal_out(row, await service.hidden_for_member(session, member))


@router.post(
    "/copy",
    operation_id="meals_copy",
    response_model=CopyOut,
    status_code=201,
    responses={
        **ERROR_RESPONSES,
        200: {"model": CopyOut, "description": "Every copy already existed (a retry): no new rows"},
    },
)
async def meals_copy(
    body: CopyIn,
    response: Response,
    current: Current,
    session: Session,
    settings: Annotated[Settings, Depends(get_app_settings)],
) -> CopyOut:
    """Copy one meal (``from_slot_id``) or the whole day onto another day (today or up to 30
    days back). Each copy keeps its source's saved food and portion, never reads the product
    again, and counts against the daily log limit. ``client_id`` is required: a retry returns
    the same rows with 200 and creates nothing. The response is redacted with the member's
    numbers display."""
    rows, created = await copy_service.copy_entries(session, current.account.id, body, settings)
    if not created:
        response.status_code = 200
    member = await members_service.get_member(session, current.account.id, rows[0].member_id)
    hidden = await service.hidden_for_member(session, member)
    return CopyOut(created=[service.to_meal_out(r, hidden) for r in rows])


@router.get("", operation_id="meals_list", response_model=list[MealOut])
async def meals_list(
    current: Current,
    session: Session,
    member_id: Annotated[UUID | None, Query(description="Defaults to the primary member")] = None,
    from_: Annotated[AwareDatetime | None, Query(alias="from")] = None,
    to: Annotated[AwareDatetime | None, Query()] = None,
    local_date: Annotated[
        date | None, Query(description="One local day; wins over from and to")
    ] = None,
) -> list[MealOut]:
    """A member's logs, newest first (at most 200), redacted with their numbers display.
    ``local_date`` returns one local day. Default range: the last 7 local days."""
    account_id = current.account.id
    member = await service.member_for_list(session, account_id, member_id)
    if local_date is not None:
        rows = await service.list_meals_by_date(
            session, account_id, member.id, local_date, local_date
        )
    else:
        default_start, default_end = await service.default_range(session, account_id)
        start: datetime = from_ or default_start
        end: datetime = to or default_end
        rows = await service.list_meals(session, account_id, member.id, start, end)
    hidden = await service.hidden_for_member(session, member)
    out = [service.to_meal_out(r, hidden) for r in rows]
    await session.commit()  # the primary member may have been created
    return out


@router.patch(
    "/{meal_id}",
    operation_id="meals_update",
    response_model=MealOut,
    responses=ERROR_RESPONSES,
    dependencies=[Depends(limit("meal_logs"))],  # first: it commits the session
)
async def meals_update(
    meal_id: UUID,
    body: MealPatch,
    current: Current,
    session: Session,
    settings: Annotated[Settings, Depends(get_app_settings)],
) -> MealOut:
    """Edit an entry: portion, slot, time or (quick adds only) the typed values. ``null`` means
    unchanged. A new portion is recomputed from the entry's own saved food, so editing one
    entry never changes another and never reads the product again."""
    row = await service.update_meal(session, current.account.id, meal_id, body, settings=settings)
    member = await members_service.get_member(session, current.account.id, row.member_id)
    out = service.to_meal_out(row, await service.hidden_for_member(session, member))
    await session.commit()
    return out


@router.get("/summary", operation_id="meals_summary", response_model=Summary)
async def meals_summary(
    current: Current,
    session: Session,
    member_id: Annotated[UUID, Query()],
    period: Annotated[SummaryPeriod, Query()] = SummaryPeriod.DAY,
    date_: Annotated[
        date | None, Query(alias="date", description="Local date; default today")
    ] = None,
) -> Summary:
    """Totals of sugar, salt, protein and kcal against the member's daily limits (pending
    clinician review). A nutrient missing on any logged label sets ``incomplete`` and is never
    counted as 0."""
    out = await service.member_summary(session, current.account.id, member_id, period, date_)
    await session.commit()  # today's frozen target row may have been written
    return out


@router.get("/week_counts", operation_id="meals_week_counts", response_model=WeekCounts)
async def meals_week_counts(
    current: Current,
    session: Session,
    date_: Annotated[
        date | None, Query(alias="date", description="IST date; default today")
    ] = None,
) -> WeekCounts:
    """Counts for the weekly share text (products checked, items logged), whole family."""
    return await service.week_counts(session, current.account.id, date_ or today_ist())


@router.delete("/{meal_id}", operation_id="meals_delete", status_code=204)
async def meals_delete(meal_id: UUID, current: Current, session: Session) -> Response:
    await service.delete_meal(session, current.account.id, meal_id)
    return Response(status_code=204)
