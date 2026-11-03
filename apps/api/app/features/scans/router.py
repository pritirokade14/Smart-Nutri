from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings, get_app_settings
from app.core.errors import ERROR_RESPONSES, ApiError, ErrorEnvelope
from app.core.ratelimit import limit
from app.db.session import get_session
from app.features.me.dependencies import CurrentAccount, current_account_row
from app.features.scans import service
from app.features.scans.api_schemas import (
    UPLOAD_URL_EXPIRES_IN_S,
    LabelScanIn,
    ScanDraftOut,
    UploadUrlIn,
    UploadUrlOut,
)
from app.integrations.callmissed import get_llm_provider
from app.integrations.providers import LLMProvider
from app.integrations.storage import StorageClient, StorageUnavailable, get_storage

router = APIRouter(prefix="/v1/scans", tags=["scans"])

_STORAGE_503 = {503: {"model": ErrorEnvelope, "description": "Storage unavailable"}}
_LABEL_RESPONSES = {
    **ERROR_RESPONSES,
    422: {
        "model": ErrorEnvelope,
        "description": (
            "Validation error, or `image_quality_low`: the photo is clearly unreadable and no "
            "extraction was attempted (not counted toward the scan limit). "
            "`details.reasons` lists `blur`, `glare` and/or `too_small`; show "
            "`image_quality.<reason>` and ask for a retake."
        ),
    },
    413: {"model": ErrorEnvelope, "description": "Image larger than 8 MB"},
    415: {"model": ErrorEnvelope, "description": "Not a JPEG, PNG or WebP image"},
    502: {"model": ErrorEnvelope, "description": "Extraction failed (no draft)"},
    503: {"model": ErrorEnvelope, "description": "Extraction or storage unavailable"},
}


@router.post(
    "/upload-url",
    operation_id="scans_create_upload_url",
    response_model=UploadUrlOut,
    responses={**ERROR_RESPONSES, **_STORAGE_503},
    dependencies=[Depends(limit("scan_uploads"))],  # first: it commits the session
)
async def scans_create_upload_url(
    body: UploadUrlIn,
    current: Annotated[CurrentAccount, Depends(current_account_row)],
    session: Annotated[AsyncSession, Depends(get_session)],
    storage: Annotated[StorageClient, Depends(get_storage)],
) -> UploadUrlOut:
    """A signed URL to PUT one label photo into the caller's private folder.

    Creates the caller's account row on first use (the photo is account-owned).
    """
    await session.commit()  # release the DB connection before the storage call
    path = service.new_upload_path(current.ctx.account_id, body.ext)
    try:
        url = await storage.create_signed_upload(path, UPLOAD_URL_EXPIRES_IN_S)
    except StorageUnavailable:
        raise ApiError("storage_unavailable", 503) from None
    return UploadUrlOut(upload_url=url, path=path, expires_in=UPLOAD_URL_EXPIRES_IN_S)


@router.post(
    "/label",
    operation_id="scans_create_label",
    response_model=ScanDraftOut,
    responses=_LABEL_RESPONSES,
    dependencies=[Depends(limit("label_requests"))],  # first: it commits the session
)
async def scans_create_label(
    body: LabelScanIn,
    current: Annotated[CurrentAccount, Depends(current_account_row)],
    session: Annotated[AsyncSession, Depends(get_session)],
    storage: Annotated[StorageClient, Depends(get_storage)],
    llm: Annotated[LLMProvider, Depends(get_llm_provider)],
    settings: Annotated[Settings, Depends(get_app_settings)],
) -> ScanDraftOut:
    """Extract an unconfirmed draft from an uploaded label photo.

    Rate-limited per account (`rate_limited_scans`), counting only paid extractions: the
    same image bytes again (from any account) reuse the stored extraction for free (it is
    normalised afresh), and the same `path` posted again returns the same `scan_id`.
    """
    return await service.create_label_scan(
        session,
        storage=storage,
        llm=llm,
        settings=settings,
        account_id=current.ctx.account_id,
        body=body,
    )
