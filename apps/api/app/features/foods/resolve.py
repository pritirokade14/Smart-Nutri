"""Load a loggable food (a generic food or dish, an own product or an OFF product) with the
units that resolve for it (Plan 12 Task 2). Slice 4 adds the custom food and recipe kinds.

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
from app.features.foods.models import Food, FoodPortion, HouseholdUnit
from app.features.foods.units import Basis, FoodUnits, Unit
from app.features.products import service as products_service
from app.integrations.openfoodfacts import OffClient

FoodKind = Literal["food", "product", "off"]
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


def ref_from_ids(*, food_id: UUID | None, product_id: UUID | None, barcode: str | None) -> FoodRef:
    """Exactly one reference, else 422 `invalid_product_ref`."""
    given = [x for x in (food_id, product_id, barcode) if x is not None]
    if len(given) != 1:
        raise ApiError("invalid_product_ref", 422)
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
) -> tuple[dict[str, Decimal], dict[str, Decimal]]:
    """(global, this account's own) grams per unit by unit code."""
    if food_id is not None:
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


async def load_food(
    session: AsyncSession,
    off: OffClient,
    ref: FoodRef,
    *,
    account_id: UUID,
    settings: Settings,
) -> LoadedFood:
    """404 `food_not_found` for an unknown generic food; for products and OFF the errors of
    `products_service.resolve_ref` (`product_not_found`, `invalid_barcode`, `off_unavailable`)."""
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
