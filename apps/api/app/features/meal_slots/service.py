"""Meal slots: defaults, reads and the slot an entry goes to (Plan 11 Task 2).

Slots hold no health data. Custom labels are user text: never logged, never sent to analytics
or prompts. No FastAPI imports.
"""

from datetime import time
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import ApiError
from app.features.meal_slots.defaults import DEFAULT_SLOTS, MAX_ACTIVE_SLOTS
from app.features.meal_slots.models import MealSlot
from app.features.meal_slots.rules import SlotChoice, SlotWindow, pick_slot
from app.features.meal_slots.schemas import MealSlotOut, TimeWindow
from app.features.members.models import Member


def _hhmm(value: str) -> time:
    hh, mm = value.split(":")
    return time(int(hh), int(mm))


def window_of(row: MealSlot) -> SlotWindow | None:
    w = row.default_time_window
    if not w:
        return None
    return SlotWindow(_hhmm(w["start"]), _hhmm(w["end"]))


def choices(rows: list[MealSlot]) -> list[SlotChoice]:
    return [SlotChoice(r.id, r.position, window_of(r)) for r in rows if r.archived_at is None]


async def ensure_defaults(session: AsyncSession, member: Member) -> None:
    """Create the member's four default slots if missing (idempotent; never commits)."""
    stmt = insert(MealSlot).values(
        [
            {
                "account_id": member.account_id,
                "member_id": member.id,
                "position": d.position,
                "label_key": d.label_key,
                "default_time_window": {
                    "start": d.start.strftime("%H:%M"),
                    "end": d.end.strftime("%H:%M"),
                },
                "is_default": True,
            }
            for d in DEFAULT_SLOTS
        ]
    )
    # The partial unique index (member_id, label_key) WHERE is_default is the conflict target.
    await session.execute(
        stmt.on_conflict_do_nothing(
            index_elements=["member_id", "label_key"], index_where=MealSlot.is_default
        )
    )


async def list_slots(
    session: AsyncSession, member: Member, *, include_archived: bool = False
) -> list[MealSlot]:
    """The member's slots in position order (defaults created first)."""
    await ensure_defaults(session, member)
    query = (
        select(MealSlot)
        .where(MealSlot.member_id == member.id, MealSlot.account_id == member.account_id)
        .order_by(MealSlot.position, MealSlot.created_at, MealSlot.id)
        .execution_options(populate_existing=True)
    )
    if not include_archived:
        query = query.where(MealSlot.archived_at.is_(None))
    return list(await session.scalars(query))


async def slot_for_entry(
    session: AsyncSession, member: Member, slot_id: UUID | None, at_local: time
) -> MealSlot:
    """The slot a new or moved entry uses.

    None: the default for the wall-clock time (``pick_slot``). A given id that is unknown or
    another member's: 404 `meal_slot_not_found` (Ruling E22); an archived one: 422
    `meal_slot_archived`.
    """
    rows = await list_slots(session, member, include_archived=True)
    if slot_id is None:
        picked = pick_slot(choices(rows), at_local)
        return next(r for r in rows if r.id == picked)
    slot = next((r for r in rows if r.id == slot_id), None)
    if slot is None:
        raise ApiError("meal_slot_not_found", 404)
    if slot.archived_at is not None:
        raise ApiError("meal_slot_archived", 422)
    return slot


def to_out(row: MealSlot) -> MealSlotOut:
    w = row.default_time_window
    return MealSlotOut(
        id=row.id,
        member_id=row.member_id,
        position=row.position,
        label_key=row.label_key,
        custom_label=row.custom_label,
        default_time_window=TimeWindow(start=w["start"], end=w["end"]) if w else None,
        is_default=row.is_default,
        archived=row.archived_at is not None,
    )


async def ensure_can_add_slot(session: AsyncSession, member: Member) -> None:
    """Guard for the create route (Task 14): at most `max_active` (defaults.yaml) active slots
    per member, else 422 `meal_slot_limit_reached`. Archived slots do not count."""
    active = await list_slots(session, member)
    if len(active) >= MAX_ACTIVE_SLOTS:
        raise ApiError("meal_slot_limit_reached", 422)
