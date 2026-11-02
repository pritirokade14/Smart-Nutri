"""FSSAI-style "high in" warnings and ingredient-list hits."""

from __future__ import annotations

from app.scoring.config import ScoringConfig
from app.scoring.ingredients import find_terms
from app.scoring.models import Product

_HIGH_IN_ORDER = (
    ("sugar", "sugars_g"),
    ("fat", "fat_g"),
    ("sat_fat", "sat_fat_g"),
    ("salt", "salt_g"),
)


def high_in(product: Product, cfg: ScoringConfig) -> tuple[str, ...]:
    limits = cfg.thresholds["high_in"]["drink" if product.is_drink else "food"]
    n = product.per_100g
    values = {
        "sugars_g": n.sugars_g,
        "fat_g": n.fat_g,
        "sat_fat_g": n.sat_fat_g,
        "salt_g": n.salt(),
    }
    return tuple(
        name for name, key in _HIGH_IN_ORDER if values[key] is not None and values[key] > limits[key]
    )


def ingredient_hits(product: Product, cfg: ScoringConfig, list_name: str) -> tuple[str, ...]:
    return tuple(sorted(find_terms(product.ingredients, cfg.ingredient_lists[list_name])))


def hidden_sugars(product: Product, cfg: ScoringConfig) -> tuple[str, ...]:
    return ingredient_hits(product, cfg, "hidden_sugars")


def added_sugar_terms(product: Product, cfg: ScoringConfig) -> tuple[str, ...]:
    terms = [*cfg.ingredient_lists["added_sugars"], *cfg.ingredient_lists["hidden_sugars"]]
    return tuple(sorted(find_terms(product.ingredients, terms)))


def sodium_additives(product: Product, cfg: ScoringConfig) -> tuple[str, ...]:
    return ingredient_hits(product, cfg, "sodium_additives")
