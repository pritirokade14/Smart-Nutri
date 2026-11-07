"""The recipe arithmetic (Plan 12 Task 12; spec 5.9; G19, G20). Pure, `Decimal`, no I/O.

``compute`` turns ingredients (each: its amount in its own basis, the mass that amount weighs,
and its per-100 values) into the totals: the raw total weight, the basis weight, the per-100 g
and per-serving values as the sum of the KNOWN parts (the recipe screen shows these as "at
least"), the nutrients at least one ingredient does not know, and the STRICT per-100 a diary
entry keeps (every incomplete nutrient None). A nutrient no ingredient knows is None, never 0.
The service and `scripts/generate_recipe_expectations.py` both call it.
"""

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from decimal import Decimal

from app.core.errors import ApiError
from app.features.foods import recipe_math

MIN_COOKED_RATIO = Decimal("0.2")  # the cooked weight must be within 0.2-3 x the raw total
MAX_COOKED_RATIO = Decimal(3)


@dataclass(frozen=True, slots=True)
class IngredientCalc:
    """``grams`` is the amount in the ingredient's basis (g, or ml); ``weight_g`` is what it
    weighs (None for an ml-basis ingredient with no density); ``per_100`` is per 100 of the
    ingredient's own basis, in `recipe_math.NUTRIENT_KEYS`."""

    grams: Decimal
    weight_g: Decimal | None
    per_100: Mapping[str, Decimal | None]


@dataclass(frozen=True, slots=True)
class RecipeCalc:
    total_raw_g: Decimal | None
    basis_weight_g: Decimal
    per_100g: dict[str, Decimal | None]  # known-part sums per 100 g of the basis weight
    per_serving: dict[str, Decimal | None] | None
    incomplete: tuple[str, ...]
    entry_per_100: dict[str, Decimal | None]  # strict: what a diary entry keeps


def total_raw_g(ingredients: Sequence[IngredientCalc]) -> Decimal | None:
    """The sum of the ingredient weights; None when any ingredient has no mass (an ml-basis
    ingredient without a density), because a partial raw total would be a wrong one."""
    weights = [i.weight_g for i in ingredients]
    if any(w is None for w in weights):
        return None
    return sum(weights, Decimal(0))  # type: ignore[arg-type]


def compute(
    ingredients: Sequence[IngredientCalc],
    *,
    servings: Decimal | None,
    cooked_weight_g: Decimal | None,
) -> RecipeCalc:
    """422 `recipe_weight_invalid`: ``details.reason`` is `cooked_weight_required` (the raw total
    is unknown and no cooked weight was given) or `out_of_range` (cooked weight outside
    0.2-3 x the raw total)."""
    raw = total_raw_g(ingredients)
    if cooked_weight_g is not None:
        if (
            raw is not None
            and not MIN_COOKED_RATIO * raw <= cooked_weight_g <= MAX_COOKED_RATIO * raw
        ):
            raise ApiError("recipe_weight_invalid", 422, details={"reason": "out_of_range"})
        basis_weight = cooked_weight_g
    elif raw is not None:
        basis_weight = raw
    else:
        raise ApiError("recipe_weight_invalid", 422, details={"reason": "cooked_weight_required"})

    sums = recipe_math.sum_nutrients([recipe_math.Amount(i.grams, i.per_100) for i in ingredients])
    per_100g = recipe_math.per_100_from(sums, basis_weight, strict=False)
    per_serving = (
        None
        if not servings
        else {
            k: (None if sums.totals[k] is None else sums.totals[k] / servings)  # type: ignore[operator]
            for k in recipe_math.NUTRIENT_KEYS
        }
    )
    return RecipeCalc(
        total_raw_g=raw,
        basis_weight_g=basis_weight,
        per_100g=per_100g,
        per_serving=per_serving,
        incomplete=sums.incomplete,
        entry_per_100=recipe_math.per_100_from(sums, basis_weight, strict=True),
    )
