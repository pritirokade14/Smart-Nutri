"""Foods API shapes (Plan 12 Task 4; spec 6.3). Hits carry no nutrients; the detail carries
the per-100 values (unrounded, null = unknown or hidden) and ONLY the units that resolve."""

from enum import StrEnum
from typing import Literal

from pydantic import BaseModel, Field

from app.features.meals.schemas import NutrientSnapshot
from app.features.products.schemas import NutriScoreGrade
from app.features.targets.schemas import NumbersHidden

UnitKindOut = Literal["mass", "volume", "count"]
UnitSourceOut = Literal[
    "mass", "serving", "portion_user", "portion_global", "density", "volume_basis"
]


class FoodKindPath(StrEnum):
    """What ``id`` is: a generic food or dish (uuid), our own product (uuid) or an Open Food
    Facts product (the barcode)."""

    FOOD = "food"
    PRODUCT = "product"
    OFF = "off"
    CUSTOM_FOOD = "custom_food"
    RECIPE = "recipe"


class SearchKind(StrEnum):
    FOOD = "food"
    PRODUCT = "product"
    CUSTOM_FOOD = "custom_food"
    RECIPE = "recipe"


class FoodHit(BaseModel):
    kind: Literal["food", "product", "off", "custom_food", "recipe"]
    id: str = Field(description="A uuid, or the barcode for kind=off")
    name: str
    brand: str | None
    group: Literal["mine", "indian", "packaged"] = Field(
        description="`mine` (your custom foods and recipes) comes first, then `indian`, `packaged`"
    )
    is_dish: bool = Field(description="A documented Indian dish (calculated from ingredients)")
    grade: NutriScoreGrade | None = Field(
        description="Nutri-Score calculated by SmartNutri; packaged products only, else null"
    )
    attribution: str | None = Field(
        description='"attribution.usda_fdc", "attribution.smartnutri_recipe" or "attribution.off"'
    )
    attributions: list[str] = Field(description="Every credit this hit needs, in order")


class FoodSearchOut(BaseModel):
    items: list[FoodHit]
    partial: bool = Field(description="true when a source (Open Food Facts) could not answer")
    failed_sources: list[Literal["off"]]


class UnitOut(BaseModel):
    code: str
    kind: UnitKindOut
    ml: float | None
    grams: float | None


class FoodUnitOut(BaseModel):
    code: str
    kind: UnitKindOut
    ml: float | None = Field(description="Volume of one unit; volume units only")
    grams_per_unit: float = Field(
        description=(
            "The amount of ONE unit in the food's basis (grams, or ml for an ml-basis food), "
            "unrounded. Only units that resolve are listed"
        )
    )
    source: UnitSourceOut
    user_override: bool = Field(description="true when the account set this value itself")


class DishIngredientOut(BaseModel):
    name: str | None
    grams: float | None


class DishOut(BaseModel):
    ingredients: list[DishIngredientOut]
    cooked_weight_g: float | None
    servings: int | None


class FoodDetailOut(BaseModel):
    kind: Literal["food", "product", "off", "custom_food", "recipe"]
    id: str
    name: str
    brand: str | None
    basis: Literal["g", "ml"]
    per_100: NutrientSnapshot = Field(
        description=(
            "Per 100 g (or 100 ml), unrounded; null = unknown, or hidden by the member's "
            "numbers display"
        )
    )
    units: list[FoodUnitOut]
    default_unit: str
    settable_units: list[str] = Field(
        description="Units that do not resolve yet and may be given the user's own grams"
    )
    serving_g: float | None
    attribution: str | None
    attributions: list[str]
    licence: str | None
    dish: DishOut | None
    review_pending: bool = Field(
        description="Household measures and dishes are pending dietitian review"
    )
    recipe_incomplete: list[str] = Field(
        default_factory=list,
        description=(
            "A recipe only: the nutrients at least one ingredient does not know. They are null in "
            "`per_100`, so a logged serving never counts a partial value"
        ),
    )
    numbers_hidden: NumbersHidden


class PortionIn(BaseModel):
    grams_per_unit: float = Field(
        gt=0, le=2000, description="The amount of one unit in the food's basis"
    )
