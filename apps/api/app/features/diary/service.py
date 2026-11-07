"""The diary day, week, partial-day status and recents (Plan 11 Task 7). No FastAPI imports.

The diary works on `terms`. The `targets` part of the day and week views needs `health_data`,
checked here: without it the day still loads with `targets: null` and `consent_required`
(Ruling E14) and no frozen row is computed or written. Targets are information, never verdicts.
"""

from datetime import date, datetime, timedelta
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app import scoring
from app.core import time as core_time
from app.core.config import Settings
from app.core.errors import ApiError
from app.features.consents import service as consents_service
from app.features.diary import aggregate, days
from app.features.diary.schemas import (
    DiaryDayOut,
    DiaryDayStatusIn,
    DiaryDayStatusOut,
    DiaryWeekOut,
    RecentItem,
    RecentsOut,
    TargetsStatusOut,
)
from app.features.me import service as me_service
from app.features.meal_slots import service as slots_service
from app.features.meals import service as meals_service
from app.features.meals.models import MealLog
from app.features.members import service as members_service
from app.features.targets import service as targets_service
from app.scoring import targets as engine

RECENTS_MAX = 30
RECENTS_DAYS = 90


async def _display(session: AsyncSession, member) -> str:
    """The member's numbers display, read whether or not `health_data` is active."""
    row = await targets_service.get_settings(session, member)
    return row.numbers_display if row is not None else "show"


async def _health_ok(session: AsyncSession, account_id: UUID) -> bool:
    return await consents_service.has_active_consent(session, account_id, "health_data")


async def _clock(
    session: AsyncSession, account_id: UUID, now: datetime | None
) -> tuple[str, date, datetime]:
    now = now or core_time.now_utc()
    tz_name = await me_service.account_timezone(session, account_id)
    return tz_name, core_time.local_today(tz_name, now), now


async def get_day(
    session: AsyncSession,
    account_id: UUID,
    member_id: UUID | None,
    day: date | None,
    settings: Settings,
    *,
    now: datetime | None = None,
) -> DiaryDayOut:
    """One local day: slots with their entries and totals, the day's frozen targets, the
    remaining and progress, the sugar and salt bands. 404 for another account's member, 422
    `diary_member_not_enabled` for a non-primary member, 422 `date_in_future` for a future day."""
    member = await targets_service.resolve_member(session, account_id, member_id, settings)
    tz_name, today, _ = await _clock(session, account_id, now)
    day = day or today
    if day > today:
        raise ApiError("date_in_future", 422)
    slots = await slots_service.list_slots(session, member, include_archived=True)
    entries = await meals_service.list_meals_by_date(session, account_id, member.id, day, day)
    display = await _display(session, member)
    result: engine.TargetResult | None = None
    status: TargetsStatusOut = "consent_required"
    if await _health_ok(session, account_id):
        result = await days.day_targets(session, member, day, today=today)
        status = result.status if result is not None else "none"
    partial = (await days.partial_flags(session, member, day, day)).get(day, False)
    limits = scoring.daily_limits_for(
        members_service.to_scoring_member(member, today=day), member.weight_kg
    )
    return aggregate.build_day(
        member_id=member.id,
        day=day,
        today=today,
        timezone=tz_name,
        slots=slots,
        entries=entries,
        result=result,
        targets_status=status,
        limits=limits,
        partial_logged=partial,
        numbers_display=display,  # type: ignore[arg-type]
    )


async def get_week(
    session: AsyncSession,
    account_id: UUID,
    member_id: UUID | None,
    end: date | None,
    settings: Settings,
    *,
    now: datetime | None = None,
) -> DiaryWeekOut:
    """The 7 local days ending at ``end`` (default today), oldest first, each against its own
    frozen targets. Without `health_data` the tiles carry no targets."""
    member = await targets_service.resolve_member(session, account_id, member_id, settings)
    _, today, _ = await _clock(session, account_id, now)
    end = end or today
    if end > today:
        raise ApiError("date_in_future", 422)
    start = end - timedelta(days=6)
    entries = await meals_service.list_meals_by_date(session, account_id, member.id, start, end)
    results: dict[date, engine.TargetResult | None] = {}
    if await _health_ok(session, account_id):
        for i in range(7):
            d = start + timedelta(days=i)
            results[d] = await days.day_targets(session, member, d, today=today)
    partial = await days.partial_flags(session, member, start, end)
    limits = scoring.daily_limits_for(
        members_service.to_scoring_member(member, today=end), member.weight_kg
    )
    return aggregate.build_week(
        member_id=member.id,
        end=end,
        today=today,
        entries=entries,
        results=results,
        partial=partial,
        limits=limits,
        numbers_display=await _display(session, member),  # type: ignore[arg-type]
    )


async def put_status(
    session: AsyncSession,
    account_id: UUID,
    day: date,
    body: DiaryDayStatusIn,
    settings: Settings,
    *,
    now: datetime | None = None,
) -> DiaryDayStatusOut:
    """Mark a day as not fully logged, or clear the mark. Only `partial_logged` changes; a past
    day without a row gets a `none` row (never a back-filled target)."""
    member = await targets_service.resolve_member(session, account_id, body.member_id, settings)
    _, today, _ = await _clock(session, account_id, now)
    row = await days.set_partial(session, member, day, body.partial_logged, today=today)
    return DiaryDayStatusOut(date=row.local_date, partial_logged=row.partial_logged)


async def recents(
    session: AsyncSession,
    account_id: UUID,
    member_id: UUID | None,
    slot_id: UUID | None,
    limit: int,
    settings: Settings,
    *,
    now: datetime | None = None,
) -> RecentsOut:
    """What the member logged lately (Ruling E18): no quick adds, one item per product or
    barcode (the newest entry), newest first, at most ``limit`` (30) from the last 90 local
    days. The given slot's items come first."""
    member = await targets_service.resolve_member(session, account_id, member_id, settings)
    _, today, _ = await _clock(session, account_id, now)
    if slot_id is not None:
        slots = await slots_service.list_slots(session, member, include_archived=True)
        if all(s.id != slot_id for s in slots):
            raise ApiError("meal_slot_not_found", 404)
    since = today - timedelta(days=RECENTS_DAYS - 1)
    rows = await session.scalars(
        select(MealLog)
        .where(
            MealLog.account_id == account_id,
            MealLog.member_id == member.id,
            MealLog.local_date >= since,
            MealLog.source_kind != "quick_add",
        )
        .order_by(MealLog.eaten_at.desc(), MealLog.id)
    )
    seen: set[tuple[str, str]] = set()
    items: list[RecentItem] = []
    for r in rows:
        # One item per product, barcode or food (the newest entry). An entry whose reference is
        # gone (a deleted custom food, slice 4) has nothing to log again and is skipped.
        if r.product_id is not None:
            key = ("product", str(r.product_id))
        elif r.food_id is not None:
            key = ("food", str(r.food_id))
        elif r.off_barcode:
            key = ("off", r.off_barcode)
        else:
            continue
        if key in seen:
            continue
        seen.add(key)
        items.append(
            RecentItem(
                source_kind=r.source_kind,  # type: ignore[arg-type]
                product_id=r.product_id,
                barcode=r.off_barcode,
                food_id=r.food_id,
                name=r.product_name or "",
                grade=r.grade,  # type: ignore[arg-type]
                grams=r.grams or 0.0,
                quantity=None if r.quantity is None else float(r.quantity),
                unit=r.unit,
                meal_slot_id=r.meal_slot_id,
                last_eaten_at=r.eaten_at,
                attribution=meals_service.OFF_ATTRIBUTION if r.off_barcode else None,
                attributions=meals_service._attributions(r),
            )
        )
    if slot_id is not None:
        items = [i for i in items if i.meal_slot_id == slot_id] + [
            i for i in items if i.meal_slot_id != slot_id
        ]
    return RecentsOut(items=items[: min(limit, RECENTS_MAX)])
