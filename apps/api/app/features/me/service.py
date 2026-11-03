from uuid import UUID

from sqlalchemy import select, text
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import AccountContext
from app.features.me.models import Account
from app.integrations.storage import StorageClient


def _default_display_name(email: str | None) -> str | None:
    if not email:
        return None
    local = email.split("@", 1)[0].strip()
    return local or None


async def ensure_account(session: AsyncSession, ctx: AccountContext) -> Account:
    """Create the account row on first login (idempotent), then return it."""
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


async def erase_account_rows(session: AsyncSession, account_id: UUID) -> None:
    """Delete every account-owned row in one transaction (the caller commits).

    Contributed products stay, without an owner. Rate-limit counters keyed by the account go
    too. Idempotent: a second run deletes nothing.
    """
    params = {"a": account_id}
    for table in ACCOUNT_OWNED_TABLES:  # fixed literals, never user input
        await session.execute(text(f"delete from {table} where account_id = :a"), params)
    await session.execute(
        text("update products set created_by = null where created_by = :a"), params
    )
    await session.execute(
        text("delete from rate_limit_counters where key = :k"), {"k": f"acct:{account_id}"}
    )
    await session.execute(text("delete from accounts where id = :a"), params)
