from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import AccountContext
from app.features.me.models import Account


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
