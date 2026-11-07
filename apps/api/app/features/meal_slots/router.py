from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core import time as core_time
from app.core.config import Settings, get_app_settings
from app.core.consent import CONSENT_RESPONSES
from app.core.errors import ERROR_RESPONSES
from app.db.session import get_session
from app.features.me import service as me_service
from app.features.me.dependencies import CurrentAccount, current_account_row
from app.features.meal_slots import service
from app.features.meal_slots.schemas import MealSlotsOut
from app.features.targets import service as targets_service

router = APIRouter(prefix="/v1/meal-slots", tags=["meal-slots"])

Current = Annotated[CurrentAccount, Depends(current_account_row)]
Session = Annotated[AsyncSession, Depends(get_session)]


@router.get(
    "",
    operation_id="meal_slots_list",
    response_model=MealSlotsOut,
    responses={**ERROR_RESPONSES, **CONSENT_RESPONSES},
)
async def meal_slots_list(
    current: Current,
    session: Session,
    settings: Annotated[Settings, Depends(get_app_settings)],
    member_id: Annotated[UUID | None, Query()] = None,
    include_archived: Annotated[bool, Query()] = False,
) -> MealSlotsOut:
    """The member's meal slots in order, plus `suggested_slot_id`, the server's pick for the
    current moment (clients preselect it and never compute a slot). Creates the four defaults on
    the first call. Needs only `terms`: slots hold no health data. 404 `member_not_found` for
    another account's member; 422 `diary_member_not_enabled` for a non-primary member."""
    account_id = current.account.id
    member = await targets_service.resolve_member(session, account_id, member_id, settings)
    rows = await service.list_slots(session, member, include_archived=include_archived)
    zone_name = await me_service.account_timezone(session, account_id)
    suggested = await service.slot_for_entry(
        session, member, None, core_time.local_clock(core_time.now_utc(), zone_name)
    )
    await session.commit()  # the defaults or the primary member may have just been created
    return MealSlotsOut(items=[service.to_out(r) for r in rows], suggested_slot_id=suggested.id)
