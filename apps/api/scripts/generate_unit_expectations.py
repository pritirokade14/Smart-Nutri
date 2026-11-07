"""Check or regenerate packages/test-fixtures/units/conversions.json from the real `to_grams`.

Run from apps/api:
  uv run python -m scripts.generate_unit_expectations          # --check (default): exit 1 if stale
  uv run python -m scripts.generate_unit_expectations --write  # write the file

The cases below are hand-written inputs; every `expected` value comes from
`app.features.foods.units` (`to_grams`, `portion_amount`) and the diary's own
`meals.service._portion` and `_round1` (the preview Android and web must reproduce: quantity x
grams per unit x per-100 / 100, rounded half-up to 1 dp). Per-100 values are synthetic test
numbers, not food data. Never hand-edit the JSON to match code.

Case shape: {case, food: {basis, serving_g, density_g_per_ml, global_portions, user_portions},
unit, quantity, per_100, expected: {grams_per_unit | null, amount | null, error | null,
preview | null}}. `grams_per_unit` is the amount of ONE unit in the food's basis (null: the unit
does not resolve, so a picker never offers it). `preview` has the NutrientSnapshot keys.
"""

from __future__ import annotations

import argparse
import difflib
import json
import sys
from decimal import Decimal
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[1]))

from app.core.errors import ApiError
from app.features.foods.units import FoodUnits, portion_amount, table_from_yaml, to_grams
from app.features.meals.service import _portion, _round1

PATH = Path(__file__).parents[3] / "packages/test-fixtures/units/conversions.json"
TABLE = table_from_yaml()

PER_100 = {  # synthetic: one unknown (sat_fat_g stays null, never 0)
    "energy_kcal": 120.0,
    "sugars_g": 2.5,
    "salt_g": 0.5,
    "protein_g": 7.0,
    "fat_g": 3.0,
    "sat_fat_g": None,
    "carbs_g": 15.0,
    "fibre_g": 4.0,
}


def food(basis="g", serving_g=None, density=None, glob=None, user=None) -> dict:
    return {
        "basis": basis,
        "serving_g": serving_g,
        "density_g_per_ml": density,
        "global_portions": glob or {},
        "user_portions": user or {},
    }


def case(name, f, unit, quantity, per_100=None) -> dict:
    return {
        "case": name,
        "food": f,
        "unit": unit,
        "quantity": quantity,
        "per_100": per_100 or PER_100,
    }


CASES = [
    case("katori_cooked_dal", food(density=0.71), "katori", 1),
    case("katori_small_nin", food(density=0.71), "katori_small", 1),
    case("katori_medium_nin", food(density=0.71), "katori_medium", 1),
    case("katori_large_nin", food(density=0.71), "katori_large", 1),
    case("one_and_a_half_katori", food(density=0.71), "katori", 1.5),
    case("tbsp_canola_oil", food(density=0.921), "tbsp", 1),
    case("tsp_half", food(density=0.921), "tsp", 0.5),
    case("glass_of_milk_g_basis", food(density=1.031), "glass", 1),
    case("glass_ml_basis", food(basis="ml"), "glass", 1),
    case("ml_on_ml_basis", food(basis="ml"), "ml", 30),
    case("grams_on_grams", food(), "g", 250),
    case("two_packaged_roti", food(glob={"roti": 68}), "roti", 2),
    case("roti_user_override_wins", food(glob={"roti": 68}, user={"roti": 35}), "roti", 2),
    case("two_large_eggs", food(glob={"piece_large": 50}), "piece_large", 2),
    case("serving_of_30g", food(serving_g=30), "serving", 2),
    case("serving_unknown_refused", food(), "serving", 1),
    case("count_unit_without_portion_refused", food(density=0.9, serving_g=30), "piece", 2),
    case("katori_without_density_refused", food(serving_g=30), "katori", 1),
    case("grams_on_ml_basis_refused", food(basis="ml"), "g", 50),
    case("bound_result_over_5000", food(density=1.0), "katori_large", 30),
    case("bound_quantity_over_1000", food(density=0.71), "katori", 1001),
    case(
        "rounding_trap_fibre_1_15",
        food(),
        "g",
        100,
        {**PER_100, "fibre_g": 1.15, "energy_kcal": None},
    ),
    case(
        "rounding_trap_fibre_10_016",
        food(),
        "g",
        250,
        {**PER_100, "fibre_g": 10.016, "energy_kcal": None},
    ),
]


def _dec(value) -> Decimal | None:
    return None if value is None else Decimal(str(value))


def _units(raw: dict) -> FoodUnits:
    return FoodUnits(
        raw["basis"],
        serving_g=_dec(raw["serving_g"]),
        density_g_per_ml=_dec(raw["density_g_per_ml"]),
        global_portions={k: _dec(v) for k, v in raw["global_portions"].items()},
        user_portions={k: _dec(v) for k, v in raw["user_portions"].items()},
    )


def expected(raw: dict) -> dict:
    f = _units(raw["food"])
    one = to_grams(Decimal(1), TABLE[raw["unit"]], f)
    out: dict = {
        "grams_per_unit": None if one is None else float(one),
        "amount": None,
        "error": None,
        "preview": None,
    }
    try:
        amount = portion_amount(_dec(raw["quantity"]), raw["unit"], f, TABLE)
    except ApiError as err:
        out["error"] = err.code
        return out
    out["amount"] = float(amount)
    out["preview"] = {
        k: None if v is None else _round1(_portion(v, float(amount)))
        for k, v in raw["per_100"].items()
    }
    return out


def render() -> str:
    cases = [{**c, "expected": expected(c)} for c in CASES]
    return json.dumps({"cases": cases}, indent=2, sort_keys=True, ensure_ascii=False) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true", help="the default")
    parser.add_argument("--write", action="store_true")
    args = parser.parse_args()
    new = render()
    old = PATH.read_text(encoding="utf-8") if PATH.exists() else ""
    if new == old:
        print("conversions.json is up to date")
        return 0
    if args.write:
        PATH.write_text(new, encoding="utf-8")
        print(f"wrote {PATH}")
        return 0
    sys.stdout.writelines(
        difflib.unified_diff(old.splitlines(True), new.splitlines(True), "current", "generated")
    )
    return 1


if __name__ == "__main__":
    sys.exit(main())
