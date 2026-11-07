"""Foods routes (Plan 12 Task 4; spec 6.3). Gated on `terms` by prefix (`CONSENT_GATES`), before
any rate limit. `/search` and `/units` are declared before `/{kind}/{id}`.

Solo only (Q9): the member behind numbers hiding is resolved with `resolve_member`."""

from decimal import Decimal
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query, Response
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings, get_app_settings
from app.core.consent import CONSENT_RESPONSES
from app.core.errors import ERROR_RESPONSES, ApiError, ErrorEnvelope
from app.core.ratelimit import limit
from app.db.session import get_session
from app.features.foods import service
from app.features.foods.resolve import FoodRef
from app.features.foods.schemas import (
    FoodDetailOut,
    FoodKindPath,
    FoodSearchOut,
    PortionIn,
    SearchKind,
    UnitOut,
)
from app.features.me.dependencies import CurrentAccount, current_account_row
from app.features.meals import service as meals_service
from app.features.products import search as products_search
from app.features.targets import service as targets_service
from app.integrations.openfoodfacts import OffClient, get_off_client

router = APIRouter(prefix="/v1/foods", tags=["foods"])

Current = Annotated[CurrentAccount, Depends(current_account_row)]
Session = Annotated[AsyncSession, Depends(get_session)]
AppSettings = Annotated[Settings, Depends(get_app_settings)]
Off = Annotated[OffClient, Depends(get_off_client)]
MemberQuery = Annotated[UUID | None, Query(description="Defaults to the primary member")]

MIN_QUERY, MAX_QUERY = 2, 80

_RESPONSES = {
    **ERROR_RESPONSES,
    **CONSENT_RESPONSES,
    503: {"model": ErrorEnvelope, "description": "Open Food Facts unavailable"},
}


def foods_search_query(
    q: Annotated[
        str,
        Query(
            max_length=MAX_QUERY,
            description=(
                f"{MIN_QUERY} to {MAX_QUERY} characters after trimming and collapsing spaces; "
                "shorter is 422 search_query_too_short"
            ),
        ),
    ],
) -> str:
    """Refused when shorter than MIN_QUERY once normalised. Runs before limit(), so a too-short
    query costs no quota and touches no database."""
    if len(products_search.normalise_query(q)) < MIN_QUERY:
        raise ApiError(
            "search_query_too_short",
            422,
            details={"fields": ["query.q"], "min_length": MIN_QUERY},
        )
    return q


@router.get(
    "/search",
    operation_id="foods_search",
    response_model=FoodSearchOut,
    responses=_RESPONSES,
    dependencies=[Depends(foods_search_query), Depends(limit("search"))],
)
async def foods_search(
    current: Current,
    session: Session,
    off: Off,
    settings: AppSettings,
    q: Annotated[str, Depends(foods_search_query)],
    kinds: Annotated[
        list[SearchKind] | None,
        Query(
            description=(
                "Which sources to search; default all (food = generic foods and dishes; "
                "custom_food and recipe = yours, listed first)"
            )
        ),
    ] = None,
    limit_: Annotated[int, Query(alias="limit", ge=1, le=50)] = 20,
) -> FoodSearchOut:
    """Search generic foods and Indian dishes first, then packaged products (our catalogue and
    Open Food Facts). Hits carry no nutrients. When Open Food Facts cannot answer, the other
    results still come back with `partial: true` and `failed_sources: ["off"]`. USDA and
    Open Food Facts credits ride on each hit."""
    out = await service.search_foods(
        session,
        off,
        q,
        limit_,
        set(kinds) if kinds else set(SearchKind),
        account_id=current.account.id,
        settings=settings,
    )
    await session.commit()  # the OFF search cache write
    return out


@router.get(
    "/units",
    operation_id="foods_units_list",
    response_model=list[UnitOut],
    responses={**ERROR_RESPONSES, **CONSENT_RESPONSES},
)
async def foods_units_list(current: Current, session: Session) -> list[UnitOut]:
    """The household units (kind, volume or grams) in display order. Whether a unit applies to
    a food is `foods_get`'s `units`; the label is the i18n key `unit.<code>`."""
    return await service.list_units(session)


async def _hidden(session: AsyncSession, current: CurrentAccount, member_id, settings):
    member = await targets_service.resolve_member(session, current.account.id, member_id, settings)
    return await meals_service.hidden_for_member(session, member)


@router.get(
    "/barcode/{barcode}",
    operation_id="foods_by_barcode",
    response_model=FoodDetailOut,
    responses=_RESPONSES,
    dependencies=[Depends(limit("product_lookups"))],
)
async def foods_by_barcode(
    barcode: str,
    current: Current,
    session: Session,
    off: Off,
    settings: AppSettings,
    member_id: MemberQuery = None,
) -> FoodDetailOut:
    """Look a scanned barcode up for LOGGING: your own custom food with that barcode first, then
    our product, then Open Food Facts. For the verdict use `products_get_by_barcode` and
    `analyze`: they never see custom foods. 422 `invalid_barcode`, 404 `product_not_found`, 503
    `off_unavailable`."""
    hidden = await _hidden(session, current, member_id, settings)
    out = await service.food_by_barcode(
        session, off, barcode, hidden, account_id=current.account.id, settings=settings
    )
    await session.commit()  # the primary member, or an OFF cache write
    return out


@router.get(
    "/{kind}/{id}",
    operation_id="foods_get",
    response_model=FoodDetailOut,
    responses=_RESPONSES,
    dependencies=[Depends(limit("product_lookups"))],
)
async def foods_get(
    kind: FoodKindPath,
    id: str,
    current: Current,
    session: Session,
    off: Off,
    settings: AppSettings,
    member_id: MemberQuery = None,
) -> FoodDetailOut:
    """One food with the per-100 values and ONLY the units that resolve (a unit with nothing to
    convert it by is never listed), the default unit, the units the user may set their own
    grams for, credits and, for a dish, its ingredients. `id` is a uuid, or the barcode for
    `off`. Per-100 values the member hid are null. Household measures and dishes are pending
    dietitian review."""
    hidden = await _hidden(session, current, member_id, settings)
    out = await service.food_detail(
        session,
        off,
        FoodRef(kind.value, id),  # type: ignore[arg-type]
        hidden,
        account_id=current.account.id,
        settings=settings,
    )
    await session.commit()  # the primary member, or an OFF cache write
    return out


@router.put(
    "/{kind}/{id}/portions/{unit}",
    operation_id="foods_portion_put",
    response_model=FoodDetailOut,
    responses=_RESPONSES,
    dependencies=[Depends(limit("diary_writes"))],  # first: it commits the session
)
async def foods_portion_put(
    kind: FoodKindPath,
    id: str,
    unit: str,
    body: PortionIn,
    current: Current,
    session: Session,
    off: Off,
    settings: AppSettings,
    member_id: MemberQuery = None,
) -> FoodDetailOut:
    """Set YOUR grams for one unit of one food (for example one roti = 35 g). Count and volume
    units only; `serving` and the mass units are 422 `unit_not_supported`. The value belongs to
    the account, replaces ours for you, and never changes a past diary entry."""
    hidden = await _hidden(session, current, member_id, settings)
    out = await service.put_portion(
        session,
        off,
        FoodRef(kind.value, id),  # type: ignore[arg-type]
        unit,
        Decimal(repr(body.grams_per_unit)),
        hidden,
        account_id=current.account.id,
        settings=settings,
    )
    await session.commit()
    return out


@router.delete(
    "/{kind}/{id}/portions/{unit}",
    operation_id="foods_portion_delete",
    status_code=204,
    responses={**ERROR_RESPONSES, **CONSENT_RESPONSES},
)
async def foods_portion_delete(
    kind: FoodKindPath, id: str, unit: str, current: Current, session: Session
) -> Response:
    """Remove YOUR value for this unit; ours applies again. 204 even when you had none."""
    await service.delete_portion(
        session,
        FoodRef(kind.value, id),  # type: ignore[arg-type]
        unit,
        account_id=current.account.id,
    )
    await session.commit()
    return Response(status_code=204)
