"""Meal slots: defaults, reads and the slot an entry goes to (Plan 11 Task 2).

Slots hold no health data. Custom labels are user text: never logged, never sent to analytics
or prompts. No FastAPI imports.
"""

import unicodedata
from datetime import UTC, datetime, time
from typing import Literal
from uuid import UUID

from sqlalchemy import exists, func, select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import ApiError
from app.features.meal_slots.defaults import DEFAULT_SLOTS, LABEL_MAX_CHARS, MAX_ACTIVE_SLOTS
from app.features.meal_slots.models import MealSlot
from app.features.meal_slots.rules import SlotChoice, SlotWindow, pick_slot
from app.features.meal_slots.schemas import (
    MealSlotCreateIn,
    MealSlotOut,
    MealSlotRenameIn,
    TimeWindow,
)
from app.features.meals.models import MealLog
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
        raise ApiError("meal_slot_limit_reached", 422, details={"max": MAX_ACTIVE_SLOTS})


# ---- writes (Plan 11 Task 14). Labels are user text: never put one in an error, log or event.


def _invalid(field: str) -> ApiError:
    return ApiError("validation_error", 422, details={"fields": [f"body.{field}"]})


def clean_label(raw: str) -> str:
    """Trim; 1 to 30 code points; no control characters, else 422 `validation_error`."""
    label = raw.strip()
    if not 1 <= len(label) <= LABEL_MAX_CHARS or any(
        unicodedata.category(ch) == "Cc" for ch in label
    ):
        raise _invalid("custom_label")
    return label


async def _lock_member(session: AsyncSession, member: Member) -> None:
    """Serialise slot writes per member, then make sure the defaults exist."""
    await session.execute(select(Member.id).where(Member.id == member.id).with_for_update())
    await ensure_defaults(session, member)


async def _label_taken(
    session: AsyncSession, member: Member, label: str, *, except_id: UUID | None = None
) -> bool:
    query = select(
        exists().where(
            MealSlot.member_id == member.id,
            MealSlot.archived_at.is_(None),
            func.lower(MealSlot.custom_label) == func.lower(label),
            *([MealSlot.id != except_id] if except_id else []),
        )
    )
    return bool(await session.scalar(query))


def _window_json(window: TimeWindow | None) -> dict[str, str] | None:
    return {"start": window.start, "end": window.end} if window else None


async def _slot(session: AsyncSession, member: Member, slot_id: UUID) -> MealSlot:
    row = await session.scalar(
        select(MealSlot)
        .where(MealSlot.id == slot_id, MealSlot.member_id == member.id)
        .execution_options(populate_existing=True)
    )
    if row is None:
        raise ApiError("meal_slot_not_found", 404)
    return row


def _duplicate() -> ApiError:
    return ApiError("meal_slot_label_duplicate", 422)  # no details: the label is never echoed


async def create_slot(
    session: AsyncSession, member: Member, body: MealSlotCreateIn
) -> tuple[MealSlot, bool]:
    label = clean_label(body.custom_label)
    await _lock_member(session, member)
    if body.client_id is not None:
        stored = await session.scalar(
            select(MealSlot)
            .where(
                MealSlot.account_id == member.account_id,
                MealSlot.client_id == body.client_id,
                MealSlot.member_id == member.id,
            )
            .execution_options(populate_existing=True)
        )
        if stored is not None:
            return stored, False
    await ensure_can_add_slot(session, member)
    if await _label_taken(session, member, label):
        raise _duplicate()
    top = await session.scalar(
        select(func.max(MealSlot.position)).where(
            MealSlot.member_id == member.id, MealSlot.archived_at.is_(None)
        )
    )
    row = MealSlot(
        account_id=member.account_id,
        member_id=member.id,
        position=(top if top is not None else -1) + 1,
        custom_label=label,
        default_time_window=_window_json(body.default_time_window),
        is_default=False,
        client_id=body.client_id,
    )
    session.add(row)
    try:
        await session.flush()
    except IntegrityError:
        await session.rollback()
        raise _duplicate() from None
    return row, True


async def rename_slot(
    session: AsyncSession, member: Member, slot_id: UUID, body: MealSlotRenameIn
) -> MealSlot:
    if body.custom_label is not None and body.clear_custom_label:
        raise _invalid("clear_custom_label")
    if body.default_time_window is not None and body.clear_time_window:
        raise _invalid("clear_time_window")
    label = clean_label(body.custom_label) if body.custom_label is not None else None
    await _lock_member(session, member)
    row = await _slot(session, member, slot_id)
    if row.archived_at is not None:
        raise ApiError("meal_slot_archived", 422)
    if body.clear_custom_label:
        if row.label_key is None:  # a custom slot has no original name to go back to
            raise _invalid("clear_custom_label")
        row.custom_label = None
    elif label is not None:
        if await _label_taken(session, member, label, except_id=row.id):
            raise _duplicate()
        row.custom_label = label
    if body.clear_time_window:
        row.default_time_window = None
    elif body.default_time_window is not None:
        row.default_time_window = _window_json(body.default_time_window)
    row.updated_at = datetime.now(UTC)
    try:
        await session.flush()
    except IntegrityError:
        await session.rollback()
        raise _duplicate() from None
    return row


async def reorder_slots(session: AsyncSession, member: Member, ids: list[UUID]) -> list[MealSlot]:
    await _lock_member(session, member)
    rows = await list_slots(session, member, include_archived=True)
    known = {r.id: r for r in rows}
    if any(i not in known for i in ids):
        raise ApiError("meal_slot_not_found", 404)
    active = {r.id for r in rows if r.archived_at is None}
    if len(set(ids)) != len(ids) or set(ids) != active:
        raise _invalid("ids")
    for position, slot_id in enumerate(ids):
        known[slot_id].position = position
        known[slot_id].updated_at = datetime.now(UTC)
    await session.flush()
    return [known[i] for i in ids]


async def archive_slot(
    session: AsyncSession, member: Member, slot_id: UUID
) -> Literal["archived", "deleted"]:
    await _lock_member(session, member)
    row = await _slot(session, member, slot_id)
    if row.archived_at is not None:
        return "archived"
    active = [r for r in await list_slots(session, member) if r.archived_at is None]
    if len(active) <= 1:
        raise ApiError("meal_slot_last_active", 422)
    used = await session.scalar(select(exists().where(MealLog.meal_slot_id == row.id)))
    # A default slot is archived even when unused: deleting it would let `ensure_defaults`
    # bring it back on the next read.
    if used or row.is_default:
        row.archived_at = datetime.now(UTC)
        row.updated_at = row.archived_at
        await session.flush()
        return "archived"
    await session.delete(row)
    await session.flush()
    return "deleted"
