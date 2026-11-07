"""Foods: search, detail with the units that resolve, and the account's portion overrides
(Plan 12 Task 4). No FastAPI imports.

Search never returns nutrients. The detail lists ONLY units that resolve (a unit with nothing
to convert it by is never offered) and redacts the per-100 values with the member's numbers
display. A portion override belongs to the account and never rewrites a past diary entry (the
entry keeps its own `food_snapshot`).
"""

import re
from decimal import Decimal
from uuid import UUID

from sqlalchemy import or_, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings
from app.core.errors import ApiError
from app.features.custom_foods.models import CustomFood
from app.features.foods import recipe_math
from app.features.foods.models import Food, FoodPortion
from app.features.foods.resolve import FoodRef, LoadedFood, load_food, unit_table
from app.features.foods.schemas import (
    DishIngredientOut,
    DishOut,
    FoodDetailOut,
    FoodHit,
    FoodSearchOut,
    FoodUnitOut,
    SearchKind,
    UnitOut,
)
from app.features.foods.units import Unit, default_unit, resolve_units, settable_units
from app.features.meals.schemas import NutrientSnapshot
from app.features.products import search as products_search
from app.features.recipes.models import Recipe
from app.features.targets.schemas import NumbersHidden
from app.integrations.openfoodfacts import InvalidBarcode, OffClient, normalize_barcode

# Room kept for packaged hits when many generic foods match.
PACKAGED_RESERVE = 5


def _f(value: Decimal | None) -> float | None:
    return None if value is None else float(value)


def _like(q: str) -> str:
    escaped = q.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
    return f"%{escaped}%"


def rank(query: str, name: str, search_text: str) -> int:
    """0: the name starts with the query; 1: a word of the name or an alias does; 2: it is
    somewhere inside."""
    if name.lower().startswith(query):
        return 0
    if re.search(rf"(?:^|\W){re.escape(query)}", search_text):
        return 1
    return 2


def _food_hit(food: Food) -> FoodHit:
    is_dish = food.source == "smartnutri_recipe"
    own = "attribution.smartnutri_recipe" if is_dish else "attribution.usda_fdc"
    return FoodHit(
        kind="food",
        id=str(food.id),
        name=food.name_en,
        brand=None,
        group="indian",
        is_dish=is_dish,
        grade=None,
        attribution=own,
        attributions=[own, "attribution.usda_fdc"] if is_dish else [own],
    )


async def _mine_hits(
    session: AsyncSession, query: str, limit: int, kinds: set[SearchKind], account_id: UUID
) -> list[FoodHit]:
    """The account's own custom foods and recipes whose name (or brand) matches, ranked like the
    rest (prefix, word prefix, substring; ties by name length, then name). Another account's
    are never read: every query is scoped by account."""
    found: list[tuple[tuple[int, int, str], FoodHit]] = []
    if SearchKind.CUSTOM_FOOD in kinds:
        rows = await session.scalars(
            select(CustomFood).where(
                CustomFood.account_id == account_id,
                or_(
                    CustomFood.name.ilike(_like(query), escape="\\"),
                    CustomFood.brand.ilike(_like(query), escape="\\"),
                ),
            )
        )
        for f in rows:
            hay = f"{f.name} {f.brand or ''}".lower()
            key = (rank(query, f.name, hay), len(f.name), f.name)
            found.append(
                (
                    key,
                    FoodHit(
                        kind="custom_food", id=str(f.id), name=f.name, brand=f.brand, group="mine",
                        is_dish=False, grade=None, attribution=None, attributions=[],
                    ),
                )
            )  # fmt: skip
    if SearchKind.RECIPE in kinds:
        rows = await session.scalars(
            select(Recipe).where(
                Recipe.account_id == account_id, Recipe.name.ilike(_like(query), escape="\\")
            )
        )
        for r in rows:
            key = (rank(query, r.name, r.name.lower()), len(r.name), r.name)
            found.append(
                (
                    key,
                    FoodHit(
                        kind="recipe", id=str(r.id), name=r.name, brand=None, group="mine",
                        is_dish=False, grade=None, attribution=None, attributions=[],
                    ),
                )
            )  # fmt: skip
    found.sort(key=lambda pair: pair[0])
    return [hit for _, hit in found[:limit]]


async def search_foods(
    session: AsyncSession,
    off: OffClient,
    q: str,
    limit: int,
    kinds: set[SearchKind],
    *,
    account_id: UUID,
    settings: Settings,
) -> FoodSearchOut:
    """Generic foods and dishes first (name prefix, then word prefix, then substring; ties by
    name length, then name), then packaged products from our catalogue and Open Food Facts.
    Does not commit (the OFF search cache write is the caller's to commit)."""
    query = products_search.normalise_query(q)
    items: list[FoodHit] = await _mine_hits(session, query, limit, kinds, account_id)
    if SearchKind.FOOD in kinds and len(items) < limit:
        rows = await session.scalars(
            select(Food).where(
                Food.search_text.ilike(_like(query), escape="\\"), Food.review_status != "retired"
            )
        )
        ranked = sorted(
            rows, key=lambda f: (rank(query, f.name_en, f.search_text), len(f.name_en), f.name_en)
        )
        room = limit - len(items)
        cap = room
        if SearchKind.PRODUCT in kinds:
            cap = max(1, room - min(PACKAGED_RESERVE, room // 2))
        items += [_food_hit(f) for f in ranked[:cap]]
    partial = False
    if SearchKind.PRODUCT in kinds and len(items) < limit:
        hits, partial = await products_search.search_products_status(
            session, off, q, limit - len(items), account_id=account_id, settings=settings
        )
        for h in hits:
            items.append(
                FoodHit(
                    kind="product" if h.product_id is not None else "off",
                    id=str(h.product_id) if h.product_id is not None else (h.barcode or ""),
                    name=h.name,
                    brand=h.brand,
                    group="packaged",
                    is_dish=False,
                    grade=h.grade,
                    attribution=h.attribution,
                    attributions=[h.attribution] if h.attribution else [],
                )
            )
    return FoodSearchOut(items=items, partial=partial, failed_sources=["off"] if partial else [])


def unit_out(unit: Unit) -> UnitOut:
    return UnitOut(code=unit.code, kind=unit.kind, ml=_f(unit.ml), grams=_f(unit.grams))  # type: ignore[arg-type]


async def list_units(session: AsyncSession) -> list[UnitOut]:
    return [unit_out(u) for u in (await unit_table(session)).values()]


def _redact(per_100: dict[str, float | None], hidden: NumbersHidden) -> dict[str, float | None]:
    if hidden.macros:
        return dict.fromkeys(recipe_math.NUTRIENT_KEYS)
    if hidden.energy:
        return {**per_100, "energy_kcal": None}
    return per_100


def to_detail_out(
    loaded: LoadedFood, table: dict[str, Unit], hidden: NumbersHidden
) -> FoodDetailOut:
    resolved = resolve_units(loaded.units, table)
    per_100 = {k: _f(v) for k, v in recipe_math.snapshot_per_100(loaded.per_100).items()}
    dish = None
    if loaded.dish is not None:
        dish = DishOut(
            ingredients=[DishIngredientOut(**i) for i in loaded.dish["ingredients"]],
            cooked_weight_g=loaded.dish["cooked_weight_g"],
            servings=loaded.dish["servings"],
        )
    return FoodDetailOut(
        kind=loaded.ref.kind,
        id=loaded.ref.id,
        name=loaded.name,
        brand=loaded.brand,
        basis=loaded.basis,
        per_100=NutrientSnapshot(**_redact(per_100, hidden)),
        units=[
            FoodUnitOut(
                code=r.code,
                kind=table[r.code].kind,
                ml=_f(table[r.code].ml),
                grams_per_unit=float(r.grams_per_unit),
                source=r.source,
                user_override=r.source == "portion_user",
            )
            for r in resolved
        ],
        default_unit=default_unit(resolved),
        # A recipe has no units of its own to set (only g and serving): nothing is settable.
        settable_units=[] if loaded.recipe_id is not None else settable_units(loaded.units, table),
        serving_g=_f(loaded.units.serving_g),
        attribution=loaded.attribution,
        attributions=list(loaded.attributions),
        licence=loaded.licence,
        dish=dish,
        review_pending=loaded.food_id is not None,
        recipe_incomplete=list(loaded.incomplete),
        numbers_hidden=hidden,
    )


async def food_detail(
    session: AsyncSession,
    off: OffClient,
    ref: FoodRef,
    hidden: NumbersHidden,
    *,
    account_id: UUID,
    settings: Settings,
) -> FoodDetailOut:
    loaded = await load_food(session, off, ref, account_id=account_id, settings=settings)
    return to_detail_out(loaded, await unit_table(session), hidden)


def _ref_columns(loaded: LoadedFood) -> dict[str, UUID | str | None]:
    if loaded.food_id is not None:
        return {"food_id": loaded.food_id}
    if loaded.custom_food_id is not None:
        return {"custom_food_id": loaded.custom_food_id}
    if loaded.product_id is not None:
        return {"product_id": loaded.product_id}
    return {"off_barcode": loaded.off_barcode}


def _matches(loaded: LoadedFood):
    cols = _ref_columns(loaded)
    return [getattr(FoodPortion, k) == v for k, v in cols.items()]


async def put_portion(
    session: AsyncSession,
    off: OffClient,
    ref: FoodRef,
    unit_code: str,
    grams_per_unit: Decimal,
    hidden: NumbersHidden,
    *,
    account_id: UUID,
    settings: Settings,
) -> FoodDetailOut:
    """Set (or replace) this account's own grams for one unit of one food. Only count and
    volume units, never `serving` or a mass unit: else 422 `unit_not_supported`. Does not
    commit."""
    table = await unit_table(session)
    unit = table.get(unit_code)
    if unit is None or unit.kind == "mass" or unit.code == "serving" or ref.kind == "recipe":
        raise ApiError("unit_not_supported", 422, details={"unit": unit_code})
    loaded = await load_food(session, off, ref, account_id=account_id, settings=settings)
    where = [
        FoodPortion.account_id == account_id,
        FoodPortion.unit == unit_code,
        *_matches(loaded),
    ]
    existing = await session.scalar(select(FoodPortion).where(*where))
    if existing is not None:
        existing.grams_per_unit = grams_per_unit
    else:
        try:
            async with session.begin_nested():
                session.add(
                    FoodPortion(
                        account_id=account_id,
                        unit=unit_code,
                        grams_per_unit=grams_per_unit,
                        source="user",
                        **_ref_columns(loaded),  # type: ignore[arg-type]
                    )
                )
        except IntegrityError:  # a concurrent PUT inserted it first: replace its value
            existing = await session.scalar(select(FoodPortion).where(*where))
            if existing is None:  # pragma: no cover
                raise
            existing.grams_per_unit = grams_per_unit
    await session.flush()
    loaded = await load_food(session, off, ref, account_id=account_id, settings=settings)
    return to_detail_out(loaded, table, hidden)


async def delete_portion(
    session: AsyncSession, ref: FoodRef, unit_code: str, *, account_id: UUID
) -> None:
    """Remove this account's override (idempotent: nothing to remove is fine). Never reads
    Open Food Facts. Does not commit."""
    from sqlalchemy import delete

    from app.features.products.models import Product

    conditions = [FoodPortion.account_id == account_id, FoodPortion.unit == unit_code]
    try:
        if ref.kind == "recipe":
            return  # a recipe has no overrides
        if ref.kind == "custom_food":
            conditions.append(FoodPortion.custom_food_id == UUID(ref.id))
        elif ref.kind == "food":
            conditions.append(FoodPortion.food_id == UUID(ref.id))
        elif ref.kind == "product":
            conditions.append(FoodPortion.product_id == UUID(ref.id))
        else:
            barcode = normalize_barcode(ref.id)
            own = select(Product.id).where(Product.barcode == barcode)
            conditions.append(
                or_(FoodPortion.off_barcode == barcode, FoodPortion.product_id.in_(own))
            )
    except (ValueError, InvalidBarcode):
        return  # not a real reference: there is no override to remove
    await session.execute(delete(FoodPortion).where(*conditions))


async def food_by_barcode(
    session: AsyncSession,
    off: OffClient,
    barcode: str,
    hidden: NumbersHidden,
    *,
    account_id: UUID,
    settings: Settings,
) -> FoodDetailOut:
    """The food behind a scanned barcode, for LOGGING only: the account's own custom food with
    that barcode first, else our product, else Open Food Facts (G17). 422 `invalid_barcode`;
    404 `product_not_found`; 503 `off_unavailable`. Custom foods are never read by the verdict
    routes (`products_get_by_barcode`, `analyze`), so they cannot reach a verdict."""
    try:
        code = normalize_barcode(barcode)
    except InvalidBarcode:
        raise ApiError("invalid_barcode", 422) from None
    custom = await session.scalar(
        select(CustomFood.id).where(CustomFood.account_id == account_id, CustomFood.barcode == code)
    )
    if custom is not None:
        return await food_detail(
            session, off, FoodRef("custom_food", str(custom)), hidden,
            account_id=account_id, settings=settings,
        )  # fmt: skip
    loaded = await load_food(
        session, off, FoodRef("off", code), account_id=account_id, settings=settings
    )
    out = to_detail_out(loaded, await unit_table(session), hidden)
    if loaded.product_id is not None:  # our own catalogue answered: a product, not an OFF hit
        out = out.model_copy(update={"kind": "product", "id": str(loaded.product_id)})
    return out
