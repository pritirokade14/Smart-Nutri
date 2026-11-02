"""Nutri-Score 2023 (general foods, beverages, water).

Step 0 verification: tables compared with Open Food Facts' open-source
implementation, `points_thresholds_2023` and `compute_nutriscore_grade_2023` in
https://github.com/openfoodfacts/openfoodfacts-server/blob/main/lib/ProductOpener/Nutriscore.pm

Result: all tables in the plan matched EXCEPT the beverage sugars table.
  plan:     0, 1.5, 3, 4.5, 6, 7.5, 9, 10.5, 12, 13.5
  official: 0.5, 2, 3.5, 5, 6, 7, 8, 9, 10, 11   (used here)
Effect: cola (10.6 g sugars) scores 9 sugar points, not 8 -> total 12 (was 11); still grade E.

Known simplification (per plan): CHEESE and FAT are scored with the general table and
flagged `approximated`. Official 2023 uses dedicated fat/oil/nuts/seeds tables (energy
from saturates, saturated-fat ratio, protein cap at <7 negative points, different grade
bands); those are not implemented. Cheese is exempt from the protein rule (matches official).

Points = number of thresholds the value strictly exceeds.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import Literal

from app.scoring.models import Category, Product

ENERGY_KJ = (335, 670, 1005, 1340, 1675, 2010, 2345, 2680, 3015, 3350)
ENERGY_KJ_BEVERAGE = (30, 90, 150, 210, 240, 270, 300, 330, 360, 390)
SUGARS = (3.4, 6.8, 10, 14, 17, 20, 24, 27, 31, 34, 37, 41, 44, 48, 51)
SUGARS_BEVERAGE = (0.5, 2, 3.5, 5, 6, 7, 8, 9, 10, 11)
SAT_FAT = (1, 2, 3, 4, 5, 6, 7, 8, 9, 10)
SALT = (0.2, 0.4, 0.6, 0.8, 1, 1.2, 1.4, 1.6, 1.8, 2, 2.2, 2.4, 2.6, 2.8, 3, 3.2, 3.4, 3.6, 3.8, 4)
PROTEIN = (2.4, 4.8, 7.2, 9.6, 12, 14, 17)
PROTEIN_BEVERAGE = (1.2, 1.5, 1.8, 2.1, 2.4, 2.7, 3.0)
FIBRE = (3.0, 4.1, 5.2, 6.3, 7.4)
FVL = (40, 60, 80, 80, 80)
FVL_BEVERAGE = (40, 40, 60, 60, 80, 80)

SWEETENER_POINTS = 4
PROTEIN_CUTOFF_NEGATIVE_POINTS = 11  # protein not counted at or above this (non-cheese food)

# Upper bound (inclusive) of each grade, A..D; above the last is E.
GRADE_BANDS = (("A", 0), ("B", 2), ("C", 10), ("D", 18))
GRADE_BANDS_BEVERAGE = (("B", 2), ("C", 6), ("D", 9))


@dataclass(frozen=True, slots=True)
class NutriScoreResult:
    grade: Literal["A", "B", "C", "D", "E"] | None
    points: int | None
    partial: bool  # fibre/protein/fvl missing -> counted as 0
    approximated: bool  # CHEESE/FAT scored with general table
    reason: str | None  # "insufficient_data" when grade is None


def _points(value: float, thresholds: Sequence[float]) -> int:
    return sum(1 for t in thresholds if value > t)


def _grade(points: int, bands: Sequence[tuple[str, int]]) -> str:
    for grade, upper in bands:
        if points <= upper:
            return grade
    return "E"


def _effective_category(product: Product) -> Category:
    """WATER with energy, sugar or sweeteners is a flavoured drink: score it as BEVERAGE."""
    n = product.per_100g
    if product.category == Category.WATER and (
        (n.energy_kcal or 0) > 0 or (n.sugars_g or 0) > 0 or product.contains_sweeteners
    ):
        return Category.BEVERAGE
    return product.category


def compute_nutriscore(product: Product) -> NutriScoreResult:
    category = _effective_category(product)
    if category == Category.WATER:
        return NutriScoreResult("A", None, False, False, None)

    n = product.per_100g
    energy, sugars, sat, salt = n.energy_kj(), n.sugars_g, n.sat_fat_g, n.salt()
    if energy is None or sugars is None or sat is None or salt is None:
        return NutriScoreResult(None, None, False, False, "insufficient_data")

    beverage = category == Category.BEVERAGE
    approximated = category in (Category.CHEESE, Category.FAT)
    partial = n.fiber_g is None or n.protein_g is None or n.fvl_percent is None

    negative = (
        _points(energy, ENERGY_KJ_BEVERAGE if beverage else ENERGY_KJ)
        + _points(sugars, SUGARS_BEVERAGE if beverage else SUGARS)
        + _points(sat, SAT_FAT)
        + _points(salt, SALT)
    )
    if beverage and product.contains_sweeteners:
        negative += SWEETENER_POINTS

    fibre_pts = _points(n.fiber_g or 0.0, FIBRE)
    fvl_pts = _points(n.fvl_percent or 0.0, FVL_BEVERAGE if beverage else FVL)
    protein_pts = _points(n.protein_g or 0.0, PROTEIN_BEVERAGE if beverage else PROTEIN)
    if not beverage and category != Category.CHEESE and negative >= PROTEIN_CUTOFF_NEGATIVE_POINTS:
        protein_pts = 0

    points = negative - fibre_pts - fvl_pts - protein_pts
    grade = _grade(points, GRADE_BANDS_BEVERAGE if beverage else GRADE_BANDS)
    return NutriScoreResult(grade, points, partial, approximated, None)  # type: ignore[arg-type]
