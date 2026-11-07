"""Scan-to-log: nutrient snapshots, idempotent logging (offline sync), list and undo.

A log stores the nutrients of the portion eaten, computed at log time from the product's
per-100 g values. A value missing on the label stays null (never 0), and later product edits
never rewrite history. Member names and nutrients never go to logs.
"""

from dataclasses import replace
from datetime import date, datetime, time, timedelta
from decimal import ROUND_HALF_UP, Decimal
from uuid import UUID

from sqlalchemy import delete, func, select
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app import scoring
from app.core.config import Settings
from app.core.errors import ApiError
from app.core.time import IST, today_ist
from app.features.consents import service as consents_service
from app.features.diary.days import day_targets
from app.features.me import service as me_service
from app.features.meal_slots.defaults import DEFAULT_SLOTS
from app.features.meal_slots.models import MealSlot
from app.features.meals.models import MealLog
from app.features.meals.schemas import MealIn, MealOut, NutrientSnapshot, Summary, WeekCounts
from app.features.meals.summary import PERIOD_DAYS, annotate_protein, redact, summarise
from app.features.members import service as members_service
from app.features.products import service as products_service
from app.features.scans import service as scans_service
from app.features.targets import mapping as targets_mapping
from app.features.targets import service as targets_service
from app.integrations.openfoodfacts import OffClient
from app.scoring import targets as engine_targets

FUTURE_TOLERANCE = timedelta(minutes=5)
MAX_AGE = timedelta(days=30)
DEFAULT_LIST_DAYS = 7
CLIENT_ID_CONSTRAINT = "uq_meal_logs_account_id_client_id"
OFF_ATTRIBUTION = products_service.OFF_ATTRIBUTION


def _round1(value: float) -> float:
    return float(Decimal(repr(value)).quantize(Decimal("0.1"), rounding=ROUND_HALF_UP))


def _portion(value: float | None, grams: float) -> float | None:
    """value x grams / 100 in decimal arithmetic (10.016 x 250 / 100 is 25.04, not
    25.039999...), NOT rounded."""
    if value is None:
        return None
    return float(Decimal(repr(float(value))) * Decimal(repr(float(grams))) / 100)


def snapshot(per_100g: scoring.Nutrients, grams: float) -> NutrientSnapshot:
    """Nutrients in ``grams`` of the product, UNROUNDED (F1): this is what a log stores.

    Rounding happens only for display (``to_meal_out``, summary totals); the summary bands
    compare the unrounded sums, so 25.04 g of sugar is over a 25 g limit and 0.04 g of salt
    is over an infant's 0 g limit (rounded at log time, both read as within the limit).

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


def _display(value: float | None) -> float | None:
    return None if value is None else _round1(float(value))


def to_meal_out(row: MealLog) -> MealOut:
    """The API shape of a log. Nutrients are rounded to 1 dp (ROUND_HALF_UP) here, for
    display only; the stored snapshot stays unrounded (F1)."""
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
            **{k: _display(row.nutrients.get(k)) for k in NutrientSnapshot.model_fields}
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


async def _bridge_slot(session: AsyncSession, member, eaten_at: datetime) -> UUID:
    """TEMPORARY (Plan 11 Task 1 only; replaced by `slot_for_entry` in Tasks 2 and 4): the
    member's default slot for the IST clock minute of ``eaten_at``."""
    await session.execute(
        pg_insert(MealSlot)
        .values(
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
        .on_conflict_do_nothing()
    )
    local = eaten_at.astimezone(IST)
    minute = local.hour * 60 + local.minute
    for d in DEFAULT_SLOTS:
        s0, e0 = d.start.hour * 60 + d.start.minute, d.end.hour * 60 + d.end.minute
        if (s0 <= minute <= e0) if s0 <= e0 else (minute >= s0 or minute <= e0):
            key = d.label_key
            break
    return await session.scalar(
        select(MealSlot.id).where(MealSlot.member_id == member.id, MealSlot.label_key == key)
    )


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
        local_date=eaten_at.astimezone(IST).date(),
        source_kind="product" if found.product_id is not None else "off",
        meal_slot_id=await _bridge_slot(session, member, eaten_at),
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
    limit: int | None = 200,
) -> list[MealLog]:
    """The member's logs with start <= eaten_at < end, newest first. 404 for a foreign member.

    ``limit=None`` returns every log in the range (summaries must never drop meals).
    """
    await members_service.get_member(session, account_id, member_id)
    query = (
        select(MealLog)
        .where(
            MealLog.account_id == account_id,
            MealLog.member_id == member_id,
            MealLog.eaten_at >= start,
            MealLog.eaten_at < end,
        )
        .order_by(MealLog.eaten_at.desc(), MealLog.id)
    )
    if limit is not None:
        query = query.limit(limit)
    return list(await session.scalars(query))


async def list_meals_by_date(
    session: AsyncSession, account_id: UUID, member_id: UUID, start_day: date, end_day: date
) -> list[MealLog]:
    """The member's logs with start_day <= local_date <= end_day, newest first (no limit:
    summaries must never drop meals). The caller has checked the member."""
    query = (
        select(MealLog)
        .where(
            MealLog.account_id == account_id,
            MealLog.member_id == member_id,
            MealLog.local_date >= start_day,
            MealLog.local_date <= end_day,
        )
        .order_by(MealLog.eaten_at.desc(), MealLog.id)
    )
    return list(await session.scalars(query))


async def member_summary(
    session: AsyncSession,
    account_id: UUID,
    member_id: UUID,
    period: str,
    end_date: date | None = None,
) -> Summary:
    """The member's summary for the ``period`` ending on ``end_date`` (the account's local
    date; default today). 404 if foreign.

    Days group by the stored ``local_date``. Limits come from the engine (age from the birth
    year as of ``end_date``). The protein target comes from that day's frozen daily-targets row
    when the member has goal settings and `health_data` is active (Plan 10 Ruling D10; Plan 11
    Ruling E15); a past day with no row, or a future day, uses the legacy weight x g/kg rule.
    Numbers the member hid are redacted either way, consent or not (Ruling D11).
    """
    member = await members_service.get_member(session, account_id, member_id)
    today = await me_service.account_today(session, account_id)
    end_date = end_date or today
    n_days = PERIOD_DAYS[period]
    meals = await list_meals_by_date(
        session, account_id, member_id, end_date - timedelta(days=n_days - 1), end_date
    )
    scoring_member = members_service.to_scoring_member(member, today=end_date)
    limits = scoring.daily_limits_for(scoring_member, member.weight_kg)
    basis: str | None = None
    status: str | None = None
    row = await targets_service.get_settings(session, member)
    health_ok = await consents_service.has_active_consent(session, account_id, "health_data")
    if limits.protein_target_g is not None and member.weight_kg:
        # No daily-targets result: the SAME reference weight and caps as `targets.compute`
        # (lean mass, or the adjusted body weight at BMI >= 30, then the g/kg cap). Body fat is
        # health data, so it counts only while `health_data` is active.
        body = targets_service.body_data(member, end_date)
        if not health_ok:
            body = replace(body, body_fat_pct=None)
        sex_key = body.sex if body.sex in ("male", "female") else "average"
        ref = engine_targets.protein_reference(body, sex_key)
        basis = ref.basis
        limits = replace(
            limits, protein_target_g=float(ref.capped_g), protein_g_per_kg=float(ref.factor)
        )
    result = None
    if row is not None and health_ok and end_date <= today:
        result = await day_targets(session, member, end_date, today=today)
    if result is not None:
        status = result.status
        if result.status == "ready" and result.explanation is not None:
            basis = result.explanation.protein_basis
            limits = replace(
                limits,
                protein_target_g=float(result.protein_g),  # type: ignore[arg-type]
                protein_g_per_kg=float(result.explanation.protein_g_per_kg),
            )
        else:
            basis = None
            limits = replace(limits, protein_target_g=None, protein_g_per_kg=None)
    summary = annotate_protein(
        summarise(meals, limits, period, end_date, member_id=member.id), basis, status
    )
    hidden = targets_mapping.hidden_for(row.numbers_display) if row is not None else None  # type: ignore[arg-type]
    return summary if hidden is None else redact(summary, hidden)


async def week_counts(session: AsyncSession, account_id: UUID, end_date: date) -> WeekCounts:
    """Account-wide counts for the 7 IST days ending on ``end_date`` (weekly share text)."""
    start_day = end_date - timedelta(days=6)
    start, end = ist_day_bounds(start_day, end_date)
    return WeekCounts(
        start=start_day,
        end=end_date,
        scans=await scans_service.count_analyses(session, account_id, start, end),
        logged=await count_logs(session, account_id, start, end),
    )


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
