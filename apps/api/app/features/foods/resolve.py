"""Load a loggable food (a generic food or dish, an own product or an OFF product) with the
units that resolve for it (Plan 12 Task 2). Slice 4 adds the account's custom foods and recipes.

Every portion row is scoped: the global rows (ours) and THIS account's own overrides, never
another account's. Open Food Facts data stays in `off_product_cache`; only the grams per unit
we derive ourselves are stored here (ODbL). Names and nutrients never go to logs.
"""

from dataclasses import dataclass
from decimal import Decimal
from typing import Any, Literal
from uuid import UUID

from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app import scoring
from app.core.config import Settings
from app.core.errors import ApiError
from app.features.custom_foods.models import CustomFood
from app.features.foods import recipe_math
from app.features.foods.models import Food, FoodPortion, HouseholdUnit
from app.features.foods.units import Basis, FoodUnits, Unit
from app.features.products import service as products_service
from app.features.recipes.models import Recipe, RecipeIngredient
from app.integrations.openfoodfacts import OffClient

FoodKind = Literal["food", "product", "off", "custom_food", "recipe"]
ATTRIBUTION_USDA = "attribution.usda_fdc"
ATTRIBUTION_RECIPE = "attribution.smartnutri_recipe"
_NUTRIENT_FIELDS = tuple(scoring.Nutrients.__dataclass_fields__)


@dataclass(frozen=True, slots=True)
class FoodRef:
    kind: FoodKind
    id: str  # a uuid string, or the barcode for `off`


@dataclass(frozen=True, slots=True)
class LoadedFood:
    ref: FoodRef
    name: str
    brand: str | None
    basis: Basis
    per_100: scoring.Nutrients  # unrounded; None = unknown
    units: FoodUnits
    grade: str | None  # products only, as `log_meal` computes it
    attribution: str | None
    attributions: tuple[str, ...]
    licence: str | None
    source: str | None
    dish: dict[str, Any] | None
    food_id: UUID | None
    product_id: UUID | None
    off_barcode: str | None
    # Slice 4: the account's own custom food or recipe (never reaches a verdict).
    custom_food_id: UUID | None = None
    recipe_id: UUID | None = None
    incomplete: tuple[str, ...] = ()  # a recipe's nutrients at least one ingredient lacks
    retired: bool = False  # a dish we no longer offer: readable, but never logged anew


def ref_from_ids(
    *,
    food_id: UUID | None,
    product_id: UUID | None,
    barcode: str | None,
    custom_food_id: UUID | None = None,
    recipe_id: UUID | None = None,
) -> FoodRef:
    """Exactly one reference, else 422 `invalid_product_ref`."""
    given = [x for x in (food_id, product_id, barcode, custom_food_id, recipe_id) if x is not None]
    if len(given) != 1:
        raise ApiError("invalid_product_ref", 422)
    if custom_food_id is not None:
        return FoodRef("custom_food", str(custom_food_id))
    if recipe_id is not None:
        return FoodRef("recipe", str(recipe_id))
    if food_id is not None:
        return FoodRef("food", str(food_id))
    if product_id is not None:
        return FoodRef("product", str(product_id))
    return FoodRef("off", barcode or "")


async def unit_table(session: AsyncSession) -> dict[str, Unit]:
    rows = await session.scalars(select(HouseholdUnit).order_by(HouseholdUnit.sort))
    return {r.code: Unit(r.code, r.kind, r.ml, r.grams, r.sort) for r in rows}  # type: ignore[arg-type]


def _nutrients(per_100: dict[str, Any] | None) -> scoring.Nutrients:
    raw = per_100 or {}
    return scoring.Nutrients(
        **{k: (None if raw.get(k) is None else float(raw[k])) for k in _NUTRIENT_FIELDS}
    )


def _dec(value: Any) -> Decimal | None:
    return None if value is None else Decimal(str(value))


async def _portions(
    session: AsyncSession,
    account_id: UUID,
    *,
    food_id: UUID | None = None,
    product_id: UUID | None = None,
    off_barcode: str | None = None,
    custom_food_id: UUID | None = None,
) -> tuple[dict[str, Decimal], dict[str, Decimal]]:
    """(global, this account's own) grams per unit by unit code."""
    if custom_food_id is not None:
        ref = FoodPortion.custom_food_id == custom_food_id
    elif food_id is not None:
        ref = FoodPortion.food_id == food_id
    elif product_id is not None:
        ref = FoodPortion.product_id == product_id
    else:
        ref = FoodPortion.off_barcode == off_barcode
    rows = await session.scalars(
        select(FoodPortion).where(
            ref, or_(FoodPortion.account_id.is_(None), FoodPortion.account_id == account_id)
        )
    )
    mine: dict[str, Decimal] = {}
    ours: dict[str, Decimal] = {}
    for row in rows:
        (mine if row.account_id is not None else ours)[row.unit] = row.grams_per_unit
    return ours, mine


def _dish(food: Food) -> dict[str, Any] | None:
    recipe = food.recipe
    if not recipe:
        return None
    return {
        "ingredients": [
            {"name": i.get("name"), "grams": i.get("grams")} for i in recipe.get("ingredients", [])
        ],
        "cooked_weight_g": recipe.get("cooked_weight_g"),
        "servings": recipe.get("servings"),
    }


async def _load_custom_food(session: AsyncSession, ref: FoodRef, account_id: UUID) -> LoadedFood:
    try:
        custom_id = UUID(ref.id)
    except ValueError:
        raise ApiError("custom_food_not_found", 404) from None
    row = await session.scalar(
        select(CustomFood).where(CustomFood.id == custom_id, CustomFood.account_id == account_id)
    )
    if row is None:
        raise ApiError("custom_food_not_found", 404)
    _, mine = await _portions(session, account_id, custom_food_id=row.id)
    return LoadedFood(
        ref=ref,
        name=row.name,
        brand=row.brand,
        basis=row.basis,  # type: ignore[arg-type]  (checked by ck_custom_foods_basis)
        per_100=_nutrients(row.per_100),
        units=FoodUnits(
            basis=row.basis,  # type: ignore[arg-type]
            serving_g=row.serving_g,
            density_g_per_ml=row.density_g_per_ml,
            user_portions=mine,
        ),
        grade=None,
        attribution=None,
        attributions=(),
        licence=None,
        source="custom_food",
        dish=None,
        food_id=None,
        product_id=None,
        off_barcode=None,
        custom_food_id=row.id,
    )


async def _load_recipe(session: AsyncSession, ref: FoodRef, account_id: UUID) -> LoadedFood:
    """A recipe is a gram-basis food. Its per-100 is STRICT: a nutrient at least one ingredient
    does not know is None (G19), never the partial sum the recipe screen shows as "at least"."""
    try:
        recipe_id = UUID(ref.id)
    except ValueError:
        raise ApiError("recipe_not_found", 404) from None
    row = await session.scalar(
        select(Recipe).where(Recipe.id == recipe_id, Recipe.account_id == account_id)
    )
    if row is None:
        raise ApiError("recipe_not_found", 404)
    basis_weight = row.cooked_weight_g or row.total_raw_g
    if basis_weight is None:  # the service refuses to store this; never divide by nothing
        raise ApiError("recipe_weight_invalid", 422, details={"reason": "cooked_weight_required"})
    incomplete = tuple(row.incomplete_nutrients or ())
    stored = row.per_100g or {}
    per_100 = {
        k: (None if stored.get(k) is None or k in incomplete else _dec(stored[k]))
        for k in recipe_math.NUTRIENT_KEYS
    }
    attributions: list[str] = []
    for ingredient in await session.scalars(
        select(RecipeIngredient)
        .where(RecipeIngredient.recipe_id == row.id)
        .order_by(RecipeIngredient.position)
    ):
        if ingredient.attribution and ingredient.attribution not in attributions:
            attributions.append(ingredient.attribution)
    return LoadedFood(
        ref=ref,
        name=row.name,
        brand=None,
        basis="g",
        per_100=recipe_math.to_nutrients(per_100),
        units=FoodUnits(
            basis="g", serving_g=None if not row.servings else basis_weight / row.servings
        ),
        grade=None,
        # The ODbL credit is mandatory when any ingredient came from Open Food Facts.
        attribution=(
            products_service.OFF_ATTRIBUTION
            if products_service.OFF_ATTRIBUTION in attributions
            else None
        ),
        attributions=tuple(attributions),
        licence=None,
        source="recipe",
        dish=None,
        food_id=None,
        product_id=None,
        off_barcode=None,
        recipe_id=row.id,
        incomplete=incomplete,
    )


async def load_food(
    session: AsyncSession,
    off: OffClient,
    ref: FoodRef,
    *,
    account_id: UUID,
    settings: Settings,
) -> LoadedFood:
    """404 `food_not_found` for an unknown generic food; for products and OFF the errors of
    `products_service.resolve_ref` (`product_not_found`, `invalid_barcode`, `off_unavailable`).
    A custom food or recipe is the ACCOUNT's own: another account's id is 404
    `custom_food_not_found` / `recipe_not_found`."""
    if ref.kind == "custom_food":
        return await _load_custom_food(session, ref, account_id)
    if ref.kind == "recipe":
        return await _load_recipe(session, ref, account_id)
    if ref.kind == "food":
        try:
            food_id = UUID(ref.id)
        except ValueError:
            raise ApiError("food_not_found", 404) from None
        food = await session.get(Food, food_id)
        if food is None:
            raise ApiError("food_not_found", 404)
        ours, mine = await _portions(session, account_id, food_id=food.id)
        is_dish = food.source == "smartnutri_recipe"
        own = ATTRIBUTION_RECIPE if is_dish else ATTRIBUTION_USDA
        return LoadedFood(
            ref=ref,
            name=food.name_en,
            brand=None,
            basis=food.basis,  # type: ignore[arg-type]  (checked by ck_foods_basis)
            per_100=_nutrients(food.per_100),
            units=FoodUnits(
                basis=food.basis,  # type: ignore[arg-type]
                serving_g=food.serving_g,
                density_g_per_ml=food.density_g_per_ml,
                global_portions=ours,
                user_portions=mine,
            ),
            grade=None,
            attribution=own,
            # A dish is built from USDA ingredients: both credits are kept.
            attributions=(own, ATTRIBUTION_USDA) if is_dish else (own,),
            licence=food.licence,
            source=food.source,
            dish=_dish(food),
            food_id=food.id,
            product_id=None,
            off_barcode=None,
            retired=food.review_status == "retired",
        )

    if ref.kind == "product":
        try:
            product_uuid = UUID(ref.id)
        except ValueError:
            raise ApiError("product_not_found", 404) from None
        found = await products_service.resolve_ref(
            session, off, product_id=product_uuid, barcode=None, settings=settings,
            account_id=account_id,
        )  # fmt: skip
    else:
        found = await products_service.resolve_ref(
            session, off, product_id=None, barcode=ref.id, settings=settings, account_id=account_id
        )
    product = found.product
    if found.product_id is not None:
        ours, mine = await _portions(session, account_id, product_id=found.product_id)
        off_barcode = None
    else:
        ours, mine = await _portions(session, account_id, off_barcode=found.info.barcode)
        off_barcode = found.info.barcode
    attribution = found.attribution
    return LoadedFood(
        ref=ref,
        name=found.info.name or "",
        brand=found.info.brand,
        basis="g",
        per_100=product.per_100g,
        units=FoodUnits(
            basis="g",
            serving_g=_dec(product.serving_size_g),
            global_portions=ours,
            user_portions=mine,
        ),
        grade=scoring.analyze(product, []).report.nutriscore.grade,
        attribution=attribution,
        attributions=(attribution,) if attribution else (),
        licence=None,
        source=found.source,
        dish=None,
        food_id=None,
        product_id=found.product_id,
        off_barcode=off_barcode,
    )
