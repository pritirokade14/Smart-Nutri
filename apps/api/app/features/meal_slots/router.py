from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query, Response
from sqlalchemy.ext.asyncio import AsyncSession

from app.core import time as core_time
from app.core.config import Settings, get_app_settings
from app.core.consent import CONSENT_RESPONSES
from app.core.errors import ERROR_RESPONSES
from app.core.ratelimit import limit
from app.db.session import get_session
from app.features.me import service as me_service
from app.features.me.dependencies import CurrentAccount, current_account_row
from app.features.meal_slots import service
from app.features.meal_slots.schemas import (
    ArchiveOut,
    MealSlotCreateIn,
    MealSlotOut,
    MealSlotRenameIn,
    MealSlotsListOut,
    MealSlotsOrderIn,
    MealSlotsOut,
)
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


_WRITE = {**ERROR_RESPONSES, **CONSENT_RESPONSES}


@router.post(
    "",
    operation_id="meal_slots_create",
    response_model=MealSlotOut,
    status_code=201,
    responses={
        **_WRITE,
        200: {"model": MealSlotOut, "description": "Already created with this client_id"},
    },
    dependencies=[Depends(limit("diary_writes"))],  # first: it commits the session
)
async def meal_slots_create(
    body: MealSlotCreateIn,
    response: Response,
    current: Current,
    session: Session,
    settings: Annotated[Settings, Depends(get_app_settings)],
) -> MealSlotOut:
    """Add a custom meal (at most 6 active; 422 `meal_slot_limit_reached` with `details.max`).
    The label is user text: 1 to 30 characters, trimmed, no control characters, unique
    case-insensitively among active meals (422 `meal_slot_label_duplicate`, label not echoed).
    A repeated `client_id` returns the stored meal with 200."""
    member = await targets_service.resolve_member(
        session, current.account.id, body.member_id, settings
    )
    row, created = await service.create_slot(session, member, body)
    out = service.to_out(row)
    await session.commit()
    if not created:
        response.status_code = 200
    return out


@router.put(
    "/order",
    operation_id="meal_slots_reorder",
    response_model=MealSlotsListOut,
    responses=_WRITE,
    dependencies=[Depends(limit("diary_writes"))],
)
async def meal_slots_reorder(
    body: MealSlotsOrderIn,
    current: Current,
    session: Session,
    settings: Annotated[Settings, Depends(get_app_settings)],
) -> MealSlotsListOut:
    """Set the order. `ids` must be every active meal exactly once (else 422
    `validation_error`, `fields: ["body.ids"]`); an unknown id is 404 `meal_slot_not_found`."""
    member = await targets_service.resolve_member(
        session, current.account.id, body.member_id, settings
    )
    rows = await service.reorder_slots(session, member, body.ids)
    out = MealSlotsListOut(items=[service.to_out(r) for r in rows])
    await session.commit()
    return out


@router.patch(
    "/{slot_id}",
    operation_id="meal_slots_rename",
    response_model=MealSlotOut,
    responses=_WRITE,
    dependencies=[Depends(limit("diary_writes"))],
)
async def meal_slots_rename(
    slot_id: UUID,
    body: MealSlotRenameIn,
    current: Current,
    session: Session,
    settings: Annotated[Settings, Depends(get_app_settings)],
    member_id: Annotated[UUID | None, Query()] = None,
) -> MealSlotOut:
    """Rename a meal or change its usual time. Null fields are unchanged; use
    `clear_custom_label` (default meals only) or `clear_time_window` to remove. Entries keep
    their meal. 422 `meal_slot_archived` for a removed meal."""
    member = await targets_service.resolve_member(session, current.account.id, member_id, settings)
    row = await service.rename_slot(session, member, slot_id, body)
    out = service.to_out(row)
    await session.commit()
    return out


@router.delete(
    "/{slot_id}",
    operation_id="meal_slots_archive",
    response_model=ArchiveOut,
    responses=_WRITE,
    dependencies=[Depends(limit("diary_writes"))],
)
async def meal_slots_archive(
    slot_id: UUID,
    current: Current,
    session: Session,
    settings: Annotated[Settings, Depends(get_app_settings)],
    member_id: Annotated[UUID | None, Query()] = None,
) -> ArchiveOut:
    """Remove a meal. One with logged entries is archived (they stay on their day); one
    without is deleted. Repeating it is a no-op. 422 `meal_slot_last_active` for the last one."""
    member = await targets_service.resolve_member(session, current.account.id, member_id, settings)
    result = await service.archive_slot(session, member, slot_id)
    await session.commit()
    return ArchiveOut(result=result)
