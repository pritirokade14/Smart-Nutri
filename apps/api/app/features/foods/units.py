"""Typed household units and ``to_grams`` that refuses to guess (Plan 12 Task 2; G4, G5, G11).

Pure and `Decimal`-only: no I/O, no FastAPI. The result of a conversion is the amount in the
food's BASIS: grams, or millilitres for an ml-basis food. It follows spec 5.6, in order:

1. a mass unit;
2. ``serving`` -> the food's ``serving_g``;
3. a portion row for this food and unit (the user's own override first, then the global row);
4. a volume unit with a density;
5. a volume unit on an ml-basis food.

Otherwise the result is ``None``: a unit with nothing to convert it by is never offered, and a
forced request is `422 unit_grams_unknown`. The API never assumes 1 ml = 1 g and never returns
the quantity itself for a unit it cannot convert. Every unit value is PENDING DIETITIAN REVIEW
(ADR 0024).
"""

from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from decimal import Decimal
from pathlib import Path
from typing import Literal

import yaml

from app.core.errors import ApiError

UnitCode = Literal[
    "g",
    "ml",
    "serving",
    "piece",
    "piece_small",
    "piece_medium",
    "piece_large",
    "roti",
    "slice",
    "katori",
    "katori_small",
    "katori_medium",
    "katori_large",
    "cup",
    "glass",
    "tbsp",
    "tsp",
]
UnitKind = Literal["mass", "volume", "count"]
Basis = Literal["g", "ml"]
UnitSource = Literal["mass", "serving", "portion_user", "portion_global", "density", "volume_basis"]

MAX_AMOUNT = Decimal(5000)  # basis amount (g or ml) per entry or ingredient
MAX_QUANTITY = Decimal(1000)  # every unit except g and ml (those: MAX_AMOUNT)
SERVING = "serving"
# The count units a default may be (in the order they are offered), after `serving`.
_COUNT_DEFAULTS = ("piece", "piece_small", "piece_medium", "piece_large", "roti", "slice")


@dataclass(frozen=True, slots=True)
class Unit:
    code: str
    kind: UnitKind
    ml: Decimal | None
    grams: Decimal | None
    sort: int


@dataclass(frozen=True, slots=True)
class FoodUnits:
    """What a food offers to convert a unit: its basis, serving weight, density, the global
    portion rows and the account's own overrides (each: unit code -> grams per unit)."""

    basis: Basis
    serving_g: Decimal | None = None
    density_g_per_ml: Decimal | None = None
    global_portions: Mapping[str, Decimal] = field(default_factory=dict)
    user_portions: Mapping[str, Decimal] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class ResolvedUnit:
    code: str
    grams_per_unit: Decimal
    source: UnitSource


def _convert(quantity: Decimal, unit: Unit, food: FoodUnits) -> tuple[Decimal, UnitSource] | None:
    if unit.kind == "mass":
        grams = unit.grams
        if grams is None:  # pragma: no cover - the table's check forbids it
            return None
        if food.basis == "g":
            return quantity * grams, "mass"
        # An ml-basis food: grams need a density, and the result is millilitres.
        if food.density_g_per_ml:
            return quantity * grams / food.density_g_per_ml, "mass"
        return None
    if unit.code == SERVING:
        if food.serving_g:
            return quantity * food.serving_g, "serving"
        return None
    mine = food.user_portions.get(unit.code)
    if mine is not None:
        return quantity * mine, "portion_user"
    ours = food.global_portions.get(unit.code)
    if ours is not None:
        return quantity * ours, "portion_global"
    if unit.kind == "volume" and unit.ml is not None:
        if food.density_g_per_ml:
            return quantity * unit.ml * food.density_g_per_ml, "density"
        if food.basis == "ml":
            return quantity * unit.ml, "volume_basis"
    return None


def to_grams(quantity: Decimal, unit: Unit, food: FoodUnits) -> Decimal | None:
    """The amount (in the food's basis) of ``quantity`` x ``unit``, or None when nothing
    converts it. Never the quantity itself for a unit that has no conversion."""
    found = _convert(quantity, unit, food)
    return None if found is None else found[0]


def resolve_units(food: FoodUnits, table: Mapping[str, Unit]) -> list[ResolvedUnit]:
    """Every unit that resolves for this food (grams of exactly one unit), in table order."""
    out: list[ResolvedUnit] = []
    for unit in sorted(table.values(), key=lambda u: (u.sort, u.code)):
        found = _convert(Decimal(1), unit, food)
        if found is not None:
            out.append(ResolvedUnit(unit.code, found[0], found[1]))
    return out


def default_unit(resolved: Sequence[ResolvedUnit]) -> str:
    """serving > the first count unit > katori > g (> ml). Only resolving units are chosen."""
    codes = {r.code for r in resolved}
    for code in (SERVING, *_COUNT_DEFAULTS, "katori", "g", "ml"):
        if code in codes:
            return code
    return resolved[0].code if resolved else "g"


def settable_units(food: FoodUnits, table: Mapping[str, Unit]) -> list[str]:
    """Count and volume codes (never ``serving``, never a mass unit) that do not resolve yet:
    the ones the user may give their own grams for."""
    out: list[str] = []
    for unit in sorted(table.values(), key=lambda u: (u.sort, u.code)):
        if unit.kind == "mass" or unit.code == SERVING:
            continue
        if _convert(Decimal(1), unit, food) is None:
            out.append(unit.code)
    return out


def portion_amount(
    quantity: Decimal, unit_code: str, food: FoodUnits, table: Mapping[str, Unit]
) -> Decimal:
    """The basis amount of an entry or ingredient, or an ApiError 422:
    ``unit_not_supported`` (unknown code), ``quantity_out_of_range`` (quantity above its limit,
    not positive, or a result above 5000), ``unit_grams_unknown`` (nothing converts the unit)."""
    unit = table.get(unit_code)
    if unit is None:
        raise ApiError("unit_not_supported", 422, details={"unit": unit_code})
    cap = MAX_AMOUNT if unit_code in ("g", "ml") else MAX_QUANTITY
    if not 0 < quantity <= cap:
        raise ApiError("quantity_out_of_range", 422)
    amount = to_grams(quantity, unit, food)
    if amount is None:
        raise ApiError("unit_grams_unknown", 422, details={"unit": unit_code})
    if not 0 < amount <= MAX_AMOUNT:
        raise ApiError("quantity_out_of_range", 422)
    return amount


UNITS_YAML = Path(__file__).parent / "data" / "household_units.yaml"


def table_from_yaml(path: Path = UNITS_YAML) -> dict[str, Unit]:
    """The unit table from ``household_units.yaml`` (equal to the migration rows; tested).
    For tests and the fixture generator: the API reads the table from the database."""
    raw = yaml.safe_load(path.read_text(encoding="utf-8"))
    return {
        u["code"]: Unit(
            u["code"],
            u["kind"],
            None if u["ml"] is None else Decimal(u["ml"]),
            None if u["grams"] is None else Decimal(u["grams"]),
            int(u["sort"]),
        )
        for u in raw["units"]
    }
