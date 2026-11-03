from typing import Annotated, Literal
from uuid import UUID

from fastapi import APIRouter, Depends, Query, Response
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings, get_app_settings
from app.core.errors import ERROR_RESPONSES, ApiError, ErrorEnvelope
from app.core.ratelimit import limit
from app.core.security import AccountContext, current_account
from app.db.session import get_session
from app.features.me.dependencies import CurrentAccount, current_account_row
from app.features.products import service
from app.features.products.schemas import ProductCreate, ProductOut, PublicProductOut
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


@router.post(
    "",
    operation_id="products_create",
    response_model=ProductOut,
    status_code=201,
    responses={
        **ERROR_RESPONSES,
        409: {"model": ErrorEnvelope, "description": "A product with this barcode exists"},
    },
    dependencies=[Depends(limit("product_creates"))],  # first: it commits the session
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
