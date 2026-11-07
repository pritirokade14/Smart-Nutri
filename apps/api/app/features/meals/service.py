"""Scan-to-log: nutrient snapshots, idempotent logging (offline sync), list and undo.

A log stores the nutrients of the portion eaten, computed at log time from the product's
per-100 g values. A value missing on the label stays null (never 0), and later product edits
never rewrite history. Member names and nutrients never go to logs.
"""

from collections.abc import Mapping, Sequence
from dataclasses import replace
from datetime import date, datetime, time, timedelta
from decimal import ROUND_HALF_UP, Decimal
from typing import Any
from uuid import UUID

from sqlalchemy import delete, func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app import scoring
from app.core import time as core_time
from app.core.config import Settings
from app.core.errors import ApiError
from app.core.time import IST, zone
from app.features.consents import service as consents_service
from app.features.diary.days import day_targets
from app.features.foods import resolve as foods_resolve
from app.features.foods import units as food_units
from app.features.me import service as me_service
from app.features.meal_slots import service as slots_service
from app.features.meals.models import MealLog
from app.features.meals.schemas import (
    MealIn,
    MealOut,
    MealPatch,
    NutrientSnapshot,
    PortionUnitOut,
    QuickIn,
    Summary,
    WeekCounts,
)
from app.features.meals.summary import PERIOD_DAYS, annotate_protein, redact, summarise
from app.features.members import service as members_service
from app.features.members.models import Member
from app.features.products import service as products_service
from app.features.scans import service as scans_service
from app.features.targets import mapping as targets_mapping
from app.features.targets import service as targets_service
from app.features.targets.schemas import NumbersHidden
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
        fibre_g=_portion(n.fiber_g, grams),
    )


NUTRIENT_KEYS = tuple(NutrientSnapshot.model_fields)


def food_snapshot(
    info_name: str,
    brand: str | None,
    per_100g: scoring.Nutrients,
    serving_g: float | None,
    attribution: str | None,
    *,
    basis: str = "g",
    units: Mapping[str, float] | None = None,
    attributions: Sequence[str] | None = None,
    licence: str | None = None,
    source: str | None = None,
    unit_sources: Mapping[str, str] | None = None,
) -> dict[str, Any]:
    """The food as it was at log time (spec 5.1 `food_snapshot`): an edit recomputes from THIS,
    never from the product row, a user override or the seed, so a later edit never rewrites
    history. ``per_100`` is after the engine's sanitiser, with salt from salt or sodium (the
    higher wins). Unrounded. ``units`` holds every unit that resolved at log time (code ->
    grams, or ml, per unit); without it, just the serving. ``unit_sources`` says how each unit
    was converted (`grams`, `portion` or `density`), so an edit keeps the "approximate" marker."""
    n, _ = per_100g.sanitized()
    return {
        "name": info_name,
        "brand": brand,
        "basis": basis,
        "per_100": {
            "energy_kcal": n.energy_kcal,
            "sugars_g": n.sugars_g,
            "salt_g": n.salt(),
            "protein_g": n.protein_g,
            "fat_g": n.fat_g,
            "sat_fat_g": n.sat_fat_g,
            "carbs_g": n.carbs_g,
            "fibre_g": n.fiber_g,
        },
        "units": dict(units)
        if units is not None
        else ({"serving": serving_g} if serving_g else {}),
        "attribution": attribution,
        "attributions": list(attributions)
        if attributions is not None
        else ([attribution] if attribution else []),
        "licence": licence,
        "source": source,
        "unit_sources": dict(unit_sources) if unit_sources is not None else {},
    }


def unit_source_label(
    source: str, basis: str, *, recipe: bool = False, code: str | None = None
) -> str:
    """The client-facing kind of a resolved unit's conversion: `portion` (a per-food weight),
    `density` (a volume through a density, which includes grams of an ml-basis food), else
    `grams` (exact: a mass, a millilitre of an ml-basis food, or a label serving). A household
    volume on an ml-basis food (`volume_basis`) is a nominal volume: approximate (`density`). A
    recipe's per-serving portion is cooked weight / servings: approximate (`portion`)."""
    if recipe and source == "serving":
        return "portion"
    if source in ("portion_user", "portion_global"):
        return "portion"
    if source == "volume_basis" and code != "ml":
        return "density"  # katori, cup, glass...: a nominal volume (plain `ml` stays exact)
    if source == "density" or (source == "mass" and basis == "ml"):
        return "density"
    return "grams"


def per_100_of(row: MealLog) -> dict[str, float | None]:
    """Per 100 g of the entry's food: its `food_snapshot.per_100`, or, for a legacy row,
    nutrients x 100 / grams (the exact inverse, in Decimal)."""
    if row.food_snapshot is not None:
        per_100 = row.food_snapshot["per_100"]
        return {k: per_100.get(k) for k in NUTRIENT_KEYS}
    grams = Decimal(repr(float(row.grams or 0)))
    out: dict[str, float | None] = {}
    for k in NUTRIENT_KEYS:
        value = (row.nutrients or {}).get(k)
        out[k] = (
            None if value is None or not grams else float(Decimal(repr(float(value))) * 100 / grams)
        )
    return out


def ist_day_bounds(start_day: date, end_day: date) -> tuple[datetime, datetime]:
    """[start of ``start_day``, start of the day after ``end_day``) in IST."""
    start = datetime.combine(start_day, time.min, tzinfo=IST)
    end = datetime.combine(end_day + timedelta(days=1), time.min, tzinfo=IST)
    return start, end


def _display(value: float | None) -> float | None:
    return None if value is None else _round1(float(value))


_UNIT_SORT = {u.code: u.sort for u in food_units.table_from_yaml().values()}


def _snapshot_units(row: MealLog) -> dict[str, float]:
    """The units that resolved when the entry was logged: its saved food's `units`, plus grams
    for a gram-basis food (always resolvable; older snapshots did not list it)."""
    snap = row.food_snapshot
    if snap is None:  # a legacy product entry (grams are always resolvable) or a quick add
        return {} if row.source_kind == "quick_add" else {"g": 1.0}
    units = {k: float(v) for k, v in (snap.get("units") or {}).items() if v}
    if snap.get("basis", "g") == "g":
        units.setdefault("g", 1.0)
    return units


def _unit_source(row: MealLog) -> str | None:
    """How the entry's unit was converted (`grams`, `portion` or `density`); null when unknown
    (older entries, quick adds, or a unit the saved food did not record)."""
    if row.unit is None or row.source_kind == "quick_add":
        return None
    snap = row.food_snapshot or {}
    recorded = (snap.get("unit_sources") or {}).get(row.unit)
    if recorded is not None:
        return recorded
    if snap.get("basis", "g") == "g" and row.unit in ("g", "serving"):
        return "grams"  # an exact unit, recorded or not
    return None


def _portion_units(row: MealLog) -> list[PortionUnitOut]:
    units = _snapshot_units(row)
    return [
        PortionUnitOut(code=c, grams_per_unit=units[c])
        for c in sorted(units, key=lambda c: (_UNIT_SORT.get(c, 999), c))
    ]


def _attributions(row: MealLog) -> list[str]:
    snap = row.food_snapshot
    if snap is not None and snap.get("attributions") is not None:
        return list(snap["attributions"])
    if snap is not None and snap.get("attribution"):
        return [snap["attribution"]]
    return [OFF_ATTRIBUTION] if row.off_barcode is not None else []


def to_meal_out(row: MealLog, hidden: NumbersHidden | None = None) -> MealOut:
    """The API shape of a log. Nutrients are rounded to 1 dp (ROUND_HALF_UP) here, for
    display only; the stored snapshot stays unrounded (F1).

    Ruling E21: every MealOut is redacted with its member's display setting. ``hide_energy``
    nulls ``energy_kcal``; ``hide_all`` nulls every nutrient. Portions and ``incomplete`` (which
    nutrients are unknown, computed from the stored values) stay."""
    raw = row.nutrients or {}
    nutrients = {k: _display(raw.get(k)) for k in NUTRIENT_KEYS}
    if hidden is not None and hidden.energy:
        nutrients["energy_kcal"] = None
    if hidden is not None and hidden.macros:
        nutrients = dict.fromkeys(NUTRIENT_KEYS)
    return MealOut(
        id=row.id,
        member_id=row.member_id,
        product_id=row.product_id,
        barcode=row.off_barcode,
        product_name=row.product_name or "",
        grade=row.grade,  # type: ignore[arg-type]  (checked by ck_meal_logs_grade)
        grams=row.grams,
        eaten_at=row.eaten_at,
        nutrients=NutrientSnapshot(**nutrients),
        client_id=row.client_id,
        attribution=OFF_ATTRIBUTION if OFF_ATTRIBUTION in _attributions(row) else None,
        source_kind=row.source_kind,  # type: ignore[arg-type]  (checked by ck_meal_logs_source_kind)
        meal_slot_id=row.meal_slot_id,
        local_date=row.local_date,
        incomplete=[k for k in NUTRIENT_KEYS if raw.get(k) is None],
        updated_at=row.updated_at,
        food_id=row.food_id,
        custom_food_id=row.custom_food_id,
        recipe_id=row.recipe_id,
        quantity=None if row.quantity is None else float(row.quantity),
        unit=row.unit,
        unit_source=_unit_source(row),  # type: ignore[arg-type]
        basis=(row.food_snapshot or {}).get("basis", "g"),  # type: ignore[arg-type]
        attributions=_attributions(row),
        portion_units=_portion_units(row),
    )


async def hidden_for_member(session: AsyncSession, member: Member) -> NumbersHidden:
    """What the member hid with the eye toggle (their settings row; none means nothing hidden)."""
    row = await targets_service.get_settings(session, member)
    if row is None:
        return NumbersHidden(energy=False, macros=False)
    return targets_mapping.hidden_for(row.numbers_display)  # type: ignore[arg-type]


async def _by_client_id(session: AsyncSession, account_id: UUID, client_id: UUID) -> MealLog | None:
    return await session.scalar(
        select(MealLog).where(MealLog.account_id == account_id, MealLog.client_id == client_id)
    )


def _check_eaten_at(eaten_at: datetime, now: datetime) -> None:
    if eaten_at > now + FUTURE_TOLERANCE or eaten_at < now - MAX_AGE:
        raise ApiError("eaten_at_out_of_range", 422)


def _grams_from(grams: float | None, servings: float | None, serving_size_g: float | None) -> float:
    if grams is not None:
        return grams
    if serving_size_g is None:
        raise ApiError("serving_size_unknown", 422)
    out = (servings or 0) * serving_size_g
    if not 0 < out <= 5000:
        raise ApiError("validation_error", 422, details={"fields": ["body.servings"]})
    return out


def _portion_of(
    body: MealIn, loaded: foods_resolve.LoadedFood, table: dict[str, food_units.Unit]
) -> tuple[float, Decimal, str]:
    """(amount in the food's basis, quantity, unit code) of a log. ``grams`` and ``servings``
    keep their exact legacy behaviour (bounds, `serving_size_unknown`); ``quantity`` + ``unit``
    goes through `to_grams`, which refuses to guess: 422 `unit_grams_unknown`,
    `quantity_out_of_range`. Every new entry stores a quantity and a unit."""
    if body.quantity is not None:
        quantity = Decimal(repr(body.quantity))
        amount = food_units.portion_amount(quantity, body.unit or "", loaded.units, table)
        return float(amount), quantity, body.unit or ""
    if body.grams is not None:
        quantity = Decimal(repr(body.grams))
        if loaded.basis == "ml":  # grams of an ml-basis food need a density
            return (
                float(food_units.portion_amount(quantity, "g", loaded.units, table)),
                quantity,
                "g",
            )
        return body.grams, quantity, "g"
    serving = loaded.units.serving_g
    grams = _grams_from(None, body.servings, None if serving is None else float(serving))
    return grams, Decimal(repr(body.servings)), "serving"


def _quick_nutrients(quick: QuickIn) -> dict[str, float | None]:
    """The stored nutrients of a quick add: sugars, saturated fat and salt are unknown."""
    return {
        "energy_kcal": quick.energy_kcal,
        "sugars_g": None,
        "salt_g": None,
        "protein_g": quick.protein_g,
        "fat_g": quick.fat_g,
        "sat_fat_g": None,
        "carbs_g": quick.carbs_g,
        "fibre_g": quick.fibre_g,
    }


async def _member_for_log(
    session: AsyncSession, account_id: UUID, member_id: UUID | None
) -> Member:
    """None -> the primary; any member of the account is accepted (family logging, Ruling E9)."""
    if member_id is None:
        return await members_service.get_or_create_primary(session, account_id)
    return await members_service.get_member(session, account_id, member_id)


def _eaten_at_for(body: MealIn, now: datetime, tz_name: str, today: date) -> datetime:
    """Ruling E8: ``local_date`` -> that date at the current local clock time, capped at now."""
    if body.eaten_at is not None:
        return body.eaten_at
    if body.local_date is None or body.local_date == today:
        return now
    if body.local_date > today:
        raise ApiError("date_in_future", 422)
    clock = core_time.local_clock(now, tz_name)
    return min(now, datetime.combine(body.local_date, clock, tzinfo=zone(tz_name)))


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
    Then, in order: the member (a foreign member never reaches OFF), the account zone,
    ``eaten_at`` and its range check, the slot (the server's pick when none is sent), the
    local date, the food (a product, an OFF barcode or a quick add), and, for today with
    `health_data` active, today's frozen target row (Ruling E5).
    """
    if body.client_id is not None:
        existing = await _by_client_id(session, account_id, body.client_id)
        if existing is not None:
            return existing, False

    now = now or core_time.now_utc()
    member = await _member_for_log(session, account_id, body.member_id)
    tz_name = await me_service.account_timezone(session, account_id)
    today = core_time.local_today(tz_name, now)
    eaten_at = _eaten_at_for(body, now, tz_name, today)
    _check_eaten_at(eaten_at, now)
    slot = await slots_service.slot_for_entry(
        session, member, body.meal_slot_id, core_time.local_clock(eaten_at, tz_name)
    )
    local_date = core_time.local_date_of(eaten_at, tz_name)

    common: dict[str, Any] = {
        "account_id": account_id,
        "member_id": member.id,
        "eaten_at": eaten_at,
        "client_id": body.client_id,
        "local_date": local_date,
        "meal_slot_id": slot.id,
    }
    if body.quick is not None:
        row = MealLog(
            **common,
            source_kind="quick_add",
            product_id=None,
            off_barcode=None,
            product_name=body.quick.name,
            grade=None,
            grams=None,
            nutrients=_quick_nutrients(body.quick),
            food_snapshot=None,
        )
    else:
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
        if loaded.retired:  # readable (old entries keep working) but never logged anew
            raise ApiError("food_retired", 422)
        table = await foods_resolve.unit_table(session)
        grams, quantity, unit_code = _portion_of(body, loaded, table)
        resolved = food_units.resolve_units(loaded.units, table)
        units = {r.code: float(r.grams_per_unit) for r in resolved}
        unit_sources = {
            r.code: unit_source_label(
                r.source, loaded.basis, recipe=loaded.ref.kind == "recipe", code=r.code
            )
            for r in resolved
        }
        serving = loaded.units.serving_g
        row = MealLog(
            **common,
            source_kind=(
                "food" if loaded.food_id is not None
                else "custom_food" if loaded.ref.kind == "custom_food"
                else "recipe" if loaded.ref.kind == "recipe"
                else "product" if loaded.product_id is not None
                else "off"
            ),
            product_id=loaded.product_id,
            off_barcode=loaded.off_barcode,
            food_id=loaded.food_id,
            custom_food_id=loaded.custom_food_id,
            recipe_id=loaded.recipe_id,
            product_name=loaded.name,
            grade=loaded.grade,
            grams=grams,
            quantity=quantity,
            unit=unit_code,
            nutrients=snapshot(loaded.per_100, grams).model_dump(),
            food_snapshot=food_snapshot(
                loaded.name,
                loaded.brand,
                loaded.per_100,
                None if serving is None else float(serving),
                loaded.attribution,
                basis=loaded.basis,
                units=units,
                attributions=loaded.attributions,
                licence=loaded.licence,
                source=loaded.source,
                unit_sources=unit_sources,
            ),
        )  # fmt: skip
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
    if (
        local_date == today
        and member.is_primary
        and await consents_service.has_active_consent(session, account_id, "health_data")
    ):
        await day_targets(session, member, today, today=today)  # today's frozen row exists
    await session.commit()
    await session.refresh(row)
    return row, True


def _patch_portion(
    row: MealLog, patch: MealPatch, *, quantity: float | None = None, unit: str | None = None
) -> tuple[float, Decimal, str]:
    """A new quantity + unit, converted ONLY from the entry's own saved units (the ones that
    resolved when it was logged): a later portion override, density or reseed never rewrites
    history, and a unit that did not resolve then is 422 `unit_grams_unknown`. ``quantity`` and
    ``unit`` override the patch's own (a grams patch on an ml-basis entry converts as `g`)."""
    unit_code = unit if unit is not None else patch.unit or ""
    per_unit = _snapshot_units(row).get(unit_code)
    if per_unit is None:
        raise ApiError("unit_grams_unknown", 422, details={"unit": unit_code})
    qty = Decimal(repr(quantity if quantity is not None else patch.quantity))
    cap = food_units.MAX_AMOUNT if unit_code in ("g", "ml") else food_units.MAX_QUANTITY
    amount = qty * Decimal(repr(per_unit))
    if not 0 < qty <= cap or not 0 < amount <= food_units.MAX_AMOUNT:
        raise ApiError("quantity_out_of_range", 422)
    return float(amount), qty, unit_code


async def update_meal(
    session: AsyncSession,
    account_id: UUID,
    meal_id: UUID,
    patch: MealPatch,
    *,
    settings: Settings | None = None,
    now: datetime | None = None,
) -> MealLog:
    """Edit an entry (Ruling E10: null = unchanged). Never commits.

    The entry is the account's, else 404 `meal_not_found`; another member's entry is 422
    `diary_member_not_enabled` while Family is off. A new portion recomputes the nutrients from
    the entry's own `food_snapshot` (or, for a legacy row, the exact inverse), never from the
    product row. A new `eaten_at` passes the range check and recomputes `local_date` in the
    CURRENT account zone. A new slot goes through `slot_for_entry`. `quick` replaces a quick
    add's values. `updated_at` is bumped. No other `meal_logs` row and no `diary_days` row is
    written.
    """
    row = await session.scalar(
        select(MealLog).where(MealLog.account_id == account_id, MealLog.id == meal_id)
    )
    if row is None:
        raise ApiError("meal_not_found", 404)
    member = await members_service.get_member(session, account_id, row.member_id)
    if not member.is_primary and not (settings is not None and settings.diary_family_enabled):
        raise ApiError("diary_member_not_enabled", 422)
    now = now or core_time.now_utc()
    tz_name = await me_service.account_timezone(session, account_id)

    if patch.quick is not None:
        if row.source_kind != "quick_add":
            raise ApiError("validation_error", 422, details={"fields": ["body.quick"]})
        row.product_name = patch.quick.name
        row.nutrients = _quick_nutrients(patch.quick)
    if patch.grams is not None or patch.servings is not None or patch.quantity is not None:
        if row.source_kind == "quick_add":
            field = next(f for f in ("grams", "servings", "quantity") if getattr(patch, f))
            raise ApiError("validation_error", 422, details={"fields": [f"body.{field}"]})
        if patch.quantity is not None:
            grams, quantity, unit_code = _patch_portion(row, patch)
        elif patch.grams is not None and (row.food_snapshot or {}).get("basis", "g") == "ml":
            # Grams of an ml-basis food are never millilitres: convert through the density the
            # entry was logged with (its saved `g` unit), or refuse (422 `unit_grams_unknown`).
            grams, quantity, unit_code = _patch_portion(row, patch, quantity=patch.grams, unit="g")
        elif patch.grams is not None:
            serving = ((row.food_snapshot or {}).get("units") or {}).get("serving")
            grams = _grams_from(patch.grams, None, serving)
            quantity, unit_code = Decimal(repr(patch.grams)), "g"
        else:
            serving = ((row.food_snapshot or {}).get("units") or {}).get("serving")
            grams = _grams_from(None, patch.servings, serving)
            quantity, unit_code = Decimal(repr(patch.servings)), "serving"
        per_100 = per_100_of(row)
        row.nutrients = {k: _portion(per_100[k], grams) for k in NUTRIENT_KEYS}
        row.grams = grams
        row.quantity = quantity
        row.unit = unit_code
    if patch.eaten_at is not None:
        _check_eaten_at(patch.eaten_at, now)
        row.eaten_at = patch.eaten_at
        row.local_date = core_time.local_date_of(patch.eaten_at, tz_name)
    if patch.meal_slot_id is not None:
        slot = await slots_service.slot_for_entry(
            session, member, patch.meal_slot_id, core_time.local_clock(row.eaten_at, tz_name)
        )
        row.meal_slot_id = slot.id
    row.updated_at = now
    await session.flush()
    return row


async def default_range(session: AsyncSession, account_id: UUID) -> tuple[datetime, datetime]:
    """The last ``DEFAULT_LIST_DAYS`` local days, today included, in the account's zone."""
    tz_name = await me_service.account_timezone(session, account_id)
    today = core_time.local_today(tz_name)
    return core_time.local_day_bounds(today - timedelta(days=DEFAULT_LIST_DAYS - 1), today, tz_name)


async def member_for_list(
    session: AsyncSession, account_id: UUID, member_id: UUID | None
) -> Member:
    """None -> the primary (created on first use); any member of the account otherwise."""
    return await _member_for_log(session, account_id, member_id)


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
