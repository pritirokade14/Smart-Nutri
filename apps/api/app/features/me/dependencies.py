"""Route dependencies owned by the `me` feature.

Every route that writes account-owned rows (members, consents, scans, meal_logs, ...) must
depend on `current_account_row`, not just `current_account`: those tables have a foreign key
to `accounts`, and a brand-new user may call them before ever calling `GET /v1/me`.
"""

from dataclasses import dataclass
from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import AccountContext, current_account
from app.db.session import get_session
from app.features.me import service
from app.features.me.models import Account


@dataclass(frozen=True, slots=True)
class CurrentAccount:
    """The verified token context plus the (now guaranteed) `accounts` row."""

    account: Account
    ctx: AccountContext


async def current_account_row(
    ctx: Annotated[AccountContext, Depends(current_account)],
    session: Annotated[AsyncSession, Depends(get_session)],
) -> CurrentAccount:
    """Verify the token, create the account row on first use, and return both.

    Uses the request's session (FastAPI caches `get_session` per request), so the route sees
    the same session.
    """
    account = await service.ensure_account(session, ctx)
    return CurrentAccount(account=account, ctx=ctx)
