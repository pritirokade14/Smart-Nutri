"""Family members. M1: the primary member and the mapping to the rules engine (M3 adds CRUD).

Member names and health fields never go to logs.
"""

from collections.abc import Sequence
from datetime import date
from uuid import UUID

from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app import scoring
from app.features.me import service as me_service
from app.features.members.models import Member


async def get_or_create_primary(session: AsyncSession, account_id: UUID) -> Member:
    """Return the account's primary member, creating it on first use (never commits).

    The account row must already exist (routes depend on ``current_account_row``). A
    transaction-scoped advisory lock keyed on the account serialises concurrent first calls,
    so an account never gets two primary members.
    """
    await session.execute(
        text("SELECT pg_advisory_xact_lock(hashtextextended(:key, 0))"),
        {"key": f"primary_member:{account_id}"},
    )
    query = (
        select(Member)
        .where(Member.account_id == account_id, Member.is_primary.is_(True))
        .order_by(Member.created_at, Member.id)
        .limit(1)
    )
    existing = await session.scalar(query)
    if existing is not None:
        return existing
    display_name = await me_service.get_display_name(session, account_id)
    member = Member(
        account_id=account_id,
        name=display_name or "",
        relation="self",
        is_primary=True,
        diet="non_veg",
        allergens=[],
        conditions=[],
        custom_alerts=[],
    )
    session.add(member)
    await session.flush()
    await session.refresh(member)
    return member


async def get_many(
    session: AsyncSession, account_id: UUID, member_ids: Sequence[UUID]
) -> list[Member] | None:
    """The account's members in ``member_ids`` order, or None if any id is unknown or foreign."""
    wanted = list(dict.fromkeys(member_ids))
    rows = await session.scalars(
        select(Member).where(Member.account_id == account_id, Member.id.in_(wanted))
    )
    by_id = {m.id: m for m in rows}
    if len(by_id) != len(wanted):
        return None
    return [by_id[i] for i in wanted]


def to_scoring_member(record: Member, *, today: date) -> scoring.Member:
    """Map a member row to the engine's Member.

    age = today.year - birth_year; None (unknown, so the engine stays protective) when there
    is no birth year or it lies in the future. ``custom_alerts`` is not mapped yet: the engine
    has no custom-alert rules until M3 (Plan 5 Task 1).
    """
    age = None
    if record.birth_year is not None and record.birth_year <= today.year:
        age = today.year - record.birth_year
    return scoring.Member(
        id=str(record.id),
        name=record.name,
        age=age,
        diet=scoring.Diet(record.diet),
        allergens=tuple(record.allergens or ()),
        conditions=tuple(record.conditions or ()),
        goal=record.goal,
    )
