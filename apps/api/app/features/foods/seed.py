"""The foods seed: USDA FoodData Central rows, household grams and densities, and documented
Indian dishes (Plan 12 Task 3; ADR 0024; G3, G5-G10).

`load_seed_data` is pure: it parses and validates the files in `data/`. `seed_foods` is an
idempotent upsert by `(source, source_code)`, so a food keeps its id across reseeds and an old
diary entry never loses its `food_id`. Every value is PENDING DIETITIAN REVIEW.

Never invent data: an empty CSV cell is None; a per-piece weight the CSV has no number for is
listed under `unknown_piece_weights` and produces no portion row; a dish nutrient unknown on
any ingredient is None (never a partial sum stored as complete).
"""

import csv
from dataclasses import dataclass
from decimal import Decimal
from pathlib import Path
from typing import Any

import yaml
from sqlalchemy import delete, func, select, update
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from app import scoring
from app.features.foods import recipe_math
from app.features.foods.models import Food, FoodPortion

DATA_DIR = Path(__file__).parent / "data"
FDC_SOURCE = "usda_fdc"
DISH_SOURCE = "smartnutri_recipe"
FDC_DATA_VERSION = "fdc_sr_legacy_2018_04"
DISH_DATA_VERSION = "dishes_2026_11"
FDC_LICENCE = "CC0 1.0"
DISH_LICENCE = "SmartNutri recipe from CC0 1.0 USDA ingredients"
DENSITY_SOURCE = "fdc_derived"
CSV_TO_NUTRIENT = {  # CSV column -> scoring.Nutrients field
    "energy_kcal": "energy_kcal",
    "protein_g": "protein_g",
    "carbs_g": "carbs_g",
    "fat_g": "fat_g",
    "fibre_g": "fiber_g",
    "sugar_g": "sugars_g",
    "sodium_mg": "sodium_mg",
}


@dataclass(frozen=True, slots=True)
class FdcFood:
    fdc_id: str
    name: str
    per_100: dict[str, Decimal | None]  # scoring.Nutrients field names; sat_fat, salt, fvl unknown


@dataclass(frozen=True, slots=True)
class PortionRow:
    csv_key: str
    fdc_id: str
    unit: str
    grams: Decimal


@dataclass(frozen=True, slots=True)
class DensityRow:
    csv_key: str
    fdc_id: str
    density: Decimal


@dataclass(frozen=True, slots=True)
class DishIngredient:
    fdc_id: str | None  # None: a gap (no FDC row)
    grams: Decimal
    name: str | None = None


@dataclass(frozen=True, slots=True)
class Dish:
    code: str
    doc_section: int
    name_en: str
    aliases: tuple[str, ...]
    reason: str | None
    cooked_weight_g: Decimal | None
    servings: int | None
    ingredients: tuple[DishIngredient, ...]
    notes: str | None

    @property
    def status(self) -> str:
        """Derived from the data: `blocked` (an ingredient has no FDC row), `needs_weighing`
        (no cooked weight in grams), else `seeded`. A dietitian adding `cooked_weight_g`
        switches a needs-weighing dish on."""
        if any(i.fdc_id is None for i in self.ingredients):
            return "blocked"
        if self.cooked_weight_g is None:
            return "needs_weighing"
        return "seeded"


@dataclass(frozen=True, slots=True)
class SeedData:
    foods: tuple[FdcFood, ...]
    aliases: dict[str, tuple[str, ...]]
    portions: tuple[PortionRow, ...]
    densities: tuple[DensityRow, ...]
    dishes: tuple[Dish, ...]
    not_seeded: tuple[str, ...]  # portion csv_keys left out (FDC id not in the CSV)
    unknown_piece_weights: tuple[str, ...]  # csv_keys with no grams: never given a number

    @property
    def seeded_dishes(self) -> tuple[Dish, ...]:
        return tuple(d for d in self.dishes if d.status == "seeded")


@dataclass(frozen=True, slots=True)
class SeedReport:
    foods: int
    dishes_seeded: int
    dishes_excluded: dict[str, str]
    portions: int
    densities: int


def _dec(value: Any) -> Decimal | None:
    if value is None or str(value).strip() == "":
        return None
    return Decimal(str(value).strip())


def _yaml(path: Path) -> Any:
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def load_seed_data(data_dir: Path = DATA_DIR) -> SeedData:
    """Parse and validate. Raises ValueError for an unknown FDC id, a duplicate or a bad unit."""
    foods: list[FdcFood] = []
    with (data_dir / "usda_fdc_foods.csv").open(encoding="utf-8", newline="") as fh:
        for row in csv.DictReader(fh):
            foods.append(
                FdcFood(
                    fdc_id=row["fdc_id"],
                    name=row["name"],
                    per_100={n: _dec(row[c]) for c, n in CSV_TO_NUTRIENT.items()},
                )
            )
    ids = [f.fdc_id for f in foods]
    if len(set(ids)) != len(ids):
        raise ValueError("duplicate fdc_id in usda_fdc_foods.csv")
    known = set(ids)

    aliases_raw = _yaml(data_dir / "aliases.yaml") or {}
    aliases = {str(k): tuple(v) for k, v in aliases_raw.items()}
    if unknown := set(aliases) - known:
        raise ValueError(f"aliases for unknown fdc_id: {sorted(unknown)}")

    unit_codes = {u["code"] for u in _yaml(data_dir / "household_units.yaml")["units"]}
    raw = _yaml(data_dir / "food_portions.yaml")
    portions = tuple(
        PortionRow(p["csv_key"], str(p["fdc_id"]), p["unit"], Decimal(p["grams"]))
        for p in raw["portions"]
    )
    for p in portions:
        if p.fdc_id not in known or p.unit not in unit_codes:
            raise ValueError(f"portion {p.csv_key}: unknown fdc_id or unit")
    if len({(p.fdc_id, p.unit) for p in portions}) != len(portions):
        raise ValueError("two portions for one food and unit")
    densities = tuple(
        DensityRow(d["csv_key"], str(d["fdc_id"]), Decimal(d["density_g_per_ml"]))
        for d in raw["densities"]
    )
    for d in densities:
        if d.fdc_id not in known:
            raise ValueError(f"density {d.csv_key}: unknown fdc_id")

    dishes = []
    for d in _yaml(data_dir / "indian_dishes.yaml")["dishes"]:
        ingredients = tuple(
            DishIngredient(
                None if i["fdc_id"] is None else str(i["fdc_id"]),
                Decimal(i["grams"]),
                i.get("name"),
            )
            for i in d["ingredients"]
        )
        for i in ingredients:
            if i.fdc_id is not None and i.fdc_id not in known:
                raise ValueError(f"dish {d['code']}: unknown fdc_id {i.fdc_id}")
        dishes.append(
            Dish(
                code=d["code"],
                doc_section=int(d["doc_section"]),
                name_en=d["name_en"],
                aliases=tuple(d["aliases"]),
                reason=d.get("reason"),
                cooked_weight_g=_dec(d.get("cooked_weight_g")),
                servings=d.get("servings"),
                ingredients=ingredients,
                notes=d.get("notes"),
            )
        )
    if len({d.code for d in dishes}) != len(dishes):
        raise ValueError("duplicate dish code")
    return SeedData(
        foods=tuple(foods),
        aliases=aliases,
        portions=portions,
        densities=densities,
        dishes=tuple(dishes),
        not_seeded=tuple(n["csv_key"] for n in raw["not_seeded"]),
        unknown_piece_weights=tuple(n["csv_key"] for n in raw["unknown_piece_weights"]),
    )


def fdc_nutrients(food: FdcFood) -> scoring.Nutrients:
    """The engine's `Nutrients` of an FDC row. Saturated fat, salt and fvl are unknown (the CSV
    has no such column); salt comes from sodium through the engine's own rule."""
    return scoring.Nutrients(
        **{k: (None if v is None else float(v)) for k, v in food.per_100.items()}
    )


def dish_per_100(dish: Dish, foods: dict[str, FdcFood]) -> dict[str, Decimal | None]:
    """A seeded dish per 100 g of its cooked weight: the sum of each ingredient's nutrients
    over the cooked weight. Strict: a nutrient unknown on any ingredient is None (G8)."""
    if dish.cooked_weight_g is None or any(i.fdc_id is None for i in dish.ingredients):
        raise ValueError(f"{dish.code} is not seedable")
    amounts = [
        recipe_math.Amount(
            i.grams,
            recipe_math.snapshot_per_100(fdc_nutrients(foods[i.fdc_id])),  # type: ignore[index]
        )
        for i in dish.ingredients
    ]
    sums = recipe_math.sum_nutrients(amounts)
    return recipe_math.per_100_from(sums, dish.cooked_weight_g, strict=True)


def _num(value: Decimal) -> int | float:
    return int(value) if value == value.to_integral_value() else float(value)


def _search_text(name: str, aliases: tuple[str, ...]) -> str:
    return " ".join([name, *aliases]).lower()


def report_for(data: SeedData) -> SeedReport:
    excluded = {
        d.code: f"{d.status}: {d.reason or ''}".strip(": ")
        for d in data.dishes
        if d.status != "seeded"
    }
    return SeedReport(
        foods=len(data.foods),
        dishes_seeded=len(data.seeded_dishes),
        dishes_excluded=excluded,
        portions=len(data.portions),
        densities=len(data.densities),
    )


def food_rows(data: SeedData) -> list[dict[str, Any]]:
    """The `foods` rows to upsert: every FDC row, then every seeded dish."""
    densities = {d.fdc_id: d.density for d in data.densities}
    rows: list[dict[str, Any]] = []
    by_id = {f.fdc_id: f for f in data.foods}
    for f in data.foods:
        aliases = data.aliases.get(f.fdc_id, ())
        per_100 = {k: (None if v is None else float(v)) for k, v in f.per_100.items()}
        per_100 |= {"sat_fat_g": None, "salt_g": None, "fvl_percent": None}
        rows.append(
            {
                "source": FDC_SOURCE,
                "source_code": f.fdc_id,
                "name_en": f.name,
                "aliases": list(aliases),
                "search_text": _search_text(f.name, aliases),
                "basis": "g",
                "per_100": per_100,
                "density_g_per_ml": densities.get(f.fdc_id),
                "density_source": DENSITY_SOURCE if f.fdc_id in densities else None,
                "serving_g": None,
                "recipe": None,
                "licence": FDC_LICENCE,
                "data_version": FDC_DATA_VERSION,
            }
        )
    for dish in data.seeded_dishes:
        per = dish_per_100(dish, by_id)
        nutrients = recipe_math.to_nutrients(per)
        recipe = {
            "ingredients": [
                {"fdc_id": i.fdc_id, "name": by_id[i.fdc_id].name, "grams": _num(i.grams)}  # type: ignore[index]
                for i in dish.ingredients
            ],
            "cooked_weight_g": _num(dish.cooked_weight_g),  # type: ignore[arg-type]
            "servings": dish.servings,
            "review": "assumed_needs_dietitian",
        }
        rows.append(
            {
                "source": DISH_SOURCE,
                "source_code": dish.code,
                "name_en": dish.name_en,
                "aliases": list(dish.aliases),
                "search_text": _search_text(dish.name_en, dish.aliases),
                "basis": "g",
                "per_100": {
                    k: getattr(nutrients, k) for k in scoring.Nutrients.__dataclass_fields__
                },
                "density_g_per_ml": None,
                "density_source": None,
                "serving_g": (
                    dish.cooked_weight_g / dish.servings  # type: ignore[operator]
                    if dish.servings
                    else None
                ),
                "recipe": recipe,
                "licence": DISH_LICENCE,
                "data_version": DISH_DATA_VERSION,
            }
        )
    return rows


_UPDATE_COLUMNS = (
    "name_en",
    "aliases",
    "search_text",
    "basis",
    "per_100",
    "density_g_per_ml",
    "density_source",
    "serving_g",
    "recipe",
    "licence",
    "data_version",
)


async def seed_foods(session: AsyncSession, *, dry_run: bool = False) -> SeedReport:
    """Idempotent upsert; commits. ``dry_run`` reads and validates the files and returns the
    report without touching the database."""
    data = load_seed_data()
    report = report_for(data)
    if dry_run:
        return report

    rows = food_rows(data)
    stmt = insert(Food).values(rows)
    stmt = stmt.on_conflict_do_update(
        constraint="uq_foods_source_source_code",
        set_={**{c: getattr(stmt.excluded, c) for c in _UPDATE_COLUMNS}, "updated_at": func.now()},
    ).returning(Food.id, Food.source, Food.source_code)
    result = await session.execute(stmt)
    ids = {(r.source, r.source_code): r.id for r in result}

    # A dish that became blocked or excluded is unlisted (kept, so old diary entries still
    # resolve); one that is seeded again is listed again. Never touches a sign-off status.
    seeded_ids = list(ids.values())
    await session.execute(
        update(Food)
        .where(
            Food.source == DISH_SOURCE, Food.id.not_in(seeded_ids), Food.review_status != "retired"
        )
        .values(review_status="retired", updated_at=func.now())
    )
    await session.execute(
        update(Food)
        .where(Food.id.in_(seeded_ids), Food.review_status == "retired")
        .values(review_status="pending_dietitian_review", updated_at=func.now())
    )

    wanted = {(ids[(FDC_SOURCE, p.fdc_id)], p.unit): p for p in data.portions}
    existing = {
        (r.food_id, r.unit): r
        for r in await session.scalars(
            select(FoodPortion).where(
                FoodPortion.account_id.is_(None),
                FoodPortion.food_id.in_({v for (src, _), v in ids.items() if src == FDC_SOURCE}),
            )
        )
    }
    for (food_id, unit), p in wanted.items():
        row = existing.get((food_id, unit))
        if row is None:
            session.add(
                FoodPortion(
                    food_id=food_id,
                    unit=unit,
                    grams_per_unit=p.grams,
                    source="reference_table",
                    csv_key=p.csv_key,
                )
            )
        else:
            row.grams_per_unit = p.grams
            row.csv_key = p.csv_key
    # A seeded global row that left the data goes too (never a user override).
    stale = [r.id for key, r in existing.items() if key not in wanted and r.csv_key is not None]
    if stale:
        await session.execute(delete(FoodPortion).where(FoodPortion.id.in_(stale)))
    await session.commit()
    return report
