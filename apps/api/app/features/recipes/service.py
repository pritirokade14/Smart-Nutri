"""Recipes: build from ingredients, read, replace, delete (Plan 12 Task 12; spec 5.9; G15,
G19-G22). No FastAPI imports.

An ingredient is resolved with `load_food` (the account's own custom foods only; OFF through the
cache) and converted with `portion_amount`, which refuses to guess (422 `unit_grams_unknown`,
with the ingredient's `position`). Each ingredient keeps a snapshot of its per-100 values, so a
recipe never changes when a food does. The stored `per_100g` is the sum of the KNOWN parts and
`incomplete_nutrients` names the rest (G19). Names and values never go to logs.
"""

from decimal import ROUND_HALF_UP, Decimal
from uuid import UUID

from sqlalchemy import delete, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core import time as core_time
from app.core.config import Settings
from app.core.cursor import decode_cursor, encode_cursor
from app.core.errors import ApiError
from app.features.foods import recipe_math
from app.features.foods import resolve as foods_resolve
from app.features.foods import units as food_units
from app.features.meals.schemas import NutrientSnapshot
from app.features.recipes import compute as recipe_compute
from app.features.recipes.models import Recipe, RecipeIngredient
from app.features.recipes.schemas import (
    RecipeIn,
    RecipeIngredientOut,
    RecipeOut,
    RecipeSummaryOut,
)
from app.features.targets.schemas import NumbersHidden
from app.integrations.openfoodfacts import OffClient

CLIENT_ID_CONSTRAINT = "uq_recipes_account_id_client_id"


def _dec(value: float | None) -> Decimal | None:
    return None if value is None else Decimal(repr(value))


def _floats(values: dict[str, Decimal | None]) -> dict[str, float | None]:
    return {k: (None if v is None else float(v)) for k, v in values.items()}


def _round1(value: Decimal | None) -> float | None:
    return None if value is None else float(value.quantize(Decimal("0.1"), rounding=ROUND_HALF_UP))


def _display(
    values: dict[str, Decimal | None] | None, hidden: NumbersHidden
) -> NutrientSnapshot | None:
    """1 dp for display, redacted with the member's numbers display (G15)."""
    if values is None:
        return None
    out = {k: _round1(values.get(k)) for k in recipe_math.NUTRIENT_KEYS}
    if hidden.macros:
        out = dict.fromkeys(recipe_math.NUTRIENT_KEYS)
    elif hidden.energy:
        out["energy_kcal"] = None
    return NutrientSnapshot(**out)


async def _resolve_ingredients(
    session: AsyncSession, off: OffClient, body: RecipeIn, *, account_id: UUID, settings: Settings
) -> list[tuple[RecipeIngredient, recipe_compute.IngredientCalc]]:
    table = await foods_resolve.unit_table(session)
    out: list[tuple[RecipeIngredient, recipe_compute.IngredientCalc]] = []
    for position, item in enumerate(body.ingredients):
        ref = foods_resolve.ref_from_ids(
            food_id=item.food_id,
            product_id=item.product_id,
            barcode=item.barcode,
            custom_food_id=item.custom_food_id,
        )
        loaded = await foods_resolve.load_food(
            session, off, ref, account_id=account_id, settings=settings
        )
        if loaded.retired:
            raise ApiError("food_retired", 422, details={"position": position})
        quantity = Decimal(repr(item.quantity))
        try:
            grams = food_units.portion_amount(quantity, item.unit, loaded.units, table)
        except ApiError as exc:
            # The ingredient's position rides along (literal codes: the i18n scan needs them).
            details = {**exc.details, "position": position}
            if exc.code == "unit_grams_unknown":
                raise ApiError("unit_grams_unknown", 422, details=details) from None
            if exc.code == "unit_not_supported":
                raise ApiError("unit_not_supported", 422, details=details) from None
            if exc.code == "quantity_out_of_range":
                raise ApiError("quantity_out_of_range", 422, details=details) from None
            raise
        density = loaded.units.density_g_per_ml
        weight = grams if loaded.basis == "g" else (grams * density if density else None)
        per_100 = recipe_math.snapshot_per_100(loaded.per_100)
        kind = (
            "custom_food" if loaded.custom_food_id is not None
            else "food" if loaded.food_id is not None
            else "product" if loaded.product_id is not None
            else "off"
        )  # fmt: skip
        row = RecipeIngredient(
            position=position,
            source_kind=kind,
            product_id=loaded.product_id,
            off_barcode=loaded.off_barcode,
            food_id=loaded.food_id,
            custom_food_id=loaded.custom_food_id,
            name=loaded.name,
            quantity=quantity,
            unit=item.unit,
            grams=grams,
            basis=loaded.basis,
            weight_g=weight,
            per_100=_floats(per_100),
            attribution=loaded.attribution,
        )
        out.append((row, recipe_compute.IngredientCalc(grams, weight, per_100)))
    return out


def _stored(row: Recipe, calc: recipe_compute.RecipeCalc) -> None:
    row.total_raw_g = calc.total_raw_g
    row.per_100g = _floats(calc.per_100g)
    row.incomplete_nutrients = list(calc.incomplete)


async def _by_client_id(session: AsyncSession, account_id: UUID, client_id: UUID) -> Recipe | None:
    return await session.scalar(
        select(Recipe)
        .where(Recipe.account_id == account_id, Recipe.client_id == client_id)
        .execution_options(populate_existing=True)
    )


async def create_recipe(
    session: AsyncSession,
    off: OffClient,
    account_id: UUID,
    body: RecipeIn,
    *,
    settings: Settings,
) -> tuple[Recipe, bool]:
    """(row, created). A ``client_id`` already stored returns that row first. Does not commit
    (the OFF cache write is the caller's to commit)."""
    if body.client_id is not None:
        stored = await _by_client_id(session, account_id, body.client_id)
        if stored is not None:
            return stored, False
    parts = await _resolve_ingredients(session, off, body, account_id=account_id, settings=settings)
    calc = recipe_compute.compute(
        [c for _, c in parts],
        servings=_dec(body.servings),
        cooked_weight_g=_dec(body.cooked_weight_g),
    )
    now = core_time.now_utc()
    row = Recipe(
        account_id=account_id,
        name=body.name,
        servings=_dec(body.servings),
        cooked_weight_g=_dec(body.cooked_weight_g),
        client_id=body.client_id,
        created_at=now,
        updated_at=now,
    )
    _stored(row, calc)
    try:
        async with session.begin_nested():
            session.add(row)
            await session.flush()
    except IntegrityError as exc:
        name = getattr(getattr(exc.orig, "diag", None), "constraint_name", None)
        if name != CLIENT_ID_CONSTRAINT or body.client_id is None:
            raise
        stored = await _by_client_id(session, account_id, body.client_id)
        if stored is None:  # pragma: no cover
            raise
        return stored, False
    for ingredient, _ in parts:
        ingredient.recipe_id = row.id
        ingredient.account_id = account_id
        session.add(ingredient)
    await session.flush()
    return row, True


async def get_owned(session: AsyncSession, account_id: UUID, recipe_id: UUID) -> Recipe:
    row = await session.scalar(
        select(Recipe)
        .where(Recipe.id == recipe_id, Recipe.account_id == account_id)
        .execution_options(populate_existing=True)
    )
    if row is None:
        raise ApiError("recipe_not_found", 404)
    return row


async def update_recipe(
    session: AsyncSession,
    off: OffClient,
    account_id: UUID,
    recipe_id: UUID,
    body: RecipeIn,
    *,
    settings: Settings,
) -> Recipe:
    """Replace the recipe and its ingredients. Past diary entries keep their own snapshot. An
    ingredient whose custom food was deleted must be replaced (it has no ref to re-send:
    422 `invalid_product_ref`). Does not commit."""
    row = await get_owned(session, account_id, recipe_id)
    parts = await _resolve_ingredients(session, off, body, account_id=account_id, settings=settings)
    calc = recipe_compute.compute(
        [c for _, c in parts],
        servings=_dec(body.servings),
        cooked_weight_g=_dec(body.cooked_weight_g),
    )
    row.name = body.name
    row.servings = _dec(body.servings)
    row.cooked_weight_g = _dec(body.cooked_weight_g)
    row.updated_at = core_time.now_utc()
    _stored(row, calc)
    await session.execute(delete(RecipeIngredient).where(RecipeIngredient.recipe_id == row.id))
    await session.flush()
    for ingredient, _ in parts:
        ingredient.recipe_id = row.id
        ingredient.account_id = account_id
        session.add(ingredient)
    await session.flush()
    return row


async def delete_recipe(session: AsyncSession, account_id: UUID, recipe_id: UUID) -> None:
    """Delete (G21): diary entries keep their snapshot with `recipe_id` set NULL. Does not
    commit."""
    row = await get_owned(session, account_id, recipe_id)
    await session.delete(row)
    await session.flush()


async def ingredients_of(session: AsyncSession, recipe_id: UUID) -> list[RecipeIngredient]:
    return list(
        await session.scalars(
            select(RecipeIngredient)
            .where(RecipeIngredient.recipe_id == recipe_id)
            .order_by(RecipeIngredient.position)
            .execution_options(populate_existing=True)
        )
    )


def _ingredient_out(i: RecipeIngredient) -> RecipeIngredientOut:
    return RecipeIngredientOut(
        position=i.position,
        source_kind=i.source_kind,  # type: ignore[arg-type]
        food_id=i.food_id,
        custom_food_id=i.custom_food_id,
        product_id=i.product_id,
        barcode=i.off_barcode,
        name=i.name,
        quantity=float(i.quantity),
        unit=i.unit,
        grams=float(i.grams),
        attribution=i.attribution,
        available=not (i.source_kind == "custom_food" and i.custom_food_id is None),
    )


async def to_out(session: AsyncSession, row: Recipe, hidden: NumbersHidden) -> RecipeOut:
    ingredients = await ingredients_of(session, row.id)
    # Displayed from the exact arithmetic over the ingredient snapshots (Decimal), never from
    # the stored floats: 3.45 must round to 3.5, not 3.4999999 to 3.4.
    calc = recipe_compute.compute(
        [
            recipe_compute.IngredientCalc(
                grams=i.grams,
                weight_g=i.weight_g,
                per_100={k: _dec((i.per_100 or {}).get(k)) for k in recipe_math.NUTRIENT_KEYS},
            )
            for i in ingredients
        ],
        servings=row.servings,
        cooked_weight_g=row.cooked_weight_g,
    )
    attributions: list[str] = []
    for i in ingredients:
        if i.attribution and i.attribution not in attributions:
            attributions.append(i.attribution)
    return RecipeOut(
        id=row.id,
        name=row.name,
        servings=None if row.servings is None else float(row.servings),
        cooked_weight_g=None if row.cooked_weight_g is None else float(row.cooked_weight_g),
        total_raw_g=None if row.total_raw_g is None else float(row.total_raw_g),
        basis_weight_g=float(calc.basis_weight_g),
        per_100g=_display(calc.per_100g, hidden),  # type: ignore[arg-type]
        per_serving=_display(calc.per_serving, hidden),
        incomplete_nutrients=list(row.incomplete_nutrients or []),
        attributions=attributions,
        ingredients=[_ingredient_out(i) for i in ingredients],
        numbers_hidden=hidden,
        updated_at=row.updated_at,
    )


async def list_recipes(
    session: AsyncSession, account_id: UUID, limit: int, cursor: str | None
) -> tuple[list[Recipe], str | None]:
    from sqlalchemy import and_, or_

    query = select(Recipe).where(Recipe.account_id == account_id)
    if cursor is not None:
        at, last_id = decode_cursor(cursor)
        query = query.where(
            or_(Recipe.updated_at < at, and_(Recipe.updated_at == at, Recipe.id < last_id))
        )
    rows = list(
        await session.scalars(
            query.order_by(Recipe.updated_at.desc(), Recipe.id.desc()).limit(limit + 1)
        )
    )
    page = rows[:limit]
    more = encode_cursor(page[-1].updated_at, page[-1].id) if len(rows) > limit else None
    return page, more


def to_summary(row: Recipe) -> RecipeSummaryOut:
    return RecipeSummaryOut(
        id=row.id,
        name=row.name,
        servings=None if row.servings is None else float(row.servings),
        incomplete_nutrients=list(row.incomplete_nutrients or []),
        updated_at=row.updated_at,
    )
