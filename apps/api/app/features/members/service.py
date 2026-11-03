"""Family members: the auto-created primary, CRUD with the health-data consent gate, and the
mapping to the rules engine.

Member names and health fields never go to logs.
"""

from collections.abc import Sequence
from datetime import date
from uuid import UUID

from sqlalchemy import delete, func, select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app import scoring
from app.core.errors import ApiError
from app.core.time import today_ist
from app.features.consents import service as consents_service
from app.features.me import service as me_service
from app.features.members.models import Member
from app.features.members.schemas import (
    HEALTH_FIELDS,
    MemberIn,
    MemberPatch,
    goal_allowed_at_age,
)

MAX_MEMBERS = 10


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


def youngest_age(birth_year: int | None, today: date) -> int | None:
    """The youngest age a birth year allows: max(0, today.year - birth_year - 1).

    With only a birth year, the birthday may still be ahead this year, and the engine's
    younger age bands are stricter, so the younger age is the safe one (Plan 3 R19). None
    when there is no birth year or it lies in the future.
    """
    if birth_year is None or birth_year > today.year:
        return None
    return max(0, today.year - birth_year - 1)


def to_scoring_member(record: Member, *, today: date) -> scoring.Member:
    """Map a member row to the engine's Member.

    Age is the YOUNGEST age the birth year allows: max(0, today.year - birth_year - 1). With
    only a birth year, the birthday may still be ahead this year, and the engine's younger age
    bands (infant, child) are stricter, so assuming the older age could turn an `avoid` into
    `ok` (e.g. born two years ago may still be 1, an infant). Age is None (unknown, so the
    engine stays protective) when there is no birth year or it lies in the future.
    """
    return scoring.Member(
        id=str(record.id),
        name=record.name,
        age=youngest_age(record.birth_year, today),
        diet=scoring.Diet(record.diet),
        allergens=tuple(record.allergens or ()),
        conditions=tuple(record.conditions or ()),
        goal=record.goal,
        custom_alerts=tuple(record.custom_alerts or ()),
    )


# --- CRUD (Plan 5 Task 5) ---------------------------------------------------------------------


# List fields where dropping entries (a strict subset of what is stored) is a pure removal.
_REMOVABLE_LISTS = frozenset({"allergens", "conditions"})


def _writes_health_data(values: dict[str, object], current: Member | None) -> bool:
    """True if a health field is being set to a non-empty value it doesn't already hold.

    Only the fields in this request count (P5). Re-sending a stored value unchanged saves no
    new health data, so a client that sends the whole form can still rename a member after
    `health_data` is withdrawn. Clearing a field (null or []) is never gated, and neither is
    removing entries from stored allergens or conditions (a subset of the stored list, Ruling
    P8.1): that writes nothing new, and gating it would push users to wipe a whole list.
    """
    for field in HEALTH_FIELDS:
        if field not in values:
            continue
        value = values[field]
        if value is None or value == []:
            continue
        if current is not None:
            stored = getattr(current, field)
            if _same(stored, value):
                continue
            if field in _REMOVABLE_LISTS and _is_subset(value, stored):
                continue
        return True
    return False


def _same(stored: object, value: object) -> bool:
    if isinstance(stored, list | tuple) and isinstance(value, list | tuple):
        return list(stored) == list(value)
    return stored == value


def _is_subset(value: object, stored: object) -> bool:
    """Every entry of `value` is already stored, exactly as stored."""
    if not isinstance(value, list | tuple) or not isinstance(stored, list | tuple):
        return False
    return set(value) <= set(stored)


async def _require_health_consent(
    session: AsyncSession,
    account_id: UUID,
    values: dict[str, object],
    current: Member | None = None,
) -> None:
    """403 `consent_required` unless `health_data` is active at the current version (P5).

    `ai_processing` does not gate member saves; it only gates the LLM explanation.
    """
    if _writes_health_data(values, current) and not await consents_service.has_active_consent(
        session, account_id, "health_data"
    ):
        raise ApiError("consent_required", 403, details={"purpose": "health_data"})


def _relation_error() -> ApiError:
    return ApiError("validation_error", 422, details={"fields": ["body.relation"]})


def _check_goal_age(goal: str | None, birth_year: int | None) -> None:
    """422 `body.goal` for an adult-only goal (build_muscle) at a minor's youngest age (P9
    safety S4). The age is the engine's youngest-age rule; an unknown age is allowed."""
    if not goal_allowed_at_age(goal, youngest_age(birth_year, today_ist())):
        raise ApiError("validation_error", 422, details={"fields": ["body.goal"]})


async def list_members(session: AsyncSession, account_id: UUID) -> list[Member]:
    """The account's members: the primary first, then in creation order. Read-only."""
    rows = await session.scalars(
        select(Member)
        .where(Member.account_id == account_id)
        .order_by(Member.is_primary.desc(), Member.created_at, Member.id)
    )
    return list(rows)


async def get_member(session: AsyncSession, account_id: UUID, member_id: UUID) -> Member:
    """The member, or 404 `member_not_found` (the same for unknown and foreign ids)."""
    member = await session.scalar(
        select(Member).where(Member.account_id == account_id, Member.id == member_id)
    )
    if member is None:
        raise ApiError("member_not_found", 404)
    return member


async def create_member(session: AsyncSession, account_id: UUID, body: MemberIn) -> Member:
    """Add a non-primary member (never commits).

    The consent gate runs before anything is written. The 10-member limit is counted under the
    same advisory lock as `get_or_create_primary`, so concurrent creates can't exceed it.
    """
    values = body.model_dump()
    _check_goal_age(body.goal, body.birth_year)
    await _require_health_consent(session, account_id, values)
    await get_or_create_primary(session, account_id)  # takes the per-account lock
    count = await session.scalar(
        select(func.count()).select_from(Member).where(Member.account_id == account_id)
    )
    if count >= MAX_MEMBERS:
        raise ApiError("member_limit", 422, details={"max": MAX_MEMBERS})
    member = Member(
        account_id=account_id,
        is_primary=False,
        created_at=func.clock_timestamp(),
        updated_at=func.clock_timestamp(),
        **values,
    )
    session.add(member)
    await session.flush()
    await session.refresh(member)
    return member


async def update_member(
    session: AsyncSession, account_id: UUID, member_id: UUID, body: MemberPatch
) -> Member:
    """Apply only the fields sent (never commits). See `MemberPatch.changes` for nulls.

    Ownership is checked first (404), so a 403 never confirms that a foreign id exists.
    """
    member = await get_member(session, account_id, member_id)
    changes = body.changes()
    # Only the primary is `self`, and the primary's relation can't change.
    if "relation" in changes and (changes["relation"] == "self") != member.is_primary:
        raise _relation_error()
    # Checked when the goal or the birth year is written; a stored legacy pair is left alone.
    if "goal" in changes or "birth_year" in changes:
        _check_goal_age(
            changes.get("goal", member.goal),  # type: ignore[arg-type]
            changes.get("birth_year", member.birth_year),  # type: ignore[arg-type]
        )
    await _require_health_consent(session, account_id, changes, member)
    for field, value in changes.items():
        setattr(member, field, value)
    member.updated_at = func.clock_timestamp()
    await session.flush()
    await session.refresh(member)
    return member


async def delete_member(session: AsyncSession, account_id: UUID, member_id: UUID) -> None:
    """Delete a non-primary member (never commits). The primary can't be deleted (P2)."""
    member = await get_member(session, account_id, member_id)
    if member.is_primary:
        raise ApiError("primary_member", 422)
    await session.execute(
        delete(Member).where(Member.account_id == account_id, Member.id == member.id)
    )
    await session.flush()
