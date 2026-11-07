"""Favourite foods and saved meals (Plan 12 Task 17; spec 5.10, 6.4; G21, G23). No FastAPI
imports.

Solo only: every call resolves the member with `targets_service.resolve_member` (a foreign
member is 404, a non-primary one 422 `diary_member_not_enabled`). Every query is scoped by
account. A favourite meal keeps the entries of one slot and day as they were, so logging it
again follows the copy rules: the foods are never read again, an entry of a retired dish is
refused (`food_retired`), a custom food or recipe that was deleted since is logged with a NULL
reference (its name and values stay in the snapshot), and every created entry counts against
the `meal_logs` limit. Meal names are user text: never logged, never in an error.
"""

from datetime import datetime, timedelta
from uuid import UUID, uuid5

from sqlalchemy import func, select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core import time as core_time
from app.core.config import Settings
from app.core.errors import ApiError
from app.core.ratelimit import consume
from app.features.consents import service as consents_service
from app.features.custom_foods.models import CustomFood
from app.features.diary.days import day_targets
from app.features.favourites.models import MAX_FAVOURITES, Favourite
from app.features.favourites.schemas import (
    FavouriteIn,
    FavouriteItemOut,
    FavouriteLogIn,
    FavouriteMealIn,
    FavouriteOut,
)
from app.features.foods import resolve as foods_resolve
from app.features.foods import units as food_units
from app.features.me import service as me_service
from app.features.meal_slots import service as slots_service
from app.features.meals import copy as copy_service
from app.features.meals import service as meals_service
from app.features.meals.models import MealLog
from app.features.members.models import Member
from app.features.recipes.models import Recipe
from app.features.targets import service as targets_service
from app.integrations.openfoodfacts import OffClient

CLIENT_ID_CONSTRAINT = "uq_favourites_account_id_client_id"
NAME_MAX = 200  # ck_favourites_name


async def _member(
    session: AsyncSession, account_id: UUID, member_id: UUID | None, settings: Settings
) -> Member:
    return await targets_service.resolve_member(session, account_id, member_id, settings)


async def get_owned(session: AsyncSession, account_id: UUID, favourite_id: UUID) -> Favourite:
    row = await session.scalar(
        select(Favourite).where(Favourite.account_id == account_id, Favourite.id == favourite_id)
    )
    if row is None:
        raise ApiError("favourite_not_found", 404)
    return row


async def list_favourites(
    session: AsyncSession,
    account_id: UUID,
    member_id: UUID | None,
    settings: Settings,
) -> list[Favourite]:
    """Newest first, at most 200 (the limit), no cursor."""
    member = await _member(session, account_id, member_id, settings)
    rows = await session.scalars(
        select(Favourite)
        .where(Favourite.account_id == account_id, Favourite.member_id == member.id)
        .order_by(Favourite.created_at.desc(), Favourite.id)
        .limit(MAX_FAVOURITES)
    )
    return list(rows)


async def _count(session: AsyncSession, member: Member) -> int:
    return (
        await session.scalar(
            select(func.count()).select_from(Favourite).where(Favourite.member_id == member.id)
        )
    ) or 0


async def _check_room(session: AsyncSession, member: Member) -> None:
    if await _count(session, member) >= MAX_FAVOURITES:
        raise ApiError("favourite_limit", 422)


def _source_kind(loaded: foods_resolve.LoadedFood) -> str:
    """The same kinds `log_meal` stores on an entry."""
    if loaded.food_id is not None:
        return "food"
    if loaded.ref.kind in ("custom_food", "recipe"):
        return loaded.ref.kind
    return "product" if loaded.product_id is not None else "off"


async def add_food(
    session: AsyncSession,
    account_id: UUID,
    body: FavouriteIn,
    *,
    off: OffClient,
    settings: Settings,
) -> tuple[Favourite, bool]:
    """(favourite, created). Commits. The same food again returns the stored favourite
    (created=False) and changes nothing. 422 `favourite_limit` past 200, `food_retired` for a
    dish we no longer offer, `unit_grams_unknown` for a default unit this food cannot convert."""
    member = await _member(session, account_id, body.member_id, settings)
    ref = foods_resolve.ref_from_ids(
        food_id=body.food_id,
        product_id=body.product_id,
        barcode=body.barcode,
        custom_food_id=body.custom_food_id,
        recipe_id=body.recipe_id,
    )
    loaded = await foods_resolve.load_food(
        session, off, ref, account_id=account_id, settings=settings
    )
    if loaded.retired:
        raise ApiError("food_retired", 422)
    source_kind = _source_kind(loaded)
    refs = {
        "product_id": loaded.product_id,
        "off_barcode": loaded.off_barcode,
        "food_id": loaded.food_id,
        "custom_food_id": loaded.custom_food_id,
        "recipe_id": loaded.recipe_id,
    }
    (column, value) = next((k, v) for k, v in refs.items() if v is not None)
    existing = await session.scalar(
        select(Favourite).where(
            Favourite.member_id == member.id, getattr(Favourite, column) == value
        )
    )
    if existing is not None:
        await session.commit()  # keep the OFF cache write
        return existing, False
    await _check_room(session, member)
    quantity = unit = None
    if body.default_unit is not None and body.default_quantity is not None:
        resolved = food_units.resolve_units(loaded.units, await foods_resolve.unit_table(session))
        if body.default_unit not in {r.code for r in resolved}:
            raise ApiError("unit_grams_unknown", 422)
        quantity, unit = body.default_quantity, body.default_unit
    row = Favourite(
        account_id=account_id,
        member_id=member.id,
        kind="food",
        source_kind=source_kind,
        name=loaded.name[:NAME_MAX] or "-",
        default_quantity=quantity,
        default_unit=unit,
        attributions=list(loaded.attributions),
        created_at=core_time.now_utc(),
        **refs,
    )
    try:
        async with session.begin_nested():
            session.add(row)
            await session.flush()
    except IntegrityError:
        # A concurrent star of the same food won the race: return its row.
        await session.commit()
        won = await session.scalar(
            select(Favourite).where(
                Favourite.member_id == member.id, getattr(Favourite, column) == value
            )
        )
        if won is None:  # pragma: no cover - deleted meanwhile
            raise
        return won, False
    await session.commit()
    await session.refresh(row)
    return row, True


async def _by_client_id(
    session: AsyncSession, account_id: UUID, client_id: UUID
) -> Favourite | None:
    return await session.scalar(
        select(Favourite).where(
            Favourite.account_id == account_id, Favourite.client_id == client_id
        )
    )


async def add_meal(
    session: AsyncSession,
    account_id: UUID,
    body: FavouriteMealIn,
    settings: Settings,
    *,
    now: datetime | None = None,
) -> tuple[Favourite, bool]:
    """(favourite, created). Commits. Saves the entries of one slot on one day, in time order,
    as they were. A repeated `client_id` returns the stored favourite. Errors: `date_in_future`,
    `meal_slot_not_found`, `copy_source_empty`, `copy_too_many` (more than 50),
    `favourite_limit`."""
    member = await _member(session, account_id, body.member_id, settings)
    if body.client_id is not None:
        existing = await _by_client_id(session, account_id, body.client_id)
        if existing is not None:
            return existing, False
    now = now or core_time.now_utc()
    tz_name = await me_service.account_timezone(session, account_id)
    if body.from_date > core_time.local_today(tz_name, now):
        raise ApiError("date_in_future", 422)
    slots = await slots_service.list_slots(session, member, include_archived=True)
    if all(s.id != body.from_slot_id for s in slots):
        raise ApiError("meal_slot_not_found", 404)  # an archived slot is allowed
    sources = list(
        await session.scalars(
            select(MealLog)
            .where(
                MealLog.account_id == account_id,
                MealLog.member_id == member.id,
                MealLog.local_date == body.from_date,
                MealLog.meal_slot_id == body.from_slot_id,
            )
            .order_by(MealLog.eaten_at, MealLog.id)
        )
    )
    if not sources:
        raise ApiError("copy_source_empty", 422)
    if len(sources) > copy_service.COPY_MAX:
        raise ApiError("copy_too_many", 422)
    await _check_room(session, member)
    credits: list[str] = []
    for source in sources:
        for credit in meals_service._attributions(source):
            if credit not in credits:
                credits.append(credit)
    row = Favourite(
        account_id=account_id,
        member_id=member.id,
        kind="meal",
        name=body.name,  # user text: exactly as typed
        items=[copy_service.item_of(s) for s in sources],
        attributions=credits,
        client_id=body.client_id,
        created_at=core_time.now_utc(),
    )
    try:
        async with session.begin_nested():
            session.add(row)
            await session.flush()
    except IntegrityError as exc:
        constraint = getattr(getattr(exc.orig, "diag", None), "constraint_name", None)
        if body.client_id is None or constraint != CLIENT_ID_CONSTRAINT:
            raise
        await session.commit()
        won = await _by_client_id(session, account_id, body.client_id)
        if won is None:  # pragma: no cover
            raise
        return won, False
    await session.commit()
    await session.refresh(row)
    return row, True


async def delete_favourite(session: AsyncSession, account_id: UUID, favourite_id: UUID) -> None:
    row = await get_owned(session, account_id, favourite_id)
    await session.delete(row)
    await session.flush()


def _derived_id(client_id: UUID, favourite_id: UUID, index: int) -> UUID:
    return uuid5(client_id, f"{favourite_id}:{index}")


async def log_meal_favourite(
    session: AsyncSession,
    account_id: UUID,
    favourite_id: UUID,
    body: FavouriteLogIn,
    settings: Settings,
    *,
    now: datetime | None = None,
) -> tuple[list[MealLog], bool]:
    """(entries, created_any). Commits. Logs a favourite meal again from its snapshots, as a
    copy does. 404 `favourite_not_found`; 422 `validation_error` for a food favourite (one tap
    on a food goes through `meals_log`). Checks, in order: the date range (`date_in_future`,
    `date_too_old`), the entry time and the slot (`meal_slot_not_found`, `meal_slot_archived`),
    a retired dish (`food_retired`). Then the new entries are counted against `meal_logs`
    (only those not already stored) and inserted with ON CONFLICT DO NOTHING."""
    fav = await get_owned(session, account_id, favourite_id)
    if fav.kind != "meal" or fav.items is None:
        raise ApiError("validation_error", 422, details={"fields": ["path.favourite_id"]})
    member = await _member(session, account_id, fav.member_id, settings)
    items = fav.items
    ids = [_derived_id(body.client_id, fav.id, i) for i in range(len(items))]
    stored = await copy_service.read_back(session, account_id, ids)
    stored_ids = {r.client_id for r in stored}
    todo = [
        (i, item, cid)
        for i, (item, cid) in enumerate(zip(items, ids, strict=True))
        if cid not in stored_ids
    ]
    if not todo:
        return stored, False  # a retry: every entry exists, nothing is counted

    now = now or core_time.now_utc()
    tz_name = await me_service.account_timezone(session, account_id)
    today = core_time.local_today(tz_name, now)
    day = body.local_date
    if day is not None and day > today:
        raise ApiError("date_in_future", 422)
    if day is not None and day < today - timedelta(days=copy_service.MAX_TARGET_AGE_DAYS):
        raise ApiError("date_too_old", 422)
    if day is None or day == today:
        at = now
    else:  # Ruling E8: that date at the current local clock time, capped at now
        clock = core_time.local_clock(now, tz_name)
        at = min(now, datetime.combine(day, clock, tzinfo=core_time.zone(tz_name)))
    meals_service._check_eaten_at(at, now)
    slot = await slots_service.slot_for_entry(
        session, member, body.meal_slot_id, core_time.local_clock(at, tz_name)
    )
    local_date = core_time.local_date_of(at, tz_name)

    food_ids = {UUID(str(item["food_id"])) for _, item, _ in todo if item.get("food_id")}
    await copy_service.refuse_retired(session, food_ids)
    alive_custom = await _existing(
        session, CustomFood, account_id, {i["custom_food_id"] for _, i, _ in todo}
    )
    alive_recipes = await _existing(
        session, Recipe, account_id, {i["recipe_id"] for _, i, _ in todo}
    )

    await consume(session, settings, account_id=account_id, bucket="meal_logs", n=len(todo))
    values = []
    for index, item, cid in todo:
        item = dict(item)  # G21: a custom food or recipe that is gone logs with a NULL ref
        if item.get("custom_food_id") and str(item["custom_food_id"]) not in alive_custom:
            item["custom_food_id"] = None
        if item.get("recipe_id") and str(item["recipe_id"]) not in alive_recipes:
            item["recipe_id"] = None
        values.append(
            copy_service.entry_values(
                item,
                account_id=account_id,
                member_id=member.id,
                # The saved order is kept: each entry is one microsecond after the one before.
                at=at - timedelta(microseconds=len(items) - 1 - index),
                local_date=local_date,
                slot_id=slot.id,
                client_id=cid,
            )
        )
    result = await session.execute(
        insert(MealLog)
        .values(values)
        .on_conflict_do_nothing(index_elements=["account_id", "client_id"])
        .returning(MealLog.client_id)
    )
    created_any = bool(result.all())
    if (
        local_date == today
        and member.is_primary
        and await consents_service.has_active_consent(session, account_id, "health_data")
    ):
        await day_targets(session, member, today, today=today)  # today's frozen row exists
    await session.commit()
    return await copy_service.read_back(session, account_id, ids), created_any


async def _existing(session: AsyncSession, model, account_id: UUID, ids: set) -> set[str]:
    wanted = {UUID(str(i)) for i in ids if i}
    if not wanted:
        return set()
    rows = await session.scalars(
        select(model.id).where(model.account_id == account_id, model.id.in_(wanted))
    )
    return {str(r) for r in rows}


def _item_credits(item: dict) -> list[str]:
    snap = item.get("food_snapshot") or {}
    if snap.get("attributions") is not None:
        return list(snap["attributions"])
    if snap.get("attribution"):
        return [snap["attribution"]]
    return [meals_service.OFF_ATTRIBUTION] if item.get("off_barcode") else []


def to_out(row: Favourite) -> FavouriteOut:
    items = None
    if row.items is not None:
        items = [
            FavouriteItemOut(
                name=i.get("product_name"),
                quantity=None if i.get("quantity") is None else float(i["quantity"]),
                unit=i.get("unit"),
                grams=i.get("grams"),
                source_kind=i["source_kind"],
                attributions=_item_credits(i),
            )
            for i in row.items
        ]
    return FavouriteOut(
        id=row.id,
        member_id=row.member_id,
        kind=row.kind,  # type: ignore[arg-type]
        source_kind=row.source_kind,  # type: ignore[arg-type]
        product_id=row.product_id,
        barcode=row.off_barcode,
        food_id=row.food_id,
        custom_food_id=row.custom_food_id,
        recipe_id=row.recipe_id,
        name=row.name,
        default_quantity=None if row.default_quantity is None else float(row.default_quantity),
        default_unit=row.default_unit,
        item_count=1 if items is None else len(items),
        items=items,
        attributions=list(row.attributions or []),
        created_at=row.created_at,
    )
