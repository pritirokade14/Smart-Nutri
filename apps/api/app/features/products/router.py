from typing import Annotated, Literal
from uuid import UUID

from fastapi import APIRouter, Depends, Query, Response
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings, get_app_settings
from app.core.consent import CONSENT_RESPONSES, gate_for
from app.core.errors import ERROR_RESPONSES, ApiError, ErrorEnvelope
from app.core.ratelimit import limit
from app.core.security import AccountContext, current_account
from app.core.time import today_ist
from app.db.session import get_session
from app.features.me.dependencies import CurrentAccount, current_account_row
from app.features.members import service as members_service
from app.features.products import alternatives, compare, search, service
from app.features.products.schemas import (
    AlternativesOut,
    CompareOut,
    ProductCreate,
    ProductOut,
    PublicProductOut,
    SearchHit,
)
from app.integrations.openfoodfacts import (
    InvalidBarcode,
    OffClient,
    OffUnavailable,
    get_off_client,
)

router = APIRouter(prefix="/v1/products", tags=["products"])

_RESPONSES = {
    **ERROR_RESPONSES,
    503: {"model": ErrorEnvelope, "description": "Open Food Facts unavailable"},
}
# Alternatives and compare (I3): `terms` consent, always. The gate first (a refused call
# costs no quota), then limit(), which commits the session.
_VERDICT_RESPONSES = {**_RESPONSES, **CONSENT_RESPONSES}
_VERDICT_DEPENDENCIES = [Depends(gate_for("product_verdicts")), Depends(limit("product_lookups"))]


async def _find(
    session: AsyncSession,
    off: OffClient,
    barcode: str,
    settings: Settings,
    account_id: UUID | None,
) -> service.ProductLookup:
    try:
        found = await service.lookup_by_barcode(
            session, off, barcode, settings=settings, account_id=account_id
        )
    except InvalidBarcode as exc:
        raise ApiError("invalid_barcode", 422) from exc
    except OffUnavailable as exc:
        raise ApiError("off_unavailable", 503) from exc
    # lookup_by_barcode never commits: persist the OFF cache write (or stale-entry delete).
    await session.commit()
    if found is None:
        raise ApiError("product_not_found", 404)
    return found


@router.get(
    "/barcode/{code}",
    operation_id="products_get_by_barcode",
    response_model=ProductOut,
    responses=_RESPONSES,
    dependencies=[Depends(limit("product_lookups"))],  # first: it commits the session
)
async def products_get_by_barcode(
    code: str,
    ctx: Annotated[AccountContext, Depends(current_account)],
    session: Annotated[AsyncSession, Depends(get_session)],
    off: Annotated[OffClient, Depends(get_off_client)],
    settings: Annotated[Settings, Depends(get_app_settings)],
) -> ProductOut:
    # The caller sees verified products plus their own pending ones (CROSS-PLAN 18).
    return service.to_product_out(await _find(session, off, code, settings, ctx.account_id))


async def _alternatives(
    session: AsyncSession,
    off: OffClient,
    settings: Settings,
    account_id: UUID,
    member_id: UUID | None,
    *,
    product_id: UUID | None = None,
    barcode: str | None = None,
) -> AlternativesOut:
    # The member first: a foreign member never reaches Open Food Facts.
    member = (
        await members_service.get_member(session, account_id, member_id)
        if member_id is not None
        else None
    )
    found = await service.resolve_ref(
        session,
        off,
        product_id=product_id,
        barcode=barcode,
        settings=settings,
        account_id=account_id,
    )
    out = await alternatives.find_alternatives(
        session, off, found, member=member, settings=settings, today=today_ist()
    )
    await session.commit()  # OFF cache writes (product and category search)
    return out


_ALTERNATIVES_DOC = (
    "Up to 5 products from the same Open Food Facts category with a strictly better "
    "Nutri-Score (calculated by SmartNutri). ``member_status`` comes from the rules engine. "
    "With ``member_id``, a product the engine rates ``avoid`` for that member is never "
    "suggested, and safer statuses rank first. "
    "Never an error for a product with no category: ``reason`` says why the list is empty."
)


@router.get(
    "/{product_id}/alternatives",
    operation_id="products_alternatives",
    response_model=AlternativesOut,
    responses=_VERDICT_RESPONSES,
    description=_ALTERNATIVES_DOC,
    dependencies=_VERDICT_DEPENDENCIES,
)
async def products_alternatives(
    product_id: UUID,
    current: Annotated[CurrentAccount, Depends(current_account_row)],
    session: Annotated[AsyncSession, Depends(get_session)],
    off: Annotated[OffClient, Depends(get_off_client)],
    settings: Annotated[Settings, Depends(get_app_settings)],
    member_id: Annotated[UUID | None, Query()] = None,
) -> AlternativesOut:
    return await _alternatives(
        session, off, settings, current.account.id, member_id, product_id=product_id
    )


@router.get(
    "/barcode/{code}/alternatives",
    operation_id="products_alternatives_by_barcode",
    response_model=AlternativesOut,
    responses=_VERDICT_RESPONSES,
    description=_ALTERNATIVES_DOC + " For products known by barcode (Open Food Facts).",
    dependencies=_VERDICT_DEPENDENCIES,
)
async def products_alternatives_by_barcode(
    code: str,
    current: Annotated[CurrentAccount, Depends(current_account_row)],
    session: Annotated[AsyncSession, Depends(get_session)],
    off: Annotated[OffClient, Depends(get_off_client)],
    settings: Annotated[Settings, Depends(get_app_settings)],
    member_id: Annotated[UUID | None, Query()] = None,
) -> AlternativesOut:
    return await _alternatives(session, off, settings, current.account.id, member_id, barcode=code)


def search_query(
    q: Annotated[
        str,
        Query(
            max_length=search.MAX_QUERY,
            description=(
                f"{search.MIN_QUERY} to {search.MAX_QUERY} characters after trimming and "
                "collapsing spaces; shorter is 422 search_query_too_short"
            ),
        ),
    ],
) -> str:
    """The search text, refused when shorter than MIN_QUERY once normalised (I4). Runs
    before limit(), so a too-short query costs no quota and touches no database."""
    if len(search.normalise_query(q)) < search.MIN_QUERY:
        raise ApiError(
            "search_query_too_short",
            422,
            details={"fields": ["query.q"], "min_length": search.MIN_QUERY},
        )
    return q


@router.get(
    "/search",
    operation_id="products_search",
    response_model=list[SearchHit],
    responses={
        **ERROR_RESPONSES,
        503: {
            "model": ErrorEnvelope,
            "description": (
                "off_unavailable: the Open Food Facts search budget is used up and nothing is "
                "cached for this query; retry after Retry-After seconds"
            ),
        },
    },
    # The query check first (no quota for a too-short query), then limit(), which commits.
    dependencies=[Depends(search_query), Depends(limit("search"))],
)
async def products_search(
    ctx: Annotated[AccountContext, Depends(current_account)],
    session: Annotated[AsyncSession, Depends(get_session)],
    off: Annotated[OffClient, Depends(get_off_client)],
    settings: Annotated[Settings, Depends(get_app_settings)],
    q: Annotated[str, Depends(search_query)],
    limit_: Annotated[int, Query(alias="limit", ge=1, le=50)] = 20,
) -> list[SearchHit]:
    """Our products first (name or brand), then Open Food Facts. ``q``: 3 to 80 characters.

    Open Food Facts search calls are capped for the whole server; over the cap a cached
    result is served, else 503 ``off_unavailable`` with Retry-After.
    """
    hits = await search.search_products(
        session, off, q, limit_, account_id=ctx.account_id, settings=settings
    )
    await session.commit()  # the OFF search cache write
    return hits


@router.get(
    "/compare",
    operation_id="products_compare",
    response_model=CompareOut,
    responses=_VERDICT_RESPONSES,
    dependencies=_VERDICT_DEPENDENCIES,
)
async def products_compare(
    current: Annotated[CurrentAccount, Depends(current_account_row)],
    session: Annotated[AsyncSession, Depends(get_session)],
    off: Annotated[OffClient, Depends(get_off_client)],
    settings: Annotated[Settings, Depends(get_app_settings)],
    a: Annotated[UUID | None, Query(description="Side a: our product id")] = None,
    a_barcode: Annotated[str | None, Query(max_length=64, description="Side a: barcode")] = None,
    b: Annotated[UUID | None, Query(description="Side b: our product id")] = None,
    b_barcode: Annotated[str | None, Query(max_length=64, description="Side b: barcode")] = None,
    member_id: Annotated[UUID | None, Query()] = None,
) -> CompareOut:
    """Two products side by side. Each side is exactly one of a product id or a barcode
    (``invalid_product_ref`` otherwise). ``member_status`` comes from the rules engine."""
    account_id = current.account.id
    for ref_id, ref_code in ((a, a_barcode), (b, b_barcode)):
        if (ref_id is None) == (ref_code is None):
            raise ApiError("invalid_product_ref", 422)
    member = (
        await members_service.get_member(session, account_id, member_id)
        if member_id is not None
        else None
    )
    sides = [
        await service.resolve_ref(
            session, off, product_id=pid, barcode=code, settings=settings, account_id=account_id
        )
        for pid, code in ((a, a_barcode), (b, b_barcode))
    ]
    await session.commit()  # OFF cache writes
    return compare.compare_products(sides[0], sides[1], member=member, today=today_ist())


@router.post(
    "",
    operation_id="products_create",
    response_model=ProductOut,
    status_code=201,
    responses={
        **ERROR_RESPONSES,
        409: {"model": ErrorEnvelope, "description": "A product with this barcode exists"},
        **CONSENT_RESPONSES,
    },
    # The consent gate first (a refused call costs no quota), then limit(), which commits.
    dependencies=[Depends(gate_for("products_create")), Depends(limit("product_creates"))],
)
async def products_create(
    body: ProductCreate,
    current: Annotated[CurrentAccount, Depends(current_account_row)],
    session: Annotated[AsyncSession, Depends(get_session)],
) -> ProductOut:
    """Save a confirmed label draft (``scan_id``) or a manual entry as a pending product.

    Then call ``analyze_create`` with the returned ``product_id``.
    """
    return await service.create_product(session, current.ctx.account_id, body)


@router.get(
    "/{barcode}/public",
    operation_id="products_get_public",
    response_model=PublicProductOut,
    responses=_RESPONSES,
    dependencies=[Depends(limit("public"))],  # first: it commits the session
)
async def products_get_public(
    barcode: str,
    response: Response,
    session: Annotated[AsyncSession, Depends(get_session)],
    off: Annotated[OffClient, Depends(get_off_client)],
    settings: Annotated[Settings, Depends(get_app_settings)],
    language: Annotated[Literal["en", "hi", "mr"], Query()] = "en",  # reserved; unused in M1
) -> PublicProductOut:
    found = await _find(session, off, barcode, settings, None)  # verified own products only
    response.headers["Cache-Control"] = "public, max-age=3600"
    return service.to_public_out(found)
