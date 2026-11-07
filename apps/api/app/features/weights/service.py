"""Weigh-ins: validation, the stored weight, the trend response (Plan 12 Task 23; G24-G28).

The pure maths is `app.scoring.weight_trend`. Nothing here touches `analyze`. Weights are health
data: never logged, never in analytics. Under `hide_all` no kg leaves this module.
"""

import math
from datetime import date, datetime, timedelta
from decimal import ROUND_HALF_UP, Decimal
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core import time as core_time
from app.core.errors import ApiError
from app.features.consents import service as consents_service
from app.features.diary.days import day_targets
from app.features.me import service as me_service
from app.features.members.models import Member
from app.features.targets import service as targets_service
from app.features.weights import store
from app.features.weights.models import WeightLog
from app.features.weights.schemas import (
    ProjectionOut,
    TrendPointOut,
    WeeklyRateOut,
    WeightIn,
    WeightOut,
    WeightPointOut,
    WeightsOut,
    WeightTrendOut,
)
from app.scoring import weight_trend as wt
from app.scoring.config import load_config

MAX_AGE_DAYS = 400
DEFAULT_LIST_DAYS = 90
CLIENT_ID_CONSTRAINT = "uq_weight_logs_account_id_client_id"
_TWO_DP = Decimal("0.01")


def _kg(x: Decimal | None) -> float | None:
    return None if x is None else float(x.quantize(_TWO_DP, rounding=ROUND_HALF_UP))


async def is_hidden(session: AsyncSession, member: Member) -> bool:
    """True when the member chose `hide_all` (energy-only hiding changes nothing here)."""
    row = await targets_service.get_settings(session, member)
    return row is not None and row.numbers_display == "hide_all"


def to_out(row: WeightLog, hidden: bool) -> WeightOut:
    return WeightOut(
        date=row.local_date,
        weight_kg=None if hidden else _kg(Decimal(row.weight_kg)),
        measured_at=row.measured_at,
        source="manual",  # type: ignore[arg-type]
        client_id=row.client_id,
        numbers_hidden=hidden,
    )


def _checked_kg(value: float) -> Decimal:
    if not math.isfinite(value):
        raise ApiError("weight_out_of_range", 422)
    kg = Decimal(str(value)).quantize(_TWO_DP, rounding=ROUND_HALF_UP)
    if kg < Decimal(2) or kg > Decimal(300):
        raise ApiError("weight_out_of_range", 422, details={"min": 2, "max": 300})
    return kg


def _needs_confirm(kg: Decimal, day: date, before: WeightLog | None) -> bool:  # G28
    cfg = load_config()
    plausible = cfg.targets["plausible"]["weight_kg"]
    if kg < Decimal(str(plausible["min"])) or kg > Decimal(str(plausible["max"])):
        return True
    if before is None:
        return False
    days = max(1, (day - before.local_date).days)
    return abs(kg - Decimal(before.weight_kg)) > wt.max_change_kg_per_day(cfg) * days


async def _by_client_id(
    session: AsyncSession, account_id: UUID, client_id: UUID
) -> WeightLog | None:
    return await session.scalar(
        select(WeightLog)
        .where(WeightLog.account_id == account_id, WeightLog.client_id == client_id)
        .execution_options(populate_existing=True)
    )


async def _refresh_member_weight(session: AsyncSession, member: Member) -> None:
    """`members.weight_kg` follows the latest weigh-in (G26). Unchanged when there is none, and
    while `health_data` is withdrawn (a terms-only delete must not write body data)."""
    if not await consents_service.has_active_consent(session, member.account_id, "health_data"):
        return
    last = await store.latest(session, member)
    if last is not None:
        member.weight_kg = float(last.weight_kg)
        await session.flush()


async def put_weigh_in(
    session: AsyncSession, member: Member, day: date, body: WeightIn, today: date
) -> tuple[WeightLog, bool]:
    """Create or replace the day's weigh-in (never commits). Returns (row, hidden)."""
    kg = _checked_kg(body.weight_kg)
    if body.client_id is not None:
        existing = await _by_client_id(session, member.account_id, body.client_id)
        if existing is not None:
            return existing, await is_hidden(session, member)
    if day > today:
        raise ApiError("date_in_future", 422)
    if (today - day).days > MAX_AGE_DAYS:
        raise ApiError("date_too_old", 422)
    hidden = await is_hidden(session, member)
    earlier = await store.list_weigh_ins(session, member, until=day - timedelta(days=1))
    before = earlier[-1] if earlier else None
    if not body.confirm_unusual and _needs_confirm(kg, day, before):
        raise ApiError(
            "weight_needs_confirm",
            422,
            details={
                "previous": None if before is None or hidden else _kg(Decimal(before.weight_kg)),
                "previous_date": None if before is None else before.local_date.isoformat(),
            },
        )
    now = core_time.now_utc()
    try:
        async with session.begin_nested():
            row = await store.upsert_weigh_in(session, member, day, kg, now, body.client_id)
    except IntegrityError as exc:
        constraint = getattr(getattr(exc.orig, "diag", None), "constraint_name", None)
        if body.client_id is None or constraint != CLIENT_ID_CONSTRAINT:
            raise
        # A concurrent put with the same client_id won the race: return its row.
        existing = await _by_client_id(session, member.account_id, body.client_id)
        if existing is None:  # pragma: no cover - the conflicting row was deleted meanwhile
            raise
        return existing, hidden
    await _refresh_member_weight(session, member)
    await _recompute_today(session, member, today)
    return row, hidden


async def _recompute_today(session: AsyncSession, member: Member, today: date) -> None:
    """Today's frozen targets follow the new weight (only while `health_data` is active)."""
    if await consents_service.has_active_consent(session, member.account_id, "health_data"):
        await day_targets(session, member, today, today=today)


async def delete_weigh_in(session: AsyncSession, member: Member, day: date, today: date) -> None:
    gone = await store.delete_weigh_in(session, member, day)
    if gone is None:
        raise ApiError("weight_not_found", 404)
    await _refresh_member_weight(session, member)
    await _recompute_today(session, member, today)


async def delete_all_weigh_ins(session: AsyncSession, member: Member, today: date) -> int:
    """Erase the member's whole weight history (terms only, never gated by `health_data`).
    `members.weight_kg` is left as it is (the profile keeps the last known weight, like the
    single delete when the last row goes); today's frozen targets are recomputed only while
    `health_data` is active, and then fall back to that profile weight."""
    count = await store.delete_all(session, member)
    if count:
        await _recompute_today(session, member, today)
    return count


async def list_range(
    session: AsyncSession, member: Member, since: date | None, until: date | None, today: date
) -> WeightsOut:
    until = until or today
    since = since or until - timedelta(days=DEFAULT_LIST_DAYS - 1)
    if since > until:
        raise ApiError("validation_error", 422, details={"fields": ["query.from"]})
    if (until - since).days > MAX_AGE_DAYS:
        raise ApiError("date_range_too_long", 422, details={"max_days": MAX_AGE_DAYS})
    rows = await store.list_weigh_ins(session, member, since=since, until=until)
    hidden = await is_hidden(session, member)
    return WeightsOut(items=[to_out(r, hidden) for r in rows], numbers_hidden=hidden)


async def trend(session: AsyncSession, member: Member, days: int, today: date) -> WeightTrendOut:
    """The trend over the member's full history, sliced to the window `days` ending today.
    `y` (0 to 1, 2 dp) is scaled over the weigh-ins and trend values of the window together, so
    the dots and the line share one scale and a hidden chart keeps its shape."""
    cfg = load_config()
    rows = await store.list_weigh_ins(session, member, until=today)
    settings_row = await targets_service.get_settings(session, member)
    hidden = settings_row is not None and settings_row.numbers_display == "hide_all"
    target = None
    if (
        settings_row is not None
        and settings_row.direction != "maintain"
        and settings_row.target_weight_kg is not None
    ):
        target = Decimal(str(settings_row.target_weight_kg))

    result = wt.compute_trend([wt.WeighIn(r.local_date, Decimal(r.weight_kg)) for r in rows], cfg)
    start = today - timedelta(days=days - 1)
    points = [p for p in result.points if p.day >= start]
    line = [(d, t) for d, t in result.trend if d >= start]
    ys = wt.shape([*(p.kg for p in points), *(t for _, t in line)])
    n = len(points)

    def y(i: int) -> float | None:
        return None if ys[i] is None else float(ys[i])  # type: ignore[arg-type]

    rate = wt.weekly_rate(result, cfg)
    reason, when = wt.projection(result, target, cfg)
    projection = None
    if reason == "ready":
        projection = ProjectionOut(
            target_kg=None if hidden else _kg(target),
            date=None if hidden else when,
        )
    return WeightTrendOut(
        member_id=member.id,
        days=days,  # type: ignore[arg-type]
        from_=start,
        to=today,
        points=[
            WeightPointOut(
                date=p.day,
                weight_kg=None if hidden else _kg(p.kg),
                outlier=p.outlier,
                y=y(i),
            )
            for i, p in enumerate(points)
        ],
        trend=[
            TrendPointOut(date=d, trend_kg=None if hidden else _kg(t), y=y(n + i))
            for i, (d, t) in enumerate(line)
        ],
        weekly_rate=None
        if rate is None or hidden
        else WeeklyRateOut(
            kg=_kg(rate[0]),  # type: ignore[arg-type]
            pct_bw=float(rate[1].quantize(_TWO_DP, rounding=ROUND_HALF_UP)),
        ),
        projection=projection,
        projection_reason=reason,
        flags=["rapid_loss"] if wt.rapid_loss(result, cfg) else [],
        rapid_loss_pct=None
        if hidden
        else float(cfg.targets["safety"]["rapid_loss_pct_bw_per_week"]),
        numbers_hidden=hidden,
    )


async def local_today(session: AsyncSession, account_id: UUID, now: datetime | None = None) -> date:
    return await me_service.account_today(session, account_id, now)
