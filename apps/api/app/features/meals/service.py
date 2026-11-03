"""Scan-to-log: nutrient snapshots, idempotent logging (offline sync), list and undo.

A log stores the nutrients of the portion eaten, computed at log time from the product's
per-100 g values. A value missing on the label stays null (never 0), and later product edits
never rewrite history. Member names and nutrients never go to logs.
"""

from datetime import date, datetime, time, timedelta
from decimal import ROUND_HALF_UP, Decimal
from uuid import UUID

from sqlalchemy import delete, func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app import scoring
from app.core.config import Settings
from app.core.errors import ApiError
from app.core.time import IST, today_ist
from app.features.meals.models import MealLog
from app.features.meals.schemas import MealIn, MealOut, NutrientSnapshot
from app.features.members import service as members_service
from app.features.products import service as products_service
from app.integrations.openfoodfacts import OffClient

FUTURE_TOLERANCE = timedelta(minutes=5)
MAX_AGE = timedelta(days=30)
DEFAULT_LIST_DAYS = 7
CLIENT_ID_CONSTRAINT = "uq_meal_logs_account_id_client_id"
OFF_ATTRIBUTION = products_service.OFF_ATTRIBUTION


def _round1(value: float) -> float:
    return float(Decimal(repr(value)).quantize(Decimal("0.1"), rounding=ROUND_HALF_UP))


def _portion(value: float | None, grams: float) -> float | None:
    return None if value is None else _round1(value * grams / 100)


def snapshot(per_100g: scoring.Nutrients, grams: float) -> NutrientSnapshot:
    """Nutrients in ``grams`` of the product, each rounded to 1 dp (ROUND_HALF_UP).

    Implausible label values are dropped first (the engine's own sanitiser), so they are null
    here, never summed. None stays None. Salt comes from ``Nutrients.salt()`` (salt or
    sodium, the higher wins).
    """
    n, _ = per_100g.sanitized()
    return NutrientSnapshot(
        energy_kcal=_portion(n.energy_kcal, grams),
        sugars_g=_portion(n.sugars_g, grams),
        salt_g=_portion(n.salt(), grams),
        protein_g=_portion(n.protein_g, grams),
        fat_g=_portion(n.fat_g, grams),
        sat_fat_g=_portion(n.sat_fat_g, grams),
        carbs_g=_portion(n.carbs_g, grams),
    )


def ist_day_bounds(start_day: date, end_day: date) -> tuple[datetime, datetime]:
    """[start of ``start_day``, start of the day after ``end_day``) in IST."""
    start = datetime.combine(start_day, time.min, tzinfo=IST)
    end = datetime.combine(end_day + timedelta(days=1), time.min, tzinfo=IST)
    return start, end


def to_meal_out(row: MealLog) -> MealOut:
    return MealOut(
        id=row.id,
        member_id=row.member_id,
        product_id=row.product_id,
        barcode=row.off_barcode,
        product_name=row.product_name or "",
        grade=row.grade,  # type: ignore[arg-type]  (checked by ck_meal_logs_grade)
        grams=row.grams,
        eaten_at=row.eaten_at,
        nutrients=NutrientSnapshot(
            **{k: row.nutrients.get(k) for k in NutrientSnapshot.model_fields}
        ),
        client_id=row.client_id,
        attribution=OFF_ATTRIBUTION if row.off_barcode is not None else None,
    )


async def _by_client_id(session: AsyncSession, account_id: UUID, client_id: UUID) -> MealLog | None:
    return await session.scalar(
        select(MealLog).where(MealLog.account_id == account_id, MealLog.client_id == client_id)
    )


def _check_eaten_at(eaten_at: datetime, now: datetime) -> None:
    if eaten_at > now + FUTURE_TOLERANCE or eaten_at < now - MAX_AGE:
        raise ApiError("eaten_at_out_of_range", 422)


def _grams(body: MealIn, serving_size_g: float | None) -> float:
    if body.grams is not None:
        return body.grams
    if serving_size_g is None:
        raise ApiError("serving_size_unknown", 422)
    grams = (body.servings or 0) * serving_size_g
    if not 0 < grams <= 5000:
        raise ApiError("validation_error", 422, details={"fields": ["body.servings"]})
    return grams


async def log_meal(
    session: AsyncSession,
    account_id: UUID,
    body: MealIn,
    *,
    off: OffClient,
    settings: Settings,
    now: datetime | None = None,
) -> tuple[MealLog, bool]:
    """(row, created). Commits.

    A ``client_id`` already stored for the account returns that row (created=False) before
    anything else is checked, so an offline retry succeeds even if Open Food Facts is down.
    The member is checked before the product, so a foreign member never reaches OFF.
    """
    if body.client_id is not None:
        existing = await _by_client_id(session, account_id, body.client_id)
        if existing is not None:
            return existing, False

    now = now or datetime.now(IST)
    eaten_at = body.eaten_at or now
    _check_eaten_at(eaten_at, now)
    member = await members_service.get_member(session, account_id, body.member_id)
    found = await products_service.resolve_ref(
        session,
        off,
        product_id=body.product_id,
        barcode=body.barcode,
        settings=settings,
        account_id=account_id,
    )
    grams = _grams(body, found.product.serving_size_g)
    grade = scoring.analyze(found.product, []).report.nutriscore.grade
    row = MealLog(
        account_id=account_id,
        member_id=member.id,
        product_id=found.product_id,
        off_barcode=found.info.barcode if found.product_id is None else None,
        product_name=found.info.name,
        grade=grade,
        grams=grams,
        eaten_at=eaten_at,
        nutrients=snapshot(found.product.per_100g, grams).model_dump(),
        client_id=body.client_id,
    )
    try:
        async with session.begin_nested():
            session.add(row)
            await session.flush()
    except IntegrityError as exc:
        constraint = getattr(getattr(exc.orig, "diag", None), "constraint_name", None)
        if body.client_id is None or constraint != CLIENT_ID_CONSTRAINT:
            raise
        # A concurrent post with the same client_id won the race: return its row.
        await session.commit()  # keep the OFF cache write
        existing = await _by_client_id(session, account_id, body.client_id)
        if existing is None:  # pragma: no cover - the conflicting row was deleted meanwhile
            raise
        return existing, False
    await session.commit()
    await session.refresh(row)
    return row, True


def default_range(today: date | None = None) -> tuple[datetime, datetime]:
    """The last ``DEFAULT_LIST_DAYS`` IST days, today included."""
    today = today or today_ist()
    return ist_day_bounds(today - timedelta(days=DEFAULT_LIST_DAYS - 1), today)


async def list_meals(
    session: AsyncSession,
    account_id: UUID,
    member_id: UUID,
    start: datetime,
    end: datetime,
    limit: int = 200,
) -> list[MealLog]:
    """The member's logs with start <= eaten_at < end, newest first. 404 for a foreign member."""
    await members_service.get_member(session, account_id, member_id)
    rows = await session.scalars(
        select(MealLog)
        .where(
            MealLog.account_id == account_id,
            MealLog.member_id == member_id,
            MealLog.eaten_at >= start,
            MealLog.eaten_at < end,
        )
        .order_by(MealLog.eaten_at.desc(), MealLog.id)
        .limit(limit)
    )
    return list(rows)


async def delete_meal(session: AsyncSession, account_id: UUID, meal_id: UUID) -> None:
    """Undo a log (commits). 404 ``meal_not_found`` for unknown and foreign ids alike."""
    result = await session.execute(
        delete(MealLog).where(MealLog.account_id == account_id, MealLog.id == meal_id)
    )
    if result.rowcount == 0:
        raise ApiError("meal_not_found", 404)
    await session.commit()


async def count_logs(
    session: AsyncSession, account_id: UUID, start: datetime, end: datetime
) -> int:
    """All members' logs with start <= eaten_at < end (for the weekly share counts)."""
    count = await session.scalar(
        select(func.count())
        .select_from(MealLog)
        .where(
            MealLog.account_id == account_id,
            MealLog.eaten_at >= start,
            MealLog.eaten_at < end,
        )
    )
    return int(count or 0)
