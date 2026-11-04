from collections.abc import Iterable
from uuid import UUID

import pytest
from sqlalchemy import func, select

from app.core.security import AccountContext, current_account
from app.db.session import get_session
from app.features.consents.models import Consent
from app.features.consents.policy import CURRENT_VERSIONS
from app.features.me.service import ensure_account
from app.features.members.models import Member

ACC_A = UUID("11111111-1111-1111-1111-111111111111")
ACC_B = UUID("22222222-2222-2222-2222-222222222222")
ACC_C = UUID("33333333-3333-3333-3333-333333333333")
ALL_PURPOSES = ("terms", "health_data", "ai_processing")


@pytest.fixture
def login(app, db_session):
    """Make the API act as `account_id` on the shared, rolled-back test session."""

    def _login(account_id: UUID = ACC_A) -> None:
        app.dependency_overrides[get_session] = lambda: db_session
        app.dependency_overrides[current_account] = lambda: AccountContext(
            account_id, "asha@example.com"
        )

    return _login


@pytest.fixture
def grant(db_session):
    """Record active consents at the given version (default: current) for an account."""

    async def _grant(
        account_id: UUID, purposes: Iterable[str] = ALL_PURPOSES, version: str | None = None
    ) -> None:
        await ensure_account(db_session, AccountContext(account_id, None))
        for purpose in purposes:
            db_session.add(
                Consent(
                    account_id=account_id,
                    purpose=purpose,
                    version=version or CURRENT_VERSIONS[purpose],
                )
            )
        await db_session.flush()

    return _grant


@pytest.fixture
async def consented(login, grant):
    """ACC_A, logged in, with all three consents granted at the current version."""
    await grant(ACC_A)
    login(ACC_A)
    return ACC_A


@pytest.fixture
def count_members(db_session):
    async def _count(account_id: UUID) -> int:
        return await db_session.scalar(
            select(func.count()).select_from(Member).where(Member.account_id == account_id)
        )

    return _count


@pytest.fixture
def add_member(db_session):
    """Insert a member row directly (bypasses the API and its consent gate)."""

    async def _add(account_id: UUID, **fields) -> Member:
        await ensure_account(db_session, AccountContext(account_id, None))
        values = {"name": "Ravi", "relation": "parent", "birth_year": 1966, "diet": "veg"}
        values.update(fields)
        member = Member(account_id=account_id, **values)
        db_session.add(member)
        await db_session.flush()
        await db_session.refresh(member)
        return member

    return _add


@pytest.fixture
async def other_account_member_id(add_member) -> UUID:
    """A non-primary member owned by ACC_C."""
    member = await add_member(ACC_C, name="Other", allergens=["milk"], conditions=["diabetes"])
    return member.id
