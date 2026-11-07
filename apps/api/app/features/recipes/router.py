"""Recipes routes (Plan 12 Task 12; spec 6.3). Gated on `terms` by prefix (`CONSENT_GATES`),
before any rate limit. Recipes belong to the account; the numbers are redacted with the primary
member's numbers display (solo only, Q9)."""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query, Response
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings, get_app_settings
from app.core.consent import CONSENT_RESPONSES
from app.core.errors import ERROR_RESPONSES, ErrorEnvelope
from app.core.ratelimit import limit
from app.db.session import get_session
from app.features.me.dependencies import CurrentAccount, current_account_row
from app.features.meals import service as meals_service
from app.features.recipes import service
from app.features.recipes.schemas import RecipeIn, RecipeOut, RecipesOut
from app.features.targets import service as targets_service
from app.features.targets.schemas import NumbersHidden
from app.integrations.openfoodfacts import OffClient, get_off_client

router = APIRouter(prefix="/v1/recipes", tags=["recipes"])

Current = Annotated[CurrentAccount, Depends(current_account_row)]
Session = Annotated[AsyncSession, Depends(get_session)]
AppSettings = Annotated[Settings, Depends(get_app_settings)]
Off = Annotated[OffClient, Depends(get_off_client)]

_RESPONSES = {
    **ERROR_RESPONSES,
    **CONSENT_RESPONSES,
    503: {"model": ErrorEnvelope, "description": "Open Food Facts unavailable"},
}


async def _hidden(
    session: AsyncSession, current: CurrentAccount, settings: Settings
) -> NumbersHidden:
    member = await targets_service.resolve_member(session, current.account.id, None, settings)
    return await meals_service.hidden_for_member(session, member)


@router.get("", operation_id="recipes_list", response_model=RecipesOut, responses=_RESPONSES)
async def recipes_list(
    current: Current,
    session: Session,
    limit_: Annotated[int, Query(alias="limit", ge=1, le=100)] = 50,
    cursor: Annotated[str | None, Query(max_length=200)] = None,
) -> RecipesOut:
    """The account's recipes, most recently changed first (no nutrients: open one for those)."""
    rows, next_cursor = await service.list_recipes(session, current.account.id, limit_, cursor)
    return RecipesOut(items=[service.to_summary(r) for r in rows], next_cursor=next_cursor)


@router.get(
    "/{recipe_id}", operation_id="recipes_get", response_model=RecipeOut, responses=_RESPONSES
)
async def recipes_get(
    recipe_id: UUID, current: Current, session: Session, settings: AppSettings
) -> RecipeOut:
    """One recipe with its ingredients. Per-100 g and per-serving values are the sum of the
    KNOWN ingredients: a nutrient in `incomplete_nutrients` is 'at least' that much. Numbers the
    member hid are null."""
    row = await service.get_owned(session, current.account.id, recipe_id)
    out = await service.to_out(session, row, await _hidden(session, current, settings))
    await session.commit()  # the primary member may have just been created
    return out


@router.post(
    "",
    operation_id="recipes_create",
    response_model=RecipeOut,
    status_code=201,
    responses={
        **_RESPONSES,
        200: {"model": RecipeOut, "description": "Already created with this client_id"},
    },
    dependencies=[Depends(limit("diary_writes"))],  # first: it commits the session
)
async def recipes_create(
    body: RecipeIn,
    response: Response,
    current: Current,
    session: Session,
    off: Off,
    settings: AppSettings,
) -> RecipeOut:
    """Build a recipe from 1 to 50 ingredients. Each is a food, one of your custom foods, one
    of our products or an Open Food Facts barcode, with a quantity and a household unit; a
    unit with no grams is 422 `unit_grams_unknown` with the ingredient's `details.position`.
    The basis weight is the cooked weight, or else the raw total (422 `recipe_weight_invalid`:
    `cooked_weight_required` or `out_of_range`, 0.2 to 3 times the raw total). A repeated
    `client_id` returns the stored recipe with 200."""
    row, created = await service.create_recipe(
        session, off, current.account.id, body, settings=settings
    )
    out = await service.to_out(session, row, await _hidden(session, current, settings))
    await session.commit()
    if not created:
        response.status_code = 200
    return out


@router.put(
    "/{recipe_id}",
    operation_id="recipes_update",
    response_model=RecipeOut,
    responses=_RESPONSES,
    dependencies=[Depends(limit("diary_writes"))],
)
async def recipes_update(
    recipe_id: UUID,
    body: RecipeIn,
    current: Current,
    session: Session,
    off: Off,
    settings: AppSettings,
) -> RecipeOut:
    """Replace the recipe and its ingredients. Past diary entries keep the values they were
    logged with. An ingredient whose custom food was deleted must be replaced."""
    row = await service.update_recipe(
        session, off, current.account.id, recipe_id, body, settings=settings
    )
    out = await service.to_out(session, row, await _hidden(session, current, settings))
    await session.commit()
    return out


@router.delete(
    "/{recipe_id}",
    operation_id="recipes_delete",
    status_code=204,
    responses=_RESPONSES,
    dependencies=[Depends(limit("diary_writes"))],
)
async def recipes_delete(recipe_id: UUID, current: Current, session: Session) -> Response:
    """Delete the recipe. Diary entries keep their name and values (their reference becomes
    null)."""
    await service.delete_recipe(session, current.account.id, recipe_id)
    await session.commit()
    return Response(status_code=204)
