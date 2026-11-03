import logging
from typing import Annotated

from fastapi import APIRouter, Depends, Response
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import ERROR_RESPONSES, ApiError, ErrorEnvelope
from app.core.security import AccountContext, current_account
from app.db.session import get_session
from app.features.me import service
from app.features.me.dependencies import CurrentAccount, current_account_row
from app.features.me.schemas import MeOut
from app.integrations.posthog import track
from app.integrations.storage import StorageClient, StorageUnavailable, get_storage
from app.integrations.supabase_admin import AdminUnavailable, SupabaseAdmin, get_supabase_admin

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/v1/me", tags=["me"])


@router.get("", operation_id="me_get", response_model=MeOut)
async def me_get(current: Annotated[CurrentAccount, Depends(current_account_row)]) -> MeOut:
    account = current.account
    return MeOut(
        id=account.id,
        email=current.ctx.email,
        display_name=account.display_name,
        language=account.language,  # type: ignore[arg-type]
        created_at=account.created_at,
    )


@router.delete(
    "",
    operation_id="me_delete",
    status_code=204,
    response_class=Response,
    responses={
        **ERROR_RESPONSES,
        204: {"description": "Account erased (also when it was already gone)"},
        503: {
            "model": ErrorEnvelope,
            "description": "deletion_incomplete: storage or sign-in removal failed; retry",
        },
    },
)
async def me_delete(
    ctx: Annotated[AccountContext, Depends(current_account)],
    session: Annotated[AsyncSession, Depends(get_session)],
    storage: Annotated[StorageClient, Depends(get_storage)],
    admin: Annotated[SupabaseAdmin, Depends(get_supabase_admin)],
) -> Response:
    """Permanently erase the caller's account (DPDP erasure, F11).

    Order: storage objects (label photos, voice answers), then every account-owned row in one
    transaction (contributed products stay with no owner), then the Supabase auth user.
    Idempotent: calling it again returns 204. On 503 `deletion_incomplete`, retry: completed
    steps are skipped. Depends on `current_account` (not `current_account_row`) so a repeat
    call never re-creates the account row.
    """
    account_id = ctx.account_id
    try:
        paths = await service.account_storage_paths(session, storage, account_id)
        await session.commit()  # release the DB connection before the storage call
        await storage.delete_paths(paths)
    except StorageUnavailable:
        logger.warning("account_delete step=storage status=unavailable")
        raise ApiError("deletion_incomplete", 503) from None

    await service.erase_account_rows(session, account_id)
    await session.commit()

    try:
        await admin.delete_user(account_id)
    except AdminUnavailable:
        logger.warning("account_delete step=auth status=unavailable")
        raise ApiError("deletion_incomplete", 503) from None
    logger.info("account_delete status=done objects=%d", len(paths))
    track(account_id, "account_deleted")  # hashed id, no properties
    return Response(status_code=204)
