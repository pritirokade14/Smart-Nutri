"""Diary routes (Plan 11 Task 7; spec 6.2). Gated on `terms` by prefix (`CONSENT_GATES`); the
targets part of the day and week views checks `health_data` inside the service."""

from datetime import date
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings, get_app_settings
from app.core.consent import CONSENT_RESPONSES
from app.core.errors import ERROR_RESPONSES
from app.core.ratelimit import limit
from app.db.session import get_session
from app.features.diary import service
from app.features.diary.schemas import (
    DiaryDayOut,
    DiaryDayStatusIn,
    DiaryDayStatusOut,
    DiaryWeekOut,
    RecentsOut,
)
from app.features.me.dependencies import CurrentAccount, current_account_row

router = APIRouter(prefix="/v1/diary", tags=["diary"])

Current = Annotated[CurrentAccount, Depends(current_account_row)]
Session = Annotated[AsyncSession, Depends(get_session)]
AppSettings = Annotated[Settings, Depends(get_app_settings)]
MemberQuery = Annotated[UUID | None, Query(description="Defaults to the primary member")]

_RESPONSES = {**ERROR_RESPONSES, **CONSENT_RESPONSES}


@router.get(
    "/day",
    operation_id="diary_day_get",
    response_model=DiaryDayOut,
    responses=_RESPONSES,
)
async def diary_day_get(
    current: Current,
    session: Session,
    settings: AppSettings,
    member_id: MemberQuery = None,
    date_: Annotated[
        date | None, Query(alias="date", description="Local date; default the account's today")
    ] = None,
) -> DiaryDayOut:
    """One local day of the diary: meal slots with their entries and totals, that day's frozen
    targets, `remaining` and `progress` (all computed here; clients never compute them), and the
    sugar and salt bands. Needs only `terms`: without `health_data`, `targets` is null with
    `targets_status: consent_required` and the entries still load. Numbers the member hid are
    null. Information, not medical advice."""
    out = await service.get_day(session, current.account.id, member_id, date_, settings)
    await session.commit()  # today's frozen row, the default slots or the primary member
    return out


@router.get(
    "/week",
    operation_id="diary_week_get",
    response_model=DiaryWeekOut,
    responses=_RESPONSES,
)
async def diary_week_get(
    current: Current,
    session: Session,
    settings: AppSettings,
    member_id: MemberQuery = None,
    end: Annotated[date | None, Query(description="Last day; default the account's today")] = None,
) -> DiaryWeekOut:
    """The 7 local days ending at `end`, oldest first, each against that day's own frozen
    targets. Averages cover days with items that are not marked partial, and an average with an
    unknown value is flagged. Needs only `terms`."""
    out = await service.get_week(session, current.account.id, member_id, end, settings)
    await session.commit()
    return out


@router.put(
    "/days/{day}/status",
    operation_id="diary_day_status_put",
    response_model=DiaryDayStatusOut,
    responses=_RESPONSES,
    dependencies=[Depends(limit("diary_settings"))],  # first: it commits the session
)
async def diary_day_status_put(
    day: date,
    body: DiaryDayStatusIn,
    current: Current,
    session: Session,
    settings: AppSettings,
) -> DiaryDayStatusOut:
    """Mark a day as not fully logged (`partial_logged: true`) or clear the mark. A marked day
    is left out of the week averages. 422 `date_in_future` for a future day."""
    out = await service.put_status(session, current.account.id, day, body, settings)
    await session.commit()
    return out


@router.get(
    "/recents",
    operation_id="diary_recents_list",
    response_model=RecentsOut,
    responses=_RESPONSES,
)
async def diary_recents_list(
    current: Current,
    session: Session,
    settings: AppSettings,
    member_id: MemberQuery = None,
    slot_id: Annotated[UUID | None, Query(description="Its items come first")] = None,
    limit_: Annotated[int, Query(alias="limit", ge=1, le=30)] = 30,
) -> RecentsOut:
    """Foods the member logged lately, newest first, one per product (quick adds excluded), at
    most 30 from the last 90 days. Needs only `terms`."""
    out = await service.recents(session, current.account.id, member_id, slot_id, limit_, settings)
    await session.commit()  # the default slots or the primary member may have been created
    return out
