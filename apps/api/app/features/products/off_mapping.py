"""Map an Open Food Facts product payload to the rules engine's `Product` (health-critical).

Rules: a missing or non-numeric OFF value is None (never invented, never taken from
per-serving values). Plausibility (negative, absurd, cross-field) is left to
`Nutrients.sanitized()` in the engine; only non-finite numbers are dropped here.
OFF has no FSSAI veg dot, so `veg_mark` is always None (unknown can only make diet
checks more cautious).
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Any

from app.scoring import Category, Nutrients, Product

_KJ_PER_KCAL = 4.184

# categories_tags -> engine category. First match wins, in this order.
# OFF lists every ancestor, so `en:beverages` covers most drinks; the extra tags
# keep drinks that are tagged only by a child category on per-100 ml thresholds.
WATER_TAGS = frozenset({"en:waters"})
BEVERAGE_TAGS = frozenset(
    {
        "en:beverages",
        "en:non-alcoholic-beverages",
        "en:alcoholic-beverages",
        "en:carbonated-drinks",
        "en:sodas",
        "en:sweetened-beverages",
        "en:artificially-sweetened-beverages",
        "en:fruit-juices",
        "en:juices-and-nectars",
        "en:energy-drinks",
        "en:plant-based-beverages",
        "en:teas",
        "en:coffees",
        "en:iced-teas",
    }
)
CHEESE_TAGS = frozenset({"en:cheeses"})
FAT_TAGS = frozenset({"en:fats"})

# OFF allergen tag -> text the engine's matcher recognises. Anything not listed is
# passed through as the tag name with "-" -> " " (so unknown allergens still show up).
# en:nuts in OFF means tree nuts; plain "nuts" would only be a weak "possible" hit.
ALLERGEN_TEXT = {
    "en:milk": "milk",
    "en:gluten": "gluten",
    "en:nuts": "tree nuts",
    "en:peanuts": "peanuts",
    "en:soybeans": "soybeans",
    "en:sesame-seeds": "sesame seeds",
    "en:eggs": "eggs",
    "en:fish": "fish",
    "en:crustaceans": "crustaceans",
    "en:mustard": "mustard",
    "en:sulphur-dioxide-and-sulphites": "sulphur dioxide, sulphites",
}

# labels_tags -> claim text the engine's claim matcher recognises. Exact tags only.
CLAIM_TAGS = {
    "en:no-added-sugar": "no added sugar",
    "en:sugar-free": "sugar free",
    "en:low-sugar": "low sugar",
    "en:low-fat": "low fat",
    "en:low-salt": "low salt",
    "en:high-protein": "high protein",
    "en:source-of-protein": "source of protein",
}


@dataclass(frozen=True, slots=True)
class ProductInfo:
    barcode: str
    name: str | None
    brand: str | None
    image_url: str | None


def _num(value: Any) -> float | None:
    """A finite float from a number or numeric string, else None (bool is not a number)."""
    if value is None or isinstance(value, bool):
        return None
    try:
        v = float(value.strip() if isinstance(value, str) else value)
    except (TypeError, ValueError):
        return None
    return v if math.isfinite(v) else None


def _text(value: Any) -> str | None:
    if isinstance(value, str) and value.strip():
        return value.strip()
    return None


def _unwrap(payload: dict) -> tuple[dict, str | None]:
    """Accept the v3 envelope ({"code", "product"}) or the bare product dict."""
    inner = payload.get("product")
    if isinstance(inner, dict):
        return inner, _text(str(payload["code"])) if payload.get("code") else None
    return payload, None


def _tags(product: dict, key: str) -> list[str]:
    raw = product.get(key)
    if not isinstance(raw, list):
        return []
    return [t.strip().lower() for t in raw if isinstance(t, str) and t.strip()]


def _nutriments(product: dict) -> Nutrients:
    raw = product.get("nutriments")
    nm: dict = raw if isinstance(raw, dict) else {}

    energy = _num(nm.get("energy-kcal_100g"))
    if energy is None:
        kj = _num(nm.get("energy-kj_100g"))
        if kj is None:
            kj = _num(nm.get("energy_100g"))  # OFF's energy_100g is kJ
        energy = None if kj is None else kj / _KJ_PER_KCAL

    sodium_g = _num(nm.get("sodium_100g"))  # OFF gives sodium in grams
    return Nutrients(
        energy_kcal=energy,
        protein_g=_num(nm.get("proteins_100g")),
        carbs_g=_num(nm.get("carbohydrates_100g")),
        sugars_g=_num(nm.get("sugars_100g")),
        fat_g=_num(nm.get("fat_100g")),
        sat_fat_g=_num(nm.get("saturated-fat_100g")),
        fiber_g=_num(nm.get("fiber_100g")),
        salt_g=_num(nm.get("salt_100g")),
        sodium_mg=None if sodium_g is None else sodium_g * 1000,
        fvl_percent=_num(nm.get("fruits-vegetables-legumes-estimate-from-ingredients_100g")),
    )


def _category(tags: list[str]) -> Category:
    found = set(tags)
    if found & WATER_TAGS:
        return Category.WATER
    if found & BEVERAGE_TAGS:
        return Category.BEVERAGE
    if found & CHEESE_TAGS:
        return Category.CHEESE
    if found & FAT_TAGS:
        return Category.FAT
    return Category.GENERAL


def _allergen_text(tag: str) -> str:
    if tag in ALLERGEN_TEXT:
        return ALLERGEN_TEXT[tag]
    return tag.split(":")[-1].replace("-", " ")


def _statement(prefix: str, tags: list[str]) -> str | None:
    if not tags:
        return None
    return prefix + ", ".join(dict.fromkeys(_allergen_text(t) for t in tags))


def _serving_size(product: dict) -> float | None:
    unit = _text(product.get("serving_quantity_unit"))
    if unit is not None and unit.lower() not in ("g", "ml"):
        return None
    return _num(product.get("serving_quantity"))


def split_ingredients(text: str | None) -> tuple[str, ...]:
    """Split on commas/semicolons outside parentheses/brackets; strip; drop empties."""
    if not text:
        return ()
    parts: list[str] = []
    depth = 0
    start = 0
    for i, ch in enumerate(text):
        if ch in "([{":
            depth += 1
        elif ch in ")]}":
            depth = max(0, depth - 1)
        elif ch in ",;" and depth == 0:
            parts.append(text[start:i])
            start = i + 1
    parts.append(text[start:])
    return tuple(p.strip() for p in parts if p.strip())


def off_to_product(payload: dict, *, confidence: float) -> Product:
    product, _ = _unwrap(payload)
    ingredients_text = _text(product.get("ingredients_text_en")) or _text(
        product.get("ingredients_text")
    )
    claims = tuple(
        dict.fromkeys(CLAIM_TAGS[t] for t in _tags(product, "labels_tags") if t in CLAIM_TAGS)
    )
    return Product(
        name=_text(product.get("product_name")) or "",
        category=_category(_tags(product, "categories_tags")),
        per_100g=_nutriments(product),
        serving_size_g=_serving_size(product),
        ingredients=split_ingredients(ingredients_text),
        allergen_statement=_statement("Contains: ", _tags(product, "allergens_tags")),
        may_contain_statement=_statement("May contain: ", _tags(product, "traces_tags")),
        claims=claims,
        veg_mark=None,
        extraction_confidence=confidence,
    )


def off_to_info(payload: dict) -> ProductInfo:
    product, outer_code = _unwrap(payload)
    code = _text(str(product["code"])) if product.get("code") else None
    brands = _text(product.get("brands"))
    brand = _text(brands.split(",")[0]) if brands else None
    return ProductInfo(
        barcode=code or outer_code or "",
        name=_text(product.get("product_name")),
        brand=brand,
        image_url=_text(product.get("image_front_url")) or _text(product.get("image_url")),
    )
