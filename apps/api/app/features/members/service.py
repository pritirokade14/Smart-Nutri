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
    """The account's members in ``member_ids`` order, or None if any id is unknown or foreign.

    Duplicate ids are rejected at the API boundary (AnalyzeRequest); they are collapsed here.
    """
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

    Age is the YOUNGEST age the birth year allows: max(0, today.year - birth_year - 1). With
    only a birth year, the birthday may still be ahead this year, and the engine's younger age
    bands (infant, child) are stricter, so assuming the older age could turn an `avoid` into
    `ok` (e.g. born two years ago may still be 1, an infant). Age is None (unknown, so the
    engine stays protective) when there is no birth year or it lies in the future.
    ``custom_alerts`` is not mapped yet: the engine has no custom-alert rules until M3
    (Plan 5 Task 1).
    """
    age = None
    if record.birth_year is not None and record.birth_year <= today.year:
        age = max(0, today.year - record.birth_year - 1)
    return scoring.Member(
        id=str(record.id),
        name=record.name,
        age=age,
        diet=scoring.Diet(record.diet),
        allergens=tuple(record.allergens or ()),
        conditions=tuple(record.conditions or ()),
        goal=record.goal,
    )
