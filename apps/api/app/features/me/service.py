import logging
from collections.abc import Sequence
from uuid import UUID

from sqlalchemy import any_, case, func, select, text, update
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import ApiError
from app.core.security import AccountContext, auth_invalid_error
from app.core.time import today_ist
from app.features.consents import service as consents_service
from app.features.me import prefill
from app.features.me.models import Account, AccountUserTypes, DeletedAccount
from app.features.me.schemas import (
    DEFAULT_TYPE,
    FOLLOW_UP_TYPE,
    HEALTH_FOLLOW_UPS,
    HEALTH_REVEALING_TYPES,
    USER_TYPE_PRIORITY,
    FollowUps,
    PrefillSuggestion,
    UserType,
    UserTypesIn,
    UserTypesOut,
)
from app.features.members import service as members_service
from app.features.members.schemas import HEALTH_FIELDS
from app.integrations.storage import StorageClient

logger = logging.getLogger(__name__)


def _default_display_name(email: str | None) -> str | None:
    if not email:
        return None
    local = email.split("@", 1)[0].strip()
    return local or None


async def _lock_account_id(session: AsyncSession, account_id: UUID) -> None:
    """Serialise account creation and erasure for one id until the transaction ends.

    Without it, a request racing `DELETE /v1/me` could pass the tombstone check before the
    erasure commits and then re-insert the account row right after it.
    """
    await session.execute(
        text("select pg_advisory_xact_lock(hashtextextended('account:' || :a, 0))"),
        {"a": str(account_id)},
    )


async def is_deleted(session: AsyncSession, account_id: UUID) -> bool:
    """True if this account id was erased and its tombstone has not been purged yet."""
    found = await session.scalar(select(DeletedAccount.id).where(DeletedAccount.id == account_id))
    return found is not None


async def ensure_account(session: AsyncSession, ctx: AccountContext) -> Account:
    """Create the account row on first login (idempotent), then return it.

    Raises 401 `auth_invalid` for an erased account (ruling D1/B1): its access token may
    still be valid, but it must never bring the account back.
    """
    await _lock_account_id(session, ctx.account_id)
    if await is_deleted(session, ctx.account_id):
        raise auth_invalid_error()  # the lock goes when the request's session closes
    await session.execute(
        insert(Account)
        .values(id=ctx.account_id, display_name=_default_display_name(ctx.email))
        .on_conflict_do_nothing(index_elements=[Account.id])
    )
    await session.commit()
    result = await session.execute(select(Account).where(Account.id == ctx.account_id))
    return result.scalar_one()


async def get_display_name(session: AsyncSession, account_id: UUID) -> str | None:
    return await session.scalar(select(Account.display_name).where(Account.id == account_id))


# --- account deletion (Plan 8 Task 2, F11) -------------------------------------------------

# Tables with an `account_id` column, erased in this order (children before parents). A new
# account-owned table must be added here; tests/api/test_delete_me.py fails until it is.
# Checked at the wave 2 merge: Plans 6 and 7 add no new tables (Plan 6's migration 0003 only
# alters meal_logs; Plan 7 reports use product_reports; voice stores no rows).
ACCOUNT_OWNED_TABLES: tuple[str, ...] = (
    "meal_logs",
    "members",
    "scans",
    "product_reports",
    "account_user_types",  # Plan 9 (P9-R1)
    "consents",
)

# Storage folders that hold an account's objects. Label photos are in the label-photo bucket
# (`<account_id>/<uuid>.<ext>`, Plan 4); voice answers are in their own private bucket
# (`settings.supabase_voice_bucket`, `voice/<account_id>/<uuid>.mp3`, Plan 7).
STORAGE_PREFIXES: tuple[str, ...] = ("{account_id}",)
VOICE_STORAGE_PREFIXES: tuple[str, ...] = ("voice/{account_id}",)


async def account_voice_paths(voice_storage: StorageClient, account_id: UUID) -> list[str]:
    """Every voice answer of the account in the voice-answers bucket."""
    paths: set[str] = set()
    for prefix in VOICE_STORAGE_PREFIXES:
        paths.update(await voice_storage.list_prefix(prefix.format(account_id=account_id)))
    return sorted(paths)


async def account_storage_paths(
    session: AsyncSession, storage: StorageClient, account_id: UUID
) -> list[str]:
    """Every stored object of the account: the listed folders plus any scan image path."""
    paths: set[str] = set()
    for prefix in STORAGE_PREFIXES:
        paths.update(await storage.list_prefix(prefix.format(account_id=account_id)))
    rows = await session.scalars(
        text("select image_path from scans where account_id = :a and image_path is not null"),
        {"a": account_id},
    )
    paths.update(rows)
    return sorted(paths)


# Kept after an erasure, so the DELETE /v1/me limit still holds for the rest of the day. It
# goes with the tombstone (app/jobs/retention.py).
ACCOUNT_DELETES_BUCKET = "account_deletes"


async def erase_account_rows(session: AsyncSession, account_id: UUID) -> None:
    """Delete every account-owned row and write the tombstone, in one transaction (the
    caller commits).

    Contributed products stay, without an owner. Rate-limit counters keyed by the account go
    too, except the `account_deletes` one. The tombstone (ruling D1/B1) is written (or its
    time refreshed) in the same transaction, so there is never an erased account without
    one. Idempotent: a second run deletes nothing.
    """
    await _lock_account_id(session, account_id)
    params = {"a": account_id}
    for table in ACCOUNT_OWNED_TABLES:  # fixed literals, never user input
        await session.execute(text(f"delete from {table} where account_id = :a"), params)
    await session.execute(
        text("update products set created_by = null where created_by = :a"), params
    )
    await session.execute(
        text("delete from rate_limit_counters where key = :k and bucket <> :keep"),
        {"k": f"acct:{account_id}", "keep": ACCOUNT_DELETES_BUCKET},
    )
    await session.execute(text("delete from accounts where id = :a"), params)
    # A retry restarts the 7-day window: until the auth user is removed, the sign-in could
    # still mint new access tokens.
    await session.execute(
        insert(DeletedAccount)
        .values(id=account_id)
        .on_conflict_do_update(index_elements=[DeletedAccount.id], set_={"deleted_at": func.now()})
    )


async def mark_auth_deleted(session: AsyncSession, account_ids: Sequence[UUID]) -> None:
    """Record on the tombstones that these accounts' Supabase auth users are gone (m2). Only
    then may the retention job purge them. The caller commits."""
    if not account_ids:
        return
    await session.execute(
        update(DeletedAccount)
        .where(DeletedAccount.id.in_(list(account_ids)))
        .values(auth_deleted_at=func.now())
    )


# --- user types (Plan 9 Task 1, rulings P9-R1..R4, P9-R8) ------------------------------------
#
# Presentation only: nothing here reads or writes a member, and nothing is sent to analytics.
# Logs carry the count only, never the types or the follow-ups.


def resolve_active_type(types: Sequence[str], stored: str | None) -> UserType:
    """The stored mode if it is still selected, else the chosen type with the highest
    safety-first priority (P9-R4), else `eat_better` (P9-R3)."""
    if stored is not None and stored in types:
        return stored  # type: ignore[return-value]
    for candidate in USER_TYPE_PRIORITY:
        if candidate in types:
            return candidate
    return DEFAULT_TYPE


def user_types_out(
    row: AccountUserTypes | None, prefill: PrefillSuggestion | None = None
) -> UserTypesOut:
    if row is None:
        return UserTypesOut(
            types=[],
            follow_ups=FollowUps(),
            active_type=DEFAULT_TYPE,
            answered=False,
            answered_at=None,
            prefill=None,
        )
    return UserTypesOut(
        types=list(row.types),  # type: ignore[arg-type]
        follow_ups=FollowUps.model_validate(row.follow_ups or {}),
        active_type=resolve_active_type(row.types, row.active_type),
        answered=True,
        answered_at=row.answered_at,
        prefill=prefill,
    )


async def get_user_types(session: AsyncSession, account_id: UUID) -> AccountUserTypes | None:
    """The account's row, or None if the user has not answered yet. Read-only."""
    return await session.scalar(
        select(AccountUserTypes)
        .where(AccountUserTypes.account_id == account_id)
        .execution_options(populate_existing=True)
    )


async def build_prefill(
    session: AsyncSession, account_id: UUID, row: AccountUserTypes | None
) -> PrefillSuggestion | None:
    """Pre-fill suggestions for the primary member (Task 2, P9-R9), or None before the first
    answer. Recomputed from the member every time, so it is empty once the user has
    confirmed. Writes nothing to the member (it may create the primary row on first use,
    like `GET /v1/members`; the caller commits)."""
    if row is None:
        return None
    primary = await members_service.get_or_create_primary(session, account_id)
    snapshot = prefill.MemberSnapshot(
        conditions=tuple(primary.conditions or ()),
        allergens=tuple(primary.allergens or ()),
        diet=primary.diet,
        goal=primary.goal,
        custom_alerts=tuple(primary.custom_alerts or ()),
        age=members_service.youngest_age(primary.birth_year, today_ist()),
    )
    follow_ups = FollowUps.model_validate(row.follow_ups or {})
    changes, goal_choice = prefill.suggest_prefill(row.types, follow_ups, snapshot)  # type: ignore[arg-type]
    touches_health = goal_choice is not None or any(c.field in HEALTH_FIELDS for c in changes)
    needs_consent = touches_health and not await consents_service.has_active_consent(
        session, account_id, "health_data"
    )
    return PrefillSuggestion(
        member_id=primary.id,
        changes=changes,
        goal_choice=goal_choice,
        needs_health_consent=needs_consent,
    )


def _needs_health_consent(body: UserTypesIn) -> bool:
    return any(t in HEALTH_REVEALING_TYPES for t in body.types) or any(
        f in HEALTH_FOLLOW_UPS for f in body.follow_ups.given()
    )


async def put_user_types(
    session: AsyncSession, account_id: UUID, body: UserTypesIn
) -> AccountUserTypes:
    """Save the types and follow-ups (an upsert; never commits). Nothing is written on error.

    - 403 `consent_required` (`details.purposes = ["health_data"]`) for a health-revealing
      type or a health follow-up without an active `health_data` consent.
    - 422 `follow_up_without_type` for a follow-up whose type is not chosen.

    `active_type` is kept only while it is still one of the new types; otherwise it becomes
    null and is resolved on read. Member data is never touched (removing a type clears
    nothing).
    """
    if _needs_health_consent(body) and not await consents_service.has_active_consent(
        session, account_id, "health_data"
    ):
        raise ApiError("consent_required", 403, details={"purposes": ["health_data"]})
    if any(FOLLOW_UP_TYPE[f] not in body.types for f in body.follow_ups.given()):
        raise ApiError("follow_up_without_type", 422)

    types = list(body.types)
    follow_ups = body.follow_ups.model_dump(mode="json", exclude_none=True)
    stmt = insert(AccountUserTypes).values(
        account_id=account_id, types=types, follow_ups=follow_ups
    )
    stmt = stmt.on_conflict_do_update(
        index_elements=[AccountUserTypes.account_id],
        set_={
            "types": stmt.excluded.types,
            "follow_ups": stmt.excluded.follow_ups,
            "active_type": case(
                (
                    AccountUserTypes.active_type == any_(stmt.excluded.types),
                    AccountUserTypes.active_type,
                ),
                else_=None,
            ),
            "updated_at": func.now(),
        },
    ).returning(AccountUserTypes)
    row = await session.scalar(stmt, execution_options={"populate_existing": True})
    await session.flush()
    logger.info("user_types status=saved count=%d", len(types))
    return row  # type: ignore[return-value]


async def set_active_type(
    session: AsyncSession, account_id: UUID, active_type: UserType
) -> AccountUserTypes:
    """Switch the focused mode (never commits). Needs no consent: it reveals nothing new, and
    after a withdrawal the stored types still drive the layout (ADR 0018).

    404 `user_types_not_found` without a row; 422 `user_type_not_selected` unless the mode is
    one of the stored types (or `eat_better` when the user skipped).
    """
    row = await session.scalar(
        select(AccountUserTypes)
        .where(AccountUserTypes.account_id == account_id)
        .with_for_update()
        .execution_options(populate_existing=True)
    )
    if row is None:
        raise ApiError("user_types_not_found", 404)
    if active_type in row.types:
        row.active_type = active_type
    elif not row.types and active_type == DEFAULT_TYPE:
        row.active_type = None  # the check constraint needs one of `types`; null resolves here
    else:
        raise ApiError("user_type_not_selected", 422)
    row.updated_at = func.now()
    await session.flush()
    await session.refresh(row)
    return row
