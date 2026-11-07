"""Frozen daily targets (Plan 11 Task 3; Ruling E5; ADR 0023). No FastAPI imports.

Today's `diary_days` row is recomputed and upserted on every read or log of today, so settings,
weight, birth-year and time-zone changes reach it without hooks. A past row is never recomputed
(only `partial_logged` changes). A past day with no row is `none` and is never back-filled.
A row is computed only while `health_data` is active: the caller checks that.
Targets are information, never verdicts: nothing here touches `analyze`.
"""

from datetime import date
from typing import Literal

from sqlalchemy import func, select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import ApiError
from app.features.consents import service as consents_service
from app.features.diary import frozen
from app.features.diary.models import DiaryDay
from app.features.members.models import Member
from app.features.targets import service as targets_service
from app.scoring import targets as engine
from app.scoring.config import ScoringConfig

DayTargetsStatus = Literal[
    "ready", "needs_body_data", "not_available_minor", "paused_pregnancy", "none"
]

_FROZEN_COLUMNS = (
    "status",
    "energy_kcal",
    "protein_g",
    "fat_g",
    "carbs_g",
    "basis",
    "direction",
    "rate_pct_bw_per_week",
    "inputs",
    "flags",
)


async def _row(session: AsyncSession, member: Member, day: date) -> DiaryDay | None:
    return await session.scalar(
        select(DiaryDay)
        .where(
            DiaryDay.member_id == member.id,
            DiaryDay.account_id == member.account_id,
            DiaryDay.local_date == day,
        )
        .execution_options(populate_existing=True)
    )


async def _upsert_frozen(session: AsyncSession, member: Member, day: date, values: dict) -> None:
    stmt = insert(DiaryDay).values(
        member_id=member.id, local_date=day, account_id=member.account_id, **values
    )
    await session.execute(
        stmt.on_conflict_do_update(
            index_elements=[DiaryDay.member_id, DiaryDay.local_date],
            set_={**{k: stmt.excluded[k] for k in _FROZEN_COLUMNS}, "computed_at": func.now()},
        )
    )
    await session.flush()


async def day_targets(
    session: AsyncSession,
    member: Member,
    day: date,
    *,
    today: date,
    cfg: ScoringConfig | None = None,
) -> engine.TargetResult | None:
    """The member's targets for ``day`` (None = status `none`).

    - ``day > today``: 422 `date_in_future`.
    - ``day == today``: computed from the stored settings (None without settings) and upserted.
    - ``day < today``: the frozen row, or None. Never writes.

    The caller has checked `health_data` (Ruling E5).
    """
    if day > today:
        raise ApiError("date_in_future", 422)
    if day < today:
        row = await _row(session, member, day)
        return None if row is None else frozen.from_row(row)
    result, _ = await targets_service.targets_for_today(session, member, today=today, cfg=cfg)
    await _upsert_frozen(session, member, day, frozen.to_row_values(result, cfg))
    return result


async def set_partial(
    session: AsyncSession, member: Member, day: date, partial: bool, *, today: date
) -> DiaryDay:
    """Mark a day as not fully logged (or clear it). Only `partial_logged` changes.

    - ``day > today``: 422 `date_in_future`.
    - Today with `health_data` active: today's row is computed first (E5).
    - Otherwise a missing row is inserted with status `none`; an existing row keeps its target.
    """
    if day > today:
        raise ApiError("date_in_future", 422)
    if day == today and await consents_service.has_active_consent(
        session, member.account_id, "health_data"
    ):
        await day_targets(session, member, day, today=today)
    stmt = insert(DiaryDay).values(
        member_id=member.id,
        local_date=day,
        account_id=member.account_id,
        status="none",
        partial_logged=partial,
    )
    await session.execute(
        stmt.on_conflict_do_update(
            index_elements=[DiaryDay.member_id, DiaryDay.local_date],
            set_={"partial_logged": partial},
        )
    )
    await session.flush()
    row = await _row(session, member, day)
    assert row is not None
    return row
