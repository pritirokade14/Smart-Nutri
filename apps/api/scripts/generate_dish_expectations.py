"""Check or regenerate packages/test-fixtures/foods/dishes.json from the real seed code.

Run from apps/api:
  uv run python -m scripts.generate_dish_expectations          # --check (default): exit 1 if stale
  uv run python -m scripts.generate_dish_expectations --write  # write the file

For each seeded dish: the per-100 g nutrients the seed computes (the sum of the ingredients over
the cooked weight, in Decimal, rounded to 4 dp for the file) and its serving grams; `null` means
unknown (a nutrient unknown on any ingredient is null). Dishes left out (blocked, needs weighing)
are listed with their status. Every value is PENDING DIETITIAN REVIEW. Never hand-edit the JSON.
"""

from __future__ import annotations

import argparse
import difflib
import json
import sys
from decimal import ROUND_HALF_UP, Decimal
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[1]))

from app.features.foods import recipe_math
from app.features.foods.seed import dish_per_100, load_seed_data

PATH = Path(__file__).parents[3] / "packages/test-fixtures/foods/dishes.json"


def _r4(value: Decimal | None) -> float | None:
    return None if value is None else float(value.quantize(Decimal("0.0001"), ROUND_HALF_UP))


def render() -> str:
    data = load_seed_data()
    foods = {f.fdc_id: f for f in data.foods}
    dishes = {}
    for dish in data.seeded_dishes:
        per = dish_per_100(dish, foods)
        dishes[dish.code] = {
            "name_en": dish.name_en,
            "cooked_weight_g": float(dish.cooked_weight_g),  # type: ignore[arg-type]
            "serving_g": (
                _r4(dish.cooked_weight_g / dish.servings) if dish.servings else None  # type: ignore[operator]
            ),
            "per_100": {k: _r4(per[k]) for k in recipe_math.NUTRIENT_KEYS},
        }
    excluded = {d.code: d.status for d in data.dishes if d.status != "seeded"}
    return json.dumps({"dishes": dishes, "excluded": excluded}, indent=2, sort_keys=True) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true", help="the default")
    parser.add_argument("--write", action="store_true")
    args = parser.parse_args()
    new = render()
    old = PATH.read_text(encoding="utf-8") if PATH.exists() else ""
    if new == old:
        print("dishes.json is up to date")
        return 0
    if args.write:
        PATH.parent.mkdir(parents=True, exist_ok=True)
        PATH.write_text(new, encoding="utf-8")
        print(f"wrote {PATH}")
        return 0
    sys.stdout.writelines(
        difflib.unified_diff(old.splitlines(True), new.splitlines(True), "current", "generated")
    )
    return 1


if __name__ == "__main__":
    sys.exit(main())
