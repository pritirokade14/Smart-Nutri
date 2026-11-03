from __future__ import annotations

import math
from collections.abc import Iterable, Mapping
from dataclasses import dataclass, field, fields, replace
from enum import StrEnum
from typing import Any, Literal

# Physical plausibility limits (not health thresholds).
MAX_GRAMS_PER_100 = 100.0
MAX_SODIUM_MG_PER_100 = 40000.0
MAX_ENERGY_KCAL_PER_100 = 900.0
MAX_FVL_PERCENT = 100.0
MAX_SERVING_SIZE_G = 5000.0  # a serving must be finite and 0 < s <= this
# Cross-field plausibility (Ruling R23): rounding tolerance and the macro-sum ceiling.
CROSS_FIELD_TOLERANCE_G = 0.5
MAX_MACROS_SUM_G = 105.0


class Category(StrEnum):
    GENERAL = "general"
    BEVERAGE = "beverage"
    WATER = "water"
    CHEESE = "cheese"
    FAT = "fat"
    # Protein powders, whey and health supplements (Plan 9, P9-R10): never graded, never
    # suggested. Set only from the user's pick or Open Food Facts tags, never the LLM.
    SUPPLEMENT = "supplement"


class Status(StrEnum):
    """Verdict status.

    WARNING: Status is a StrEnum, so `<`, `>`, `max()` and `sorted()` compare the
    string values ALPHABETICALLY ("avoid" < "caution" < "ok" < "unknown"), which is
    not the severity order. Always compare with `.rank` or use `Status.worst()`.
    """

    OK = "ok"
    CAUTION = "caution"
    UNKNOWN = "unknown"
    AVOID = "avoid"

    @property
    def rank(self) -> int:
        return _STATUS_RANK[self.value]

    @classmethod
    def worst(cls, statuses: Iterable[Status]) -> Status:
        """Most severe status by rank (avoid > unknown > caution > ok); OK when empty."""
        return max(statuses, key=lambda s: s.rank, default=cls.OK)


_STATUS_RANK = {"ok": 0, "caution": 1, "unknown": 2, "avoid": 3}


class AllergenState(StrEnum):
    CONTAINS = "contains"
    MAY_CONTAIN = "may_contain"
    UNKNOWN = "unknown"


class Diet(StrEnum):
    VEG = "veg"
    EGGETARIAN = "eggetarian"
    VEGAN = "vegan"
    JAIN = "jain"
    NON_VEG = "non_veg"


class ClaimVerdict(StrEnum):
    SUPPORTED = "supported"
    CONTRADICTED = "contradicted"
    UNVERIFIABLE = "unverifiable"


@dataclass(frozen=True, slots=True)
class Nutrients:
    """Per 100 g / 100 ml; None = unknown."""

    energy_kcal: float | None = None
    protein_g: float | None = None
    carbs_g: float | None = None
    sugars_g: float | None = None
    fat_g: float | None = None
    sat_fat_g: float | None = None
    fiber_g: float | None = None
    salt_g: float | None = None
    sodium_mg: float | None = None
    fvl_percent: float | None = None

    def salt(self) -> float | None:
        """Salt in g; when both salt and sodium are given, the HIGHER value wins (Ruling R22)."""
        candidates = []
        if self.salt_g is not None:
            candidates.append(self.salt_g)
        if self.sodium_mg is not None:
            candidates.append(self.sodium_mg * 2.5 / 1000)
        return max(candidates) if candidates else None

    def energy_kj(self) -> float | None:
        if self.energy_kcal is None:
            return None
        return self.energy_kcal * 4.184

    def sanitized(self) -> tuple[Nutrients, tuple[str, ...]]:
        """Drop physically implausible values (per field, then across fields)."""
        drop: set[str] = set()
        values: dict[str, float | None] = {}
        for f in fields(self):
            value = getattr(self, f.name)
            values[f.name] = value
            if value is None:
                continue
            if f.name == "sodium_mg":
                upper = MAX_SODIUM_MG_PER_100
            elif f.name == "energy_kcal":
                upper = MAX_ENERGY_KCAL_PER_100
            elif f.name == "fvl_percent":
                upper = MAX_FVL_PERCENT
            else:
                upper = MAX_GRAMS_PER_100
            if not (0 <= value <= upper):
                drop.add(f.name)
                values[f.name] = None

        # Cross-field checks run on the per-field-sanitised values (Ruling R23).
        for part, whole in (("sugars_g", "carbs_g"), ("sat_fat_g", "fat_g")):
            p, w = values[part], values[whole]
            if p is not None and w is not None and p > w + CROSS_FIELD_TOLERANCE_G:
                drop |= {part, whole}
        macros = {m: v for m in ("protein_g", "carbs_g", "fat_g") if (v := values[m]) is not None}
        if sum(macros.values()) > MAX_MACROS_SUM_G:
            drop |= set(macros)

        dropped = tuple(f.name for f in fields(self) if f.name in drop)
        return replace(self, **dict.fromkeys(dropped)), dropped


def _reject_bare_str(obj: object, names: tuple[str, ...]) -> None:
    for name in names:
        if isinstance(getattr(obj, name), str):
            raise TypeError(f"{type(obj).__name__}.{name} must be a tuple of str, not a bare str")


def _plausible_serving(value: float | None) -> bool:
    if value is None:
        return True
    try:
        v = float(value)
    except (TypeError, ValueError):
        return False
    return math.isfinite(v) and 0 < v <= MAX_SERVING_SIZE_G


@dataclass(frozen=True, slots=True)
class Product:
    name: str
    category: Category = Category.GENERAL
    per_100g: Nutrients = Nutrients()
    serving_size_g: float | None = None
    ingredients: tuple[str, ...] = ()
    allergen_statement: str | None = None
    may_contain_statement: str | None = None
    claims: tuple[str, ...] = ()
    veg_mark: Literal["veg", "non_veg"] | None = None
    contains_sweeteners: bool = False
    extraction_confidence: float = 1.0

    def __post_init__(self) -> None:
        _reject_bare_str(self, ("ingredients", "claims"))

    @property
    def is_drink(self) -> bool:
        return self.category in (Category.BEVERAGE, Category.WATER)

    def per_serving(self, value_per_100g: float | None) -> float | None:
        if value_per_100g is None or self.serving_size_g is None:
            return None
        return value_per_100g * self.serving_size_g / 100

    def sanitized(self) -> tuple[Product, tuple[str, ...]]:
        """Drop implausible nutrients and serving size; returns (clean, dropped field names)."""
        clean, dropped = self.per_100g.sanitized()
        updates: dict[str, Any] = {"per_100g": clean}
        if not _plausible_serving(self.serving_size_g):
            updates["serving_size_g"] = None
            dropped = (*dropped, "serving_size_g")
        return replace(self, **updates), dropped


@dataclass(frozen=True, slots=True)
class ProteinFacts:
    """Protein numbers for the protein guide (Plan 9 Task 4). Information only: they never
    change a verdict. All rounded to 1 dp from the SANITISED product; a missing input is None,
    never 0."""

    per_100g: float | None
    per_serving: float | None  # None without serving_size_g (Product.per_serving)
    per_100kcal: float | None  # protein_g / energy_kcal * 100; None if either is None or kcal == 0
    serving_size_g: float | None


@dataclass(frozen=True, slots=True)
class Member:
    id: str
    name: str
    age: int | None = None
    diet: Diet = Diet.NON_VEG
    allergens: tuple[str, ...] = ()
    conditions: tuple[str, ...] = ()
    goal: str | None = None
    custom_alerts: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        _reject_bare_str(self, ("allergens", "conditions", "custom_alerts"))


# Ingredient alerts a member can switch on (preferences, not safety rules). The order is
# the order of `custom_alert` reasons. Terms: data/ingredients.yaml `custom_alerts`;
# `added_sugar` reuses the added_sugars + hidden_sugars lists.
CUSTOM_ALERT_KEYS: tuple[str, ...] = (
    "palm_oil",
    "maida",
    "added_sugar",
    "artificial_sweetener",
    "msg",
)


@dataclass(frozen=True, slots=True)
class Reason:
    code: str
    severity: Status
    params: Mapping[str, Any] = field(default_factory=dict)
