"""Nutri-Score 2023 (general foods, beverages, water, fats/oils/nuts/seeds).

Specification (Santé publique France, the Nutri-Score owner; cited in
data/thresholds.yaml `sources.nutriscore_2023*`):
- foods: "Update of the Nutri-Score algorithm. Update report from the Scientific Committee of
  the Nutri-Score 2022" (fats, oils, nuts and seeds table, cheese and red-meat rules);
- beverages: "Update of the Nutri-Score algorithm for beverages. Second update report from the
  Scientific Committee of the Nutri-Score V2-2023" (milk, dairy and plant drinks are beverages;
  only water gets A);
- https://www.santepubliquefrance.fr/nutri-score (Règlement d'usage / conditions of use with
  the 2023 algorithm in its annex).
Reference implementation used to verify every table, operator and band:
`points_thresholds_2023`, `compute_nutriscore_score_2023` and `compute_nutriscore_grade_2023`
in https://github.com/openfoodfacts/openfoodfacts-server/blob/main/lib/ProductOpener/Nutriscore.pm
(E2 compares this engine with OFF's own 2023 points on 705 Indian products).

Step 0 verification (Plan 1): all tables in the plan matched EXCEPT the beverage sugars table.
  plan:     0, 1.5, 3, 4.5, 6, 7.5, 9, 10.5, 12, 13.5
  official: 0.5, 2, 3.5, 5, 6, 7, 8, 9, 10, 11   (used here)

Fats, oils, nuts and seeds (category FAT, EF1): energy is replaced by energy from saturated
fat (sat g x 37 kJ) and saturated fat by the saturated fat / total fat ratio (%); sugars and
salt use the general tables; protein is not counted at >= 7 negative points; own grade bands
(A <= -6). Total energy is not needed; total fat is (a missing fat is insufficient data).

Beverages: category BEVERAGE, a WATER with energy, sugar or sweeteners, and a GENERAL product
flagged `nutriscore_beverage` (liquid milk; see `Product.nutriscore_beverage`).

Known simplification: the red-meat protein cap (max 2 protein points) is not implemented (no
red-meat category). CHEESE is scored with the general table and exempt from the protein rule
(as in the official algorithm) and is still flagged `approximated` (Plan 1 wording).

Points = number of thresholds the value strictly exceeds, except the saturated fat ratio,
which counts thresholds the value reaches or exceeds (official table: "< 10" -> 0, ...,
">= 64" -> 10; Nutriscore.pm uses >= for this one component).
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
# Fats, oils, nuts and seeds (2022 foods report; Nutriscore.pm `energy_from_saturated_fat`,
# `saturated_fat_ratio`).
ENERGY_FROM_SAT_FAT_KJ = (120, 240, 360, 480, 600, 720, 840, 960, 1080, 1200)
SAT_FAT_RATIO_PCT = (10, 16, 22, 28, 34, 40, 46, 52, 58, 64)  # counted with >=
KJ_PER_G_SAT_FAT = 37

SWEETENER_POINTS = 4
PROTEIN_CUTOFF_NEGATIVE_POINTS = 11  # protein not counted at or above this (non-cheese food)
PROTEIN_CUTOFF_NEGATIVE_POINTS_FAT = 7  # the same for fats, oils, nuts and seeds

# Upper bound (inclusive) of each grade, A..D; above the last is E.
GRADE_BANDS = (("A", 0), ("B", 2), ("C", 10), ("D", 18))
GRADE_BANDS_BEVERAGE = (("B", 2), ("C", 6), ("D", 9))
GRADE_BANDS_FAT = (("A", -6), ("B", 2), ("C", 10), ("D", 18))


@dataclass(frozen=True, slots=True)
class NutriScoreResult:
    grade: Literal["A", "B", "C", "D", "E"] | None
    points: int | None
    partial: bool  # fibre/protein/fvl missing -> counted as 0
    approximated: bool  # CHEESE flagged (see module docstring)
    reason: str | None  # "insufficient_data" / "not_scored_supplement" when grade is None


def _points(value: float, thresholds: Sequence[float]) -> int:
    return sum(1 for t in thresholds if value > t)


def _points_inclusive(value: float, thresholds: Sequence[float]) -> int:
    return sum(1 for t in thresholds if value >= t)


def _grade(points: int, bands: Sequence[tuple[str, int]]) -> str:
    for grade, upper in bands:
        if points <= upper:
            return grade
    return "E"


def _effective_category(product: Product) -> Category:
    """WATER with energy, sugar or sweeteners is a flavoured drink: score it as BEVERAGE.
    A GENERAL product flagged `nutriscore_beverage` (liquid milk) is a BEVERAGE too."""
    n = product.per_100g
    if product.category == Category.WATER and (
        (n.energy_kcal or 0) > 0 or (n.sugars_g or 0) > 0 or product.contains_sweeteners
    ):
        return Category.BEVERAGE
    if product.category == Category.GENERAL and product.nutriscore_beverage:
        return Category.BEVERAGE
    return product.category


def _fat_negative(product: Product) -> int | None:
    """Negative points of the fats, oils, nuts and seeds table; None when an input is missing."""
    n = product.per_100g
    sugars, sat, fat, salt = n.sugars_g, n.sat_fat_g, n.fat_g, n.salt()
    if sugars is None or sat is None or fat is None or salt is None:
        return None
    ratio = sat / fat * 100 if fat > 0 else 0.0
    return (
        _points(sat * KJ_PER_G_SAT_FAT, ENERGY_FROM_SAT_FAT_KJ)
        + _points(sugars, SUGARS)
        + _points_inclusive(ratio, SAT_FAT_RATIO_PCT)
        + _points(salt, SALT)
    )


def _general_negative(product: Product, *, beverage: bool) -> int | None:
    n = product.per_100g
    energy, sugars, sat, salt = n.energy_kj(), n.sugars_g, n.sat_fat_g, n.salt()
    if energy is None or sugars is None or sat is None or salt is None:
        return None
    negative = (
        _points(energy, ENERGY_KJ_BEVERAGE if beverage else ENERGY_KJ)
        + _points(sugars, SUGARS_BEVERAGE if beverage else SUGARS)
        + _points(sat, SAT_FAT)
        + _points(salt, SALT)
    )
    if beverage and product.contains_sweeteners:
        negative += SWEETENER_POINTS
    return negative


def compute_nutriscore(product: Product) -> NutriScoreResult:
    # Nutri-Score is not designed for supplements: no grade (Plan 9 Task 7, P9-R10).
    if product.category == Category.SUPPLEMENT:
        return NutriScoreResult(None, None, False, False, "not_scored_supplement")
    category = _effective_category(product)
    if category == Category.WATER:
        return NutriScoreResult("A", None, False, False, None)

    n = product.per_100g
    beverage = category == Category.BEVERAGE
    fat = category == Category.FAT
    negative = _fat_negative(product) if fat else _general_negative(product, beverage=beverage)
    if negative is None:
        return NutriScoreResult(None, None, False, False, "insufficient_data")

    approximated = category == Category.CHEESE
    partial = n.fiber_g is None or n.protein_g is None or n.fvl_percent is None

    fibre_pts = _points(n.fiber_g or 0.0, FIBRE)
    fvl_pts = _points(n.fvl_percent or 0.0, FVL_BEVERAGE if beverage else FVL)
    protein_pts = _points(n.protein_g or 0.0, PROTEIN_BEVERAGE if beverage else PROTEIN)
    cutoff = PROTEIN_CUTOFF_NEGATIVE_POINTS_FAT if fat else PROTEIN_CUTOFF_NEGATIVE_POINTS
    if not beverage and category != Category.CHEESE and negative >= cutoff:
        protein_pts = 0

    points = negative - fibre_pts - fvl_pts - protein_pts
    bands = GRADE_BANDS_BEVERAGE if beverage else GRADE_BANDS_FAT if fat else GRADE_BANDS
    grade = _grade(points, bands)
    return NutriScoreResult(grade, points, partial, approximated, None)  # type: ignore[arg-type]
