"""Weigh-in storage (Plan 12 Task 21). No import of `diary`, `targets` or `weights.service`,
so members and targets can use it without a cycle. Never commits."""

from datetime import date, datetime
from decimal import Decimal
from uuid import UUID

from sqlalchemy import delete, func, select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.features.members.models import Member
from app.features.weights.models import WeightLog


def _own(member: Member) -> tuple:
    return (WeightLog.member_id == member.id, WeightLog.account_id == member.account_id)


async def upsert_weigh_in(
    session: AsyncSession,
    member: Member,
    day: date,
    weight_kg: Decimal,
    measured_at: datetime,
    client_id: UUID | None = None,
) -> WeightLog:
    """One row per member and day: a second write for the day replaces the first."""
    values = {"weight_kg": weight_kg, "measured_at": measured_at, "client_id": client_id}
    stmt = insert(WeightLog).values(
        member_id=member.id, account_id=member.account_id, local_date=day, **values
    )
    await session.execute(
        stmt.on_conflict_do_update(
            constraint="uq_weight_logs_member_id_local_date",
            # A replace without a client_id keeps the stored one, so a late offline retry of
            # the first put still finds its row instead of re-saving a stale value.
            set_={
                "weight_kg": weight_kg,
                "measured_at": measured_at,
                "client_id": func.coalesce(stmt.excluded.client_id, WeightLog.client_id),
                "updated_at": func.now(),
            },
        )
    )
    await session.flush()
    row = await session.scalar(
        select(WeightLog)
        .where(*_own(member), WeightLog.local_date == day)
        .execution_options(populate_existing=True)
    )
    assert row is not None
    return row


async def list_weigh_ins(
    session: AsyncSession,
    member: Member,
    *,
    until: date | None = None,
    since: date | None = None,
) -> list[WeightLog]:
    """Oldest first; both bounds inclusive."""
    query = select(WeightLog).where(*_own(member)).order_by(WeightLog.local_date)
    if since is not None:
        query = query.where(WeightLog.local_date >= since)
    if until is not None:
        query = query.where(WeightLog.local_date <= until)
    return list(await session.scalars(query.execution_options(populate_existing=True)))


async def get_weigh_in(session: AsyncSession, member: Member, day: date) -> WeightLog | None:
    return await session.scalar(
        select(WeightLog)
        .where(*_own(member), WeightLog.local_date == day)
        .execution_options(populate_existing=True)
    )


async def delete_weigh_in(session: AsyncSession, member: Member, day: date) -> WeightLog | None:
    """Delete the day's row and return it (None if there was none)."""
    row = await get_weigh_in(session, member, day)
    if row is None:
        return None
    await session.execute(delete(WeightLog).where(WeightLog.id == row.id))
    await session.flush()
    session.expunge(row)
    return row


async def delete_all(session: AsyncSession, member: Member) -> int:
    """Delete every weigh-in of the member and return how many went."""
    result = await session.execute(delete(WeightLog).where(*_own(member)))
    await session.flush()
    return result.rowcount or 0


async def latest(session: AsyncSession, member: Member) -> WeightLog | None:
    return await session.scalar(
        select(WeightLog)
        .where(*_own(member))
        .order_by(WeightLog.local_date.desc())
        .limit(1)
        .execution_options(populate_existing=True)
    )
