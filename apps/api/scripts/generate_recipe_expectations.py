"""Check or regenerate packages/test-fixtures/recipes/expected from the real recipe arithmetic.

Run from apps/api:
  uv run python -m scripts.generate_recipe_expectations          # --check (default): exit 1 if stale
  uv run python -m scripts.generate_recipe_expectations --write  # write the files

Each input (recipes/inputs/<case>.json) lists synthetic ingredients: the amount in the
ingredient's basis (g or ml), an optional density for an ml ingredient, and per-100 values where
`null` is unknown. The expected file is what `app.features.recipes.compute.compute` returns:
the raw total, the basis weight, per-100 g and per-serving as the sum of the KNOWN ingredients
(1 dp), the incomplete nutrients, and the strict per-100 a diary entry keeps (4 dp, incomplete
nutrients null). A case the API refuses has `{"error": {"code", "details"}}`. Never hand-edit the
expected files; every value is information, not advice.
"""

from __future__ import annotations

import argparse
import difflib
import json
import sys
from decimal import ROUND_HALF_UP, Decimal
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[1]))

from app.core.errors import ApiError
from app.features.foods import recipe_math
from app.features.recipes.compute import IngredientCalc, compute

ROOT = Path(__file__).parents[3] / "packages/test-fixtures/recipes"


def _r(value: Decimal | None, dp: int) -> float | None:
    if value is None:
        return None
    return float(value.quantize(Decimal(1).scaleb(-dp), ROUND_HALF_UP))


def _row(values: dict[str, Decimal | None] | None, dp: int) -> dict[str, float | None] | None:
    return None if values is None else {k: _r(values[k], dp) for k in recipe_math.NUTRIENT_KEYS}


def _dec(value: float | None) -> Decimal | None:
    return None if value is None else Decimal(str(value))


def expected_for(case: dict) -> dict:
    ingredients = []
    for i in case["ingredients"]:
        amount = Decimal(str(i["amount"]))
        density = _dec(i.get("density_g_per_ml"))
        if i["basis"] == "g":
            weight = amount
        else:
            weight = amount * density if density else None
        ingredients.append(
            IngredientCalc(
                grams=amount,
                weight_g=weight,
                per_100={k: _dec(i["per_100"].get(k)) for k in recipe_math.NUTRIENT_KEYS},
            )
        )
    try:
        calc = compute(
            ingredients,
            servings=_dec(case.get("servings")),
            cooked_weight_g=_dec(case.get("cooked_weight_g")),
        )
    except ApiError as exc:
        return {"error": {"code": exc.code, "details": exc.details}}
    return {
        "total_raw_g": _r(calc.total_raw_g, 1),
        "basis_weight_g": _r(calc.basis_weight_g, 1),
        "per_100g": _row(calc.per_100g, 1),
        "per_serving": _row(calc.per_serving, 1),
        "incomplete_nutrients": list(calc.incomplete),
        "entry_snapshot_per_100": _row(calc.entry_per_100, 4),
    }


def render() -> dict[str, str]:
    out = {}
    for path in sorted((ROOT / "inputs").glob("*.json")):
        case = json.loads(path.read_text(encoding="utf-8"))
        out[path.name] = json.dumps(expected_for(case), indent=2, sort_keys=True) + "\n"
    return out


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true", help="the default")
    parser.add_argument("--write", action="store_true")
    args = parser.parse_args()
    target = ROOT / "expected"
    stale = False
    for name, new in render().items():
        path = target / name
        old = path.read_text(encoding="utf-8") if path.exists() else ""
        if new == old:
            continue
        if args.write:
            target.mkdir(parents=True, exist_ok=True)
            path.write_text(new, encoding="utf-8")
            print(f"wrote {path}")
            continue
        stale = True
        sys.stdout.writelines(
            difflib.unified_diff(
                old.splitlines(True), new.splitlines(True), f"{name} current", "generated"
            )
        )
    if not stale and not args.write:
        print("recipe expectations are up to date")
    return 1 if stale else 0


if __name__ == "__main__":
    sys.exit(main())
