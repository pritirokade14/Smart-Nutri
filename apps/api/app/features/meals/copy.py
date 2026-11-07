"""Copy a meal or a day onto another day (Plan 11 Task 6; Rulings E9, E12).

Each copy keeps its source's snapshot (the product is never fetched again) and gets its own
`client_id` = uuid5(request client_id, source id), so a retry returns the same rows and a
double tap creates nothing twice. `eaten_at` is the target day at the source's local clock time,
capped at now. Every created entry counts against the `meal_logs` limit. No FastAPI imports.
"""

from datetime import datetime, timedelta
from uuid import UUID, uuid5

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.core import time as core_time
from app.core.config import Settings
from app.core.errors import ApiError
from app.core.ratelimit import consume
from app.features.consents import service as consents_service
from app.features.diary.days import day_targets
from app.features.foods.models import Food
from app.features.me import service as me_service
from app.features.meal_slots import service as slots_service
from app.features.meals import service as meals_service
from app.features.meals.models import MealLog
from app.features.meals.schemas import CopyIn
from app.features.targets import service as targets_service

COPY_MAX = 50
MAX_TARGET_AGE_DAYS = 30


def _snapshot_of(source: MealLog) -> dict | None:
    """The source's food snapshot; a legacy row gets one derived from its nutrients (the exact
    inverse), a quick add has none."""
    if source.source_kind == "quick_add":
        return None
    if source.food_snapshot is not None:
        return source.food_snapshot
    return {
        "name": source.product_name or "",
        "brand": None,
        "basis": "g",
        "per_100": meals_service.per_100_of(source),
        "units": {},
        "attribution": meals_service.OFF_ATTRIBUTION if source.off_barcode else None,
        "attributions": [meals_service.OFF_ATTRIBUTION] if source.off_barcode else [],
        "licence": None,
        "source": None,
    }


def _derived_id(client_id: UUID, source_id: UUID) -> UUID:
    return uuid5(client_id, str(source_id))


async def _read_back(session: AsyncSession, account_id: UUID, ids: list[UUID]) -> list[MealLog]:
    rows = await session.scalars(
        select(MealLog)
        .where(MealLog.account_id == account_id, MealLog.client_id.in_(ids))
        .execution_options(populate_existing=True)
    )
    by_client = {r.client_id: r for r in rows}
    return [by_client[i] for i in ids if i in by_client]


async def _refuse_retired(session: AsyncSession, sources: list[MealLog]) -> None:
    """A dish we no longer offer is never logged anew: 422 `food_retired` (before anything is
    counted). Reading the old entry is unaffected."""
    food_ids = {s.food_id for s in sources if s.food_id is not None}
    if not food_ids:
        return
    retired = await session.scalar(
        select(Food.id).where(Food.id.in_(food_ids), Food.review_status == "retired").limit(1)
    )
    if retired is not None:
        raise ApiError("food_retired", 422)


async def copy_entries(
    session: AsyncSession,
    account_id: UUID,
    body: CopyIn,
    settings: Settings,
    *,
    now: datetime | None = None,
) -> tuple[list[MealLog], bool]:
    """(rows, created_any). Commits. Checks, in order: the member, the dates, the source and
    target slots, the sources (empty, more than 50), an archived source slot without a target.
    Then the copies are counted against `meal_logs` (only those not already stored) and
    inserted with ON CONFLICT DO NOTHING, and read back by their derived ids in source order."""
    member = await targets_service.resolve_member(session, account_id, body.member_id, settings)
    now = now or core_time.now_utc()
    tz_name = await me_service.account_timezone(session, account_id)
    today = core_time.local_today(tz_name, now)
    if body.from_date > today or body.to_date > today:
        raise ApiError("date_in_future", 422)
    if body.to_date < today - timedelta(days=MAX_TARGET_AGE_DAYS):
        raise ApiError("date_too_old", 422)

    slots = {
        s.id: s for s in await slots_service.list_slots(session, member, include_archived=True)
    }
    if body.from_slot_id is not None and body.from_slot_id not in slots:
        raise ApiError("meal_slot_not_found", 404)  # an archived source slot is allowed
    if body.to_slot_id is not None:
        target_slot = slots.get(body.to_slot_id)
        if target_slot is None:
            raise ApiError("meal_slot_not_found", 404)
        if target_slot.archived_at is not None:
            raise ApiError("meal_slot_archived", 422)

    query = (
        select(MealLog)
        .where(
            MealLog.account_id == account_id,
            MealLog.member_id == member.id,
            MealLog.local_date == body.from_date,
        )
        .order_by(MealLog.eaten_at, MealLog.id)
    )
    if body.from_slot_id is not None:
        query = query.where(MealLog.meal_slot_id == body.from_slot_id)
    sources = list(await session.scalars(query))
    if not sources:
        raise ApiError("copy_source_empty", 422)
    if len(sources) > COPY_MAX:
        raise ApiError("copy_too_many", 422)
    if body.to_slot_id is None and any(slots[s.meal_slot_id].archived_at for s in sources):
        raise ApiError("meal_slot_archived", 422)

    ids = [_derived_id(body.client_id, s.id) for s in sources]
    stored = await _read_back(session, account_id, ids)
    stored_ids = {r.client_id for r in stored}
    todo = [(s, i) for s, i in zip(sources, ids, strict=True) if i not in stored_ids]
    if not todo:
        return stored, False  # a retry: every copy exists, nothing is counted
    await _refuse_retired(session, [s for s, _ in todo])

    planned = []
    for source, client_id in todo:
        clock = core_time.local_clock(source.eaten_at, tz_name)
        at = min(now, datetime.combine(body.to_date, clock, tzinfo=core_time.zone(tz_name)))
        # Never store what a normal log refuses (same check, same code), before anything counts.
        meals_service._check_eaten_at(at, now)
        planned.append((source, client_id, at))

    await consume(session, settings, account_id=account_id, bucket="meal_logs", n=len(todo))
    values = []
    for source, client_id, at in planned:
        values.append(
            {
                "account_id": account_id,
                "member_id": member.id,
                "source_kind": source.source_kind,
                "product_id": source.product_id,
                "off_barcode": source.off_barcode,
                "food_id": source.food_id,
                "custom_food_id": source.custom_food_id,
                "recipe_id": source.recipe_id,
                "quantity": source.quantity,
                "unit": source.unit,
                "product_name": source.product_name,
                "grade": source.grade,
                "grams": source.grams,
                "nutrients": source.nutrients,
                "food_snapshot": _snapshot_of(source),
                "eaten_at": at,
                "local_date": body.to_date,
                "meal_slot_id": body.to_slot_id or source.meal_slot_id,
                "client_id": client_id,
            }
        )
    result = await session.execute(
        insert(MealLog)
        .values(values)
        .on_conflict_do_nothing(index_elements=["account_id", "client_id"])
        .returning(MealLog.client_id)
    )
    created_any = bool(result.all())
    if (
        body.to_date == today
        and member.is_primary
        and await consents_service.has_active_consent(session, account_id, "health_data")
    ):
        await day_targets(session, member, today, today=today)  # today's frozen row exists
    await session.commit()
    return await _read_back(session, account_id, ids), created_any
