"""Custom foods CRUD (Plan 12 Task 11; spec 5.8; G15, G18, G21). No FastAPI imports.

The account's own foods only: every query is scoped by account, another account's id is 404
`custom_food_not_found`. Never reads or feeds the public catalogue, `products` or `analyze`.
Values are stored per 100 g/ml in `Decimal`-exact arithmetic (12 g per 30 g serving is 40
per 100), a blank stays absent (unknown), and the stored values pass the engine's
plausibility rules. Names and values never go to logs.
"""

import base64
import json
from datetime import datetime
from decimal import Decimal
from uuid import UUID

from sqlalchemy import and_, delete, or_, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import ApiError
from app.features.custom_foods.models import CustomFood
from app.features.custom_foods.schemas import (
    NUTRIENT_FIELDS,
    CustomFoodIn,
    CustomFoodOut,
    CustomNutrientsIn,
    CustomPortionOut,
    EnteredOut,
)
from app.features.foods import recipe_math
from app.features.foods.models import FoodPortion
from app.features.foods.resolve import unit_table
from app.features.meals.schemas import NutrientSnapshot
from app.features.scans.normalize import implausible_fields
from app.integrations.openfoodfacts import InvalidBarcode, normalize_barcode
from app.scoring import Nutrients

BARCODE_CONSTRAINT = "uq_custom_foods_account_id_barcode"
CLIENT_ID_CONSTRAINT = "uq_custom_foods_account_id_client_id"
_ENGINE_NAME = {"fibre_g": "fiber_g"}  # the engine spells fibre `fiber_g`
_API_NAME = {v: k for k, v in _ENGINE_NAME.items()}


def _dec(value: float) -> Decimal:
    return Decimal(repr(value))


def entered_nutrients(body: CustomFoodIn) -> dict[str, float]:
    """Only what was typed (a blank is absent), as typed, with the API's field names."""
    return {k: v for k in NUTRIENT_FIELDS if (v := getattr(body.nutrients, k)) is not None}


def nutrients_known(typed: dict[str, float]) -> bool:
    """Energy, or at least one of protein, carbs and fat, must be known."""
    return any(k in typed for k in ("energy_kcal", "protein_g", "carbs_g", "fat_g"))


def per_100_of(body: CustomFoodIn) -> dict[str, float]:
    """The typed values per 100 g/ml (engine field names). ``serving``: value x 100 / serving_g
    in Decimal. Absent stays absent."""
    typed = entered_nutrients(body)
    scale = Decimal(100) / _dec(body.serving_g) if body.values_per == "serving" else Decimal(1)  # type: ignore[arg-type]
    out: dict[str, float] = {}
    for key, value in typed.items():
        out[_ENGINE_NAME.get(key, key)] = float(_dec(value) * scale)
    return out


def validate_values(body: CustomFoodIn) -> dict[str, float]:
    """The per-100 values to store, or 422 `custom_food_nutrients_empty` / `implausible_value`
    (the engine's own plausibility rules; the offending fields in `details.fields`)."""
    if not nutrients_known(entered_nutrients(body)):
        raise ApiError("custom_food_nutrients_empty", 422)
    per_100 = per_100_of(body)
    bad = implausible_fields(per_100, serving_size_g=None)  # type: ignore[arg-type]
    if bad:
        raise ApiError(
            "implausible_value",
            422,
            details={"fields": [f"body.nutrients.{_API_NAME.get(f, f)}" for f in bad]},
        )
    return per_100


def clean_barcode(raw: str | None) -> str | None:
    if raw is None or not raw.strip():
        return None
    try:
        return normalize_barcode(raw)
    except InvalidBarcode:
        raise ApiError("invalid_barcode", 422) from None


def snapshot_of(per_100: dict[str, float]) -> NutrientSnapshot:
    """Per-100 values in the diary's keys (salt from salt or sodium, the higher wins)."""
    nutrients = Nutrients(
        **{k: per_100.get(k) for k in Nutrients.__dataclass_fields__ if k in per_100}
    )
    return NutrientSnapshot(
        **{
            k: (None if v is None else float(v))
            for k, v in recipe_math.snapshot_per_100(nutrients).items()
        }
    )


async def _portion_rows(session: AsyncSession, food: CustomFood) -> list[CustomPortionOut]:
    table = await unit_table(session)
    rows = await session.scalars(
        select(FoodPortion).where(
            FoodPortion.custom_food_id == food.id, FoodPortion.account_id == food.account_id
        )
    )
    ordered = sorted(rows, key=lambda r: (table[r.unit].sort if r.unit in table else 999, r.unit))
    return [CustomPortionOut(unit=r.unit, grams_per_unit=float(r.grams_per_unit)) for r in ordered]


async def to_out(session: AsyncSession, food: CustomFood) -> CustomFoodOut:
    entered = food.entered or {}
    typed = entered.get("nutrients") or {}
    return CustomFoodOut(
        id=food.id,
        name=food.name,
        brand=food.brand,
        basis=food.basis,  # type: ignore[arg-type]
        per_100=snapshot_of(food.per_100),
        entered=EnteredOut(
            values_per=entered.get("values_per", "100"),
            serving_g=entered.get("serving_g"),
            nutrients=CustomNutrientsIn(**{k: typed.get(k) for k in NUTRIENT_FIELDS}),
        ),
        serving_g=None if food.serving_g is None else float(food.serving_g),
        density_g_per_ml=None if food.density_g_per_ml is None else float(food.density_g_per_ml),
        barcode=food.barcode,
        portions=await _portion_rows(session, food),
        created_at=food.created_at,
        updated_at=food.updated_at,
    )


async def get_owned(session: AsyncSession, account_id: UUID, food_id: UUID) -> CustomFood:
    row = await session.scalar(
        select(CustomFood)
        .where(CustomFood.id == food_id, CustomFood.account_id == account_id)
        .execution_options(populate_existing=True)
    )
    if row is None:
        raise ApiError("custom_food_not_found", 404)
    return row


async def _barcode_taken(
    session: AsyncSession, account_id: UUID, barcode: str | None, *, except_id: UUID | None = None
) -> bool:
    if barcode is None:
        return False
    query = select(CustomFood.id).where(
        CustomFood.account_id == account_id, CustomFood.barcode == barcode
    )
    if except_id is not None:
        query = query.where(CustomFood.id != except_id)
    return await session.scalar(query) is not None


def _serving_basis(body: CustomFoodIn) -> Decimal | None:
    return None if body.serving_g is None else _dec(body.serving_g)


def _values(body: CustomFoodIn, per_100: dict[str, float], barcode: str | None) -> dict:
    return {
        "name": body.name,
        "brand": body.brand,
        "basis": body.basis,
        "per_100": per_100,
        "entered": {
            "values_per": body.values_per,
            "serving_g": body.serving_g,
            "nutrients": entered_nutrients(body),
        },
        "serving_g": _serving_basis(body),
        "density_g_per_ml": None if body.density_g_per_ml is None else _dec(body.density_g_per_ml),
        "barcode": barcode,
    }


async def _replace_portions(session: AsyncSession, food: CustomFood, body: CustomFoodIn) -> None:
    table = await unit_table(session)
    for portion in body.portions:
        unit = table.get(portion.unit)
        if unit is None or unit.kind == "mass" or unit.code == "serving":
            raise ApiError("unit_not_supported", 422, details={"unit": portion.unit})
    await session.execute(
        delete(FoodPortion).where(
            FoodPortion.custom_food_id == food.id, FoodPortion.account_id == food.account_id
        )
    )
    for portion in body.portions:
        session.add(
            FoodPortion(
                account_id=food.account_id,
                custom_food_id=food.id,
                unit=portion.unit,
                grams_per_unit=_dec(portion.grams_per_unit),
                source="user",
            )
        )
    await session.flush()


def _constraint(exc: IntegrityError) -> str | None:
    return getattr(getattr(exc.orig, "diag", None), "constraint_name", None)


async def create_food(
    session: AsyncSession, account_id: UUID, body: CustomFoodIn
) -> tuple[CustomFood, bool]:
    """(row, created). A ``client_id`` already stored returns that row (created=False) before
    anything is validated, so an offline retry succeeds. Does not commit."""
    if body.client_id is not None:
        stored = await _by_client_id(session, account_id, body.client_id)
        if stored is not None:
            return stored, False
    per_100 = validate_values(body)
    barcode = clean_barcode(body.barcode)
    if await _barcode_taken(session, account_id, barcode):
        raise ApiError("barcode_already_used", 422)
    now = datetime_now()  # one clock for created_at and updated_at (the list order)
    row = CustomFood(
        account_id=account_id,
        client_id=body.client_id,
        created_at=now,
        updated_at=now,
        **_values(body, per_100, barcode),
    )
    try:
        async with session.begin_nested():
            session.add(row)
            await session.flush()
    except IntegrityError as exc:
        name = _constraint(exc)
        if name == BARCODE_CONSTRAINT:
            raise ApiError("barcode_already_used", 422) from None
        if name != CLIENT_ID_CONSTRAINT or body.client_id is None:
            raise
        # A concurrent post with the same client_id won the race: return its row.
        stored = await _by_client_id(session, account_id, body.client_id)
        if stored is None:  # pragma: no cover - deleted meanwhile
            raise
        return stored, False
    await _replace_portions(session, row, body)
    return row, True


async def _by_client_id(
    session: AsyncSession, account_id: UUID, client_id: UUID
) -> CustomFood | None:
    return await session.scalar(
        select(CustomFood)
        .where(CustomFood.account_id == account_id, CustomFood.client_id == client_id)
        .execution_options(populate_existing=True)
    )


async def update_food(
    session: AsyncSession, account_id: UUID, food_id: UUID, body: CustomFoodIn
) -> CustomFood:
    """Full replace (G18): a nutrient left out becomes unknown, the portions are replaced. A past
    diary entry keeps its own snapshot. Does not commit."""
    row = await get_owned(session, account_id, food_id)
    per_100 = validate_values(body)
    barcode = clean_barcode(body.barcode)
    if await _barcode_taken(session, account_id, barcode, except_id=row.id):
        raise ApiError("barcode_already_used", 422)
    for key, value in _values(body, per_100, barcode).items():
        setattr(row, key, value)
    row.updated_at = datetime_now()
    try:
        async with session.begin_nested():
            await session.flush()
    except IntegrityError as exc:
        if _constraint(exc) == BARCODE_CONSTRAINT:
            raise ApiError("barcode_already_used", 422) from None
        raise
    await _replace_portions(session, row, body)
    return row


def datetime_now() -> datetime:
    from app.core import time as core_time

    return core_time.now_utc()


async def delete_food(session: AsyncSession, account_id: UUID, food_id: UUID) -> None:
    """Delete (G21): entries and recipe ingredients keep their snapshot with the ref set NULL,
    portions go with it. 404 for an unknown or foreign id. Does not commit."""
    row = await get_owned(session, account_id, food_id)
    await session.delete(row)
    await session.flush()


# ---- list: an opaque cursor over (updated_at desc, id desc)


def encode_cursor(updated_at: datetime, food_id: UUID) -> str:
    raw = json.dumps({"t": updated_at.isoformat(), "i": str(food_id)}).encode()
    return base64.urlsafe_b64encode(raw).decode()


def decode_cursor(cursor: str) -> tuple[datetime, UUID]:
    try:
        data = json.loads(base64.urlsafe_b64decode(cursor.encode()))
        return datetime.fromisoformat(data["t"]), UUID(data["i"])
    except (ValueError, KeyError, TypeError):
        raise ApiError("validation_error", 422, details={"fields": ["query.cursor"]}) from None


async def list_foods(
    session: AsyncSession, account_id: UUID, limit: int, cursor: str | None
) -> tuple[list[CustomFood], str | None]:
    query = select(CustomFood).where(CustomFood.account_id == account_id)
    if cursor is not None:
        at, last_id = decode_cursor(cursor)
        query = query.where(
            or_(
                CustomFood.updated_at < at,
                and_(CustomFood.updated_at == at, CustomFood.id < last_id),
            )
        )
    rows = list(
        await session.scalars(
            query.order_by(CustomFood.updated_at.desc(), CustomFood.id.desc()).limit(limit + 1)
        )
    )
    page = rows[:limit]
    more = encode_cursor(page[-1].updated_at, page[-1].id) if len(rows) > limit else None
    return page, more
