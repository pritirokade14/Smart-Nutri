from typing import Annotated, Literal

from fastapi import APIRouter, Depends, Query, Response
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings, get_app_settings
from app.core.errors import ERROR_RESPONSES, ApiError, ErrorEnvelope
from app.core.ratelimit import limit
from app.core.security import AccountContext, current_account
from app.db.session import get_session
from app.features.products import service
from app.features.products.schemas import NutrientsOut, ProductOut, PublicProductOut
from app.integrations.openfoodfacts import (
    InvalidBarcode,
    OffClient,
    OffUnavailable,
    get_off_client,
)
from app.scoring import analyze

router = APIRouter(prefix="/v1/products", tags=["products"])

_RESPONSES = {
    **ERROR_RESPONSES,
    503: {"model": ErrorEnvelope, "description": "Open Food Facts unavailable"},
}


def _to_out(found: service.ProductLookup) -> ProductOut:
    p = found.product
    n = p.per_100g
    return ProductOut(
        source=found.source,
        product_id=found.product_id,
        barcode=found.info.barcode or None,
        name=found.info.name,
        brand=found.info.brand,
        image_url=found.info.image_url,
        category=p.category.value,
        per_100g=NutrientsOut(
            energy_kcal=n.energy_kcal,
            protein_g=n.protein_g,
            carbs_g=n.carbs_g,
            sugars_g=n.sugars_g,
            fat_g=n.fat_g,
            sat_fat_g=n.sat_fat_g,
            fiber_g=n.fiber_g,
            salt_g=n.salt_g,
            sodium_mg=n.sodium_mg,
        ),
        serving_size_g=p.serving_size_g,
        ingredients=list(p.ingredients),
        claims=list(p.claims),
        attribution=found.attribution,
    )


async def _find(
    session: AsyncSession, off: OffClient, barcode: str, settings: Settings
) -> service.ProductLookup:
    try:
        found = await service.lookup_by_barcode(session, off, barcode, settings=settings)
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
    _: Annotated[AccountContext, Depends(current_account)],
    session: Annotated[AsyncSession, Depends(get_session)],
    off: Annotated[OffClient, Depends(get_off_client)],
    settings: Annotated[Settings, Depends(get_app_settings)],
) -> ProductOut:
    return _to_out(await _find(session, off, code, settings))


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
    found = await _find(session, off, barcode, settings)
    report = analyze(found.product, []).to_dict()["report"]
    response.headers["Cache-Control"] = "public, max-age=3600"
    return PublicProductOut(
        product=_to_out(found), report=report, score_label="calculated_by_smartnutri"
    )
