from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field, fields, replace
from enum import StrEnum
from typing import Any, Literal

# Physical plausibility limits (not health thresholds).
MAX_GRAMS_PER_100 = 100.0
MAX_SODIUM_MG_PER_100 = 40000.0
MAX_ENERGY_KCAL_PER_100 = 900.0
MAX_FVL_PERCENT = 100.0


class Category(StrEnum):
    GENERAL = "general"
    BEVERAGE = "beverage"
    WATER = "water"
    CHEESE = "cheese"
    FAT = "fat"


class Status(StrEnum):
    OK = "ok"
    CAUTION = "caution"
    UNKNOWN = "unknown"
    AVOID = "avoid"

    @property
    def rank(self) -> int:
        return _STATUS_RANK[self.value]


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
        if self.salt_g is not None:
            return self.salt_g
        if self.sodium_mg is not None:
            return self.sodium_mg * 2.5 / 1000
        return None

    def energy_kj(self) -> float | None:
        if self.energy_kcal is None:
            return None
        return self.energy_kcal * 4.184

    def sanitized(self) -> tuple[Nutrients, tuple[str, ...]]:
        dropped: list[str] = []
        updates: dict[str, None] = {}
        for f in fields(self):
            value = getattr(self, f.name)
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
                updates[f.name] = None
                dropped.append(f.name)
        return replace(self, **updates), tuple(dropped)


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

    @property
    def is_drink(self) -> bool:
        return self.category in (Category.BEVERAGE, Category.WATER)

    def per_serving(self, value_per_100g: float | None) -> float | None:
        if value_per_100g is None or self.serving_size_g is None:
            return None
        return value_per_100g * self.serving_size_g / 100


@dataclass(frozen=True, slots=True)
class Member:
    id: str
    name: str
    age: int | None = None
    diet: Diet = Diet.NON_VEG
    allergens: tuple[str, ...] = ()
    conditions: tuple[str, ...] = ()
    goal: str | None = None


@dataclass(frozen=True, slots=True)
class Reason:
    code: str
    severity: Status
    params: Mapping[str, Any] = field(default_factory=dict)
