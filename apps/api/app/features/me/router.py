import logging
from typing import Annotated

from fastapi import APIRouter, Depends, Response
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import ERROR_RESPONSES, ApiError, ErrorEnvelope
from app.core.ratelimit import limit
from app.core.security import AccountContext, current_account
from app.db.session import get_session
from app.features.me import service
from app.features.me.dependencies import CurrentAccount, current_account_row
from app.features.me.schemas import ActiveTypeIn, MeOut, UserTypesIn, UserTypesOut
from app.integrations.posthog import track
from app.integrations.storage import (
    StorageClient,
    StorageUnavailable,
    get_storage,
    get_voice_storage,
)
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


# --- user types (Plan 9 Task 1). No analytics event and no log of the types (P9-R8). ------

Current = Annotated[CurrentAccount, Depends(current_account_row)]
Session = Annotated[AsyncSession, Depends(get_session)]

_USER_TYPES_PUT_RESPONSES = {
    **ERROR_RESPONSES,
    403: {
        "model": ErrorEnvelope,
        "description": (
            "consent_required (details.purposes = ['health_data']): a health-revealing type "
            "(health_condition, weight_loss, allergy_diet) or a health follow-up (conditions, "
            "allergens, diet) needs the health_data consent. Nothing is saved."
        ),
    },
}


@router.get("/user-types", operation_id="me_user_types_get", response_model=UserTypesOut)
async def me_user_types_get(current: Current, session: Session) -> UserTypesOut:
    """The account's user types. Without an answer yet: `answered=false`, `types=[]` and the
    `eat_better` mode (clients then show the picker)."""
    row = await service.get_user_types(session, current.account.id)
    return service.user_types_out(row)


@router.put(
    "/user-types",
    operation_id="me_user_types_put",
    response_model=UserTypesOut,
    responses=_USER_TYPES_PUT_RESPONSES,
)
async def me_user_types_put(body: UserTypesIn, current: Current, session: Session) -> UserTypesOut:
    """Save up to 3 types (tap order) and their follow-ups; `types=[]` is "Skip for now".

    Presentation only: it never changes a member or a verdict. 422 `validation_error` for more
    than 3 types or duplicates; 422 `follow_up_without_type` for a follow-up whose type is not
    chosen.
    """
    row = await service.put_user_types(session, current.account.id, body)
    out = service.user_types_out(row)
    await session.commit()
    return out


@router.patch(
    "/user-types/active",
    operation_id="me_user_types_set_active",
    response_model=UserTypesOut,
)
async def me_user_types_set_active(
    body: ActiveTypeIn, current: Current, session: Session
) -> UserTypesOut:
    """Switch the focused mode. Needs no consent. 404 `user_types_not_found` before the first
    PUT; 422 `user_type_not_selected` unless it is one of the chosen types (or `eat_better`
    after "Skip for now")."""
    row = await service.set_active_type(session, current.account.id, body.active_type)
    out = service.user_types_out(row)
    await session.commit()
    return out


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
    # First: it commits the session. allow_deleted: a retry after a 503 must get through.
    dependencies=[Depends(limit("account_deletes", allow_deleted=True))],
)
async def me_delete(
    ctx: Annotated[AccountContext, Depends(current_account)],
    session: Annotated[AsyncSession, Depends(get_session)],
    storage: Annotated[StorageClient, Depends(get_storage)],
    voice_storage: Annotated[StorageClient, Depends(get_voice_storage)],
    admin: Annotated[SupabaseAdmin, Depends(get_supabase_admin)],
) -> Response:
    """Permanently erase the caller's account (DPDP erasure, F11).

    Order: storage objects (label photos, and voice answers in their own bucket), then every
    account-owned row in one transaction (contributed products stay with no owner), then the
    Supabase auth user. The row erasure also writes a tombstone (ruling D1/B1): until it is
    purged (7 days), the caller's still-valid token gets 401 `auth_invalid` everywhere else.
    Idempotent: calling it again returns 204 (at most 5 calls a day, then 429). On 503
    `deletion_incomplete`, retry: completed steps are skipped. Depends on `current_account`
    (not `current_account_row`) so a repeat call never re-creates the account row.
    """
    account_id = ctx.account_id
    try:
        paths = await service.account_storage_paths(session, storage, account_id)
        voice_paths = await service.account_voice_paths(voice_storage, account_id)
        await session.commit()  # release the DB connection before the storage calls
        await storage.delete_paths(paths)
        await voice_storage.delete_paths(voice_paths)
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
    # m2: only now may the retention job purge the tombstone (it retries the removal if this
    # request never gets here).
    await service.mark_auth_deleted(session, [account_id])
    await session.commit()
    logger.info("account_delete status=done objects=%d", len(paths) + len(voice_paths))
    track(account_id, "account_deleted")  # hashed id, no properties
    return Response(status_code=204)
