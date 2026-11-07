"""Favourites routes (Plan 12 Task 17; spec 6.4). Gated on `terms` by prefix (`CONSENT_GATES`),
before any rate limit. Solo only: the member resolves like the diary's (Q9). Writes use the
`diary_writes` bucket; logging a favourite meal also counts each entry against `meal_logs`."""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query, Response
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings, get_app_settings
from app.core.consent import CONSENT_RESPONSES
from app.core.errors import ERROR_RESPONSES, ErrorEnvelope
from app.core.ratelimit import limit
from app.db.session import get_session
from app.features.favourites import service
from app.features.favourites.schemas import (
    FavouriteIn,
    FavouriteLogIn,
    FavouriteLogOut,
    FavouriteMealIn,
    FavouriteOut,
    FavouritesOut,
)
from app.features.me.dependencies import CurrentAccount, current_account_row
from app.features.meals import service as meals_service
from app.features.members import service as members_service
from app.integrations.openfoodfacts import OffClient, get_off_client

router = APIRouter(prefix="/v1/favourites", tags=["favourites"])

Current = Annotated[CurrentAccount, Depends(current_account_row)]
Session = Annotated[AsyncSession, Depends(get_session)]
AppSettings = Annotated[Settings, Depends(get_app_settings)]
Off = Annotated[OffClient, Depends(get_off_client)]

_RESPONSES = {**ERROR_RESPONSES, **CONSENT_RESPONSES}


@router.get("", operation_id="favourites_list", response_model=FavouritesOut, responses=_RESPONSES)
async def favourites_list(
    current: Current,
    session: Session,
    settings: AppSettings,
    member_id: Annotated[UUID | None, Query(description="Defaults to the primary member")] = None,
) -> FavouritesOut:
    """The member's favourite foods and saved meals, newest first (at most 200, no cursor)."""
    rows = await service.list_favourites(session, current.account.id, member_id, settings)
    out = FavouritesOut(items=[service.to_out(r) for r in rows])
    await session.commit()  # the primary member may have been created
    return out


@router.post(
    "",
    operation_id="favourites_add",
    response_model=FavouriteOut,
    status_code=201,
    responses={
        **_RESPONSES,
        200: {"model": FavouriteOut, "description": "Already a favourite: nothing changed"},
        503: {"model": ErrorEnvelope, "description": "Open Food Facts unavailable"},
    },
    dependencies=[Depends(limit("diary_writes"))],  # first: it commits the session
)
async def favourites_add(
    body: FavouriteIn,
    response: Response,
    current: Current,
    session: Session,
    settings: AppSettings,
    off: Off,
) -> FavouriteOut:
    """Star a food with an optional default portion (the one a tap logs). 201 for a new
    favourite, 200 with the stored one when the food is already starred. 422 `favourite_limit`
    past 200, `food_retired`, `unit_grams_unknown`, `invalid_product_ref`."""
    row, created = await service.add_food(
        session, current.account.id, body, off=off, settings=settings
    )
    if not created:
        response.status_code = 200
    return service.to_out(row)


@router.post(
    "/meals",
    operation_id="favourites_add_meal",
    response_model=FavouriteOut,
    status_code=201,
    responses={
        **_RESPONSES,
        200: {"model": FavouriteOut, "description": "Already saved with this client_id"},
    },
    dependencies=[Depends(limit("diary_writes"))],
)
async def favourites_add_meal(
    body: FavouriteMealIn,
    response: Response,
    current: Current,
    session: Session,
    settings: AppSettings,
) -> FavouriteOut:
    """Save one meal (a slot on a day) under a name you type, exactly as typed. The entries are
    kept as they were (no food is read again). 422 `copy_source_empty`, `copy_too_many` (more
    than 50), `date_in_future`, `favourite_limit`; 404 `meal_slot_not_found`."""
    row, created = await service.add_meal(session, current.account.id, body, settings)
    if not created:
        response.status_code = 200
    return service.to_out(row)


@router.post(
    "/{favourite_id}/log",
    operation_id="favourites_log",
    response_model=FavouriteLogOut,
    status_code=201,
    responses={
        **_RESPONSES,
        200: {"model": FavouriteLogOut, "description": "Every entry already existed (a retry)"},
    },
    dependencies=[Depends(limit("diary_writes"))],
)
async def favourites_log(
    favourite_id: UUID,
    body: FavouriteLogIn,
    response: Response,
    current: Current,
    session: Session,
    settings: AppSettings,
) -> FavouriteLogOut:
    """Log a favourite MEAL again, from its saved entries, onto today or a day up to 30 days
    back. ``client_id`` is required: a retry returns the same rows with 200 and creates
    nothing. Each entry counts against the daily log limit. A food favourite is logged with
    `meals_log` instead (422 `validation_error` here). 422 `food_retired` if a saved dish was
    retired; a deleted custom food or recipe logs with a null reference. The response is
    redacted with the member's numbers display."""
    rows, created = await service.log_meal_favourite(
        session, current.account.id, favourite_id, body, settings
    )
    if not created:
        response.status_code = 200
    member = await members_service.get_member(session, current.account.id, rows[0].member_id)
    hidden = await meals_service.hidden_for_member(session, member)
    return FavouriteLogOut(created=[meals_service.to_meal_out(r, hidden) for r in rows])


@router.delete(
    "/{favourite_id}",
    operation_id="favourites_delete",
    status_code=204,
    responses=_RESPONSES,
    dependencies=[Depends(limit("diary_writes"))],
)
async def favourites_delete(favourite_id: UUID, current: Current, session: Session) -> Response:
    """Remove a favourite. Entries already logged from it stay."""
    await service.delete_favourite(session, current.account.id, favourite_id)
    await session.commit()
    return Response(status_code=204)
