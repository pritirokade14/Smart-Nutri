"""Custom foods routes (Plan 12 Task 11; spec 6.3). Gated on `terms` by prefix (`CONSENT_GATES`),
before any rate limit. Account-owned (no member): every query is scoped by account."""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query, Response
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.consent import CONSENT_RESPONSES
from app.core.errors import ERROR_RESPONSES
from app.core.ratelimit import limit
from app.db.session import get_session
from app.features.custom_foods import service
from app.features.custom_foods.schemas import CustomFoodIn, CustomFoodOut, CustomFoodsOut
from app.features.me.dependencies import CurrentAccount, current_account_row

router = APIRouter(prefix="/v1/custom-foods", tags=["custom-foods"])

Current = Annotated[CurrentAccount, Depends(current_account_row)]
Session = Annotated[AsyncSession, Depends(get_session)]

_RESPONSES = {**ERROR_RESPONSES, **CONSENT_RESPONSES}


@router.get(
    "", operation_id="custom_foods_list", response_model=CustomFoodsOut, responses=_RESPONSES
)
async def custom_foods_list(
    current: Current,
    session: Session,
    limit_: Annotated[int, Query(alias="limit", ge=1, le=100)] = 50,
    cursor: Annotated[str | None, Query(max_length=200)] = None,
) -> CustomFoodsOut:
    """The account's own foods, most recently changed first. `next_cursor` is opaque."""
    rows, next_cursor = await service.list_foods(session, current.account.id, limit_, cursor)
    return CustomFoodsOut(
        items=[await service.to_out(session, r) for r in rows], next_cursor=next_cursor
    )


@router.post(
    "",
    operation_id="custom_foods_create",
    response_model=CustomFoodOut,
    status_code=201,
    responses={
        **_RESPONSES,
        200: {"model": CustomFoodOut, "description": "Already created with this client_id"},
    },
    dependencies=[Depends(limit("diary_writes"))],  # first: it commits the session
)
async def custom_foods_create(
    body: CustomFoodIn, response: Response, current: Current, session: Session
) -> CustomFoodOut:
    """Save a food from its label. A blank nutrient is unknown (never 0); energy, or one of
    protein, carbs and fat, is required (422 `custom_food_nutrients_empty`); implausible values
    are 422 `implausible_value`; a barcode already on another of your foods is 422
    `barcode_already_used`. A repeated `client_id` returns the stored food with 200. It is never
    in the public catalogue and never reaches a verdict."""
    row, created = await service.create_food(session, current.account.id, body)
    out = await service.to_out(session, row)
    await session.commit()
    if not created:
        response.status_code = 200
    return out


@router.put(
    "/{food_id}",
    operation_id="custom_foods_update",
    response_model=CustomFoodOut,
    responses=_RESPONSES,
    dependencies=[Depends(limit("diary_writes"))],
)
async def custom_foods_update(
    food_id: UUID, body: CustomFoodIn, current: Current, session: Session
) -> CustomFoodOut:
    """Replace the food (a nutrient left out becomes unknown; the portions are replaced). Past
    diary entries keep the values they were logged with."""
    row = await service.update_food(session, current.account.id, food_id, body)
    out = await service.to_out(session, row)
    await session.commit()
    return out


@router.delete(
    "/{food_id}",
    operation_id="custom_foods_delete",
    status_code=204,
    responses=_RESPONSES,
    dependencies=[Depends(limit("diary_writes"))],
)
async def custom_foods_delete(food_id: UUID, current: Current, session: Session) -> Response:
    """Delete the food. Diary entries and recipe ingredients keep their name and values (their
    reference becomes null); recipes using it show it as unavailable."""
    await service.delete_food(session, current.account.id, food_id)
    await session.commit()
    return Response(status_code=204)
