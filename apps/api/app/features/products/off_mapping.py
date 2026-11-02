"""Map an Open Food Facts product payload to the rules engine's `Product` (health-critical).

Rules: a missing or non-numeric OFF value is None (never invented, never taken from
per-serving values). Plausibility (negative, absurd, cross-field) is left to
`Nutrients.sanitized()` in the engine; only non-finite numbers are dropped here.
OFF has no FSSAI veg dot, so `veg_mark` is always None (unknown can only make diet
checks more cautious).
"""

from __future__ import annotations

import math
import re
from dataclasses import dataclass
from typing import Any

from app.scoring import Category, Nutrients, Product

_KJ_PER_KCAL = 4.184

# categories_tags -> engine category. Order: dry/powder exclusion (GENERAL), WATER, BEVERAGE,
# CHEESE, FAT. OFF lists every ancestor, so powders and tea bags also carry `en:beverages`;
# they are per-100 g of dry product and must NOT get per-100 ml drink thresholds.
DRY_DRINK_TAGS = frozenset(
    {
        "en:beverage-preparations",
        "en:instant-beverages",
        "en:chocolate-powders",
        "en:cocoa-powders",
        "en:malted-drinks",
        "en:tea-bags",
        "en:loose-leaf-teas",
        "en:instant-teas",
        "en:ground-coffees",
        "en:coffee-beans",
        "en:instant-coffees",
        "en:dried-products-to-be-rehydrated",
        "en:dehydrated-beverages",
        "en:cocoa-and-chocolate-powders",
    }
)
# Dry leaves unless the product is also tagged as a ready-to-drink child category.
DRY_UNLESS_READY_TAGS = frozenset({"en:green-teas", "en:black-teas"})
# Best-effort lists: an unknown powder tag falls through to BEVERAGE and over-warns as a drink.
WATER_TAGS = frozenset({"en:waters"})
# en:coffees / en:teas alone are deliberately NOT here (often dry leaves/grounds);
# ready-to-drink children are. Plain en:milks stays GENERAL.
# PENDING CLINICIAN REVIEW: whether plain milk should use per-100 ml drink thresholds.
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
        "en:iced-teas",
        "en:tea-based-beverages",
        "en:coffee-drinks",
        "en:dairy-drinks",
        "en:flavoured-milks",
        "en:fermented-milk-drinks",
        "en:buttermilks",
        "en:lassi",
        "en:plant-based-milks",
        "en:plant-based-beverages",
    }
)
# Parent tags that say "a drink" but not "ready to drink".
GENERIC_DRINK_TAGS = frozenset(
    {"en:beverages", "en:non-alcoholic-beverages", "en:plant-based-beverages"}
)
CHEESE_TAGS = frozenset({"en:cheeses"})
FAT_TAGS = frozenset({"en:fats"})

# OFF allergen tag -> text the engine's matcher recognises. Anything not listed is
# passed through as the tag name with "-" -> " " (so unknown allergens still show up).
# en:nuts in OFF means tree nuts; plain "nuts" would only be a weak "possible" hit.
ALLERGEN_TEXT = {
    "en:milk": "milk",
    "en:gluten": "gluten",
    # OFF en:nuts = tree nuts. The extra "nuts" is the engine's weak peanut term, so a peanut
    # allergic member gets may_contain (cross-reactivity) but never contains.
    "en:nuts": "tree nuts, nuts",
    "en:peanuts": "peanuts",
    "en:soybeans": "soybeans",
    "en:sesame-seeds": "sesame seeds",
    "en:eggs": "eggs",
    "en:fish": "fish",
    "en:crustaceans": "crustaceans",
    "en:mustard": "mustard",
    "en:sulphur-dioxide-and-sulphites": "sulphur dioxide, sulphites",
    "en:lupin": "lupin",
    "en:celery": "celery",
    "en:molluscs": "molluscs",
    # Common non-English tags (OFF often tags by the product's country language).
    "fr:lait": "milk",
    "de:milch": "milk",
    "es:leche": "milk",
    "fr:gluten": "gluten",
    "de:gluten": "gluten",
    "fr:arachides": "peanuts",
    "de:erdnüsse": "peanuts",
    "fr:fruits-a-coque": "tree nuts, nuts",
    "de:schalenfrüchte": "tree nuts, nuts",
    "fr:soja": "soybeans",
    "de:soja": "soybeans",
    "fr:oeufs": "eggs",
    "de:eier": "eggs",
    "fr:sesame": "sesame seeds",
    "de:sesam": "sesame seeds",
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


# Languages the engine's term lists can read.
READABLE_LANGS = frozenset({"en", "hi", "mr"})
# Intense/low-calorie sweetener E-numbers (not sugar alcohols such as E420/E421).
SWEETENER_E_NUMBERS = frozenset(
    {950, 951, 952, 954, 955, 957, 959, 960, 961, 962, 965, 966, 967, 968, 969}
)
_ADDITIVE_TAG = re.compile(r"^en:e(\d{3,4})[a-z]?$")
_G_ML = r"(?:g|gm|gms|grams?|ml)"
_LEADING_AMOUNT = re.compile(rf"^\s*(\d+(?:\.\d+)?)\s*{_G_ML}\b", re.IGNORECASE)
_PAREN_AMOUNT = re.compile(rf"\(\s*(\d+(?:\.\d+)?)\s*{_G_ML}\s*\)", re.IGNORECASE)
# Any amount with a unit (also units we reject: litres, kg, oz), comma decimals included.
_ANY_AMOUNT = re.compile(
    r"(\d+(?:[.,]\d+)?)\s*(?:g|gm|gms|grams?|ml|cl|dl|l|litres?|liters?|kg|oz)\b", re.IGNORECASE
)
_MULTIPLIER = re.compile(r"\d\s*[x\u00d7]\s*\d", re.IGNORECASE)

# Common non-English ingredient words that are NOT English words. A text containing any of
# these is treated as unreadable even if labelled en/hi/mr (OFF language labels are unreliable).
FOREIGN_INGREDIENT_WORDS = frozenset(
    {
        "lait",
        "sucre",
        "farine",
        "huile",
        "beurre",
        "oeuf",
        "oeufs",
        "\u0153ufs",
        "noisettes",
        "poudre",
        "entier",
        "eau",
        "milch",
        "zucker",
        "mehl",
        "eier",
        "vollmilch",
        "vollmilchpulver",
        "leche",
        "az\u00facar",
        "azucar",
        "harina",
        "aceite",
        "huevos",
        "agua",
    }
)
_WORD = re.compile(r"[^\W\d_]+")


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
    per = product.get("nutrition_data_per")
    if isinstance(per, str) and per.strip().lower() == "serving":
        return Nutrients()  # *_100g values are derived from per-serving: never trust (M1)

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
    if found & DRY_DRINK_TAGS:
        return Category.GENERAL
    ready = found & (BEVERAGE_TAGS - GENERIC_DRINK_TAGS)
    if found & DRY_UNLESS_READY_TAGS and not ready:
        return Category.GENERAL
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


def _serving_from_text(size: str) -> float | None:
    """Exactly one explicit g/ml amount: a leading "30 g" or a parenthesised "(500 ml)".

    Rejects multipliers ("2 x 15 g"), litres, comma decimals and two different amounts.
    """
    if _MULTIPLIER.search(size):
        return None
    amounts = {a.replace(",", ".") for a in _ANY_AMOUNT.findall(size)}
    if len(amounts) != 1:
        return None
    candidates = {float(m) for m in _PAREN_AMOUNT.findall(size)}
    if (lead := _LEADING_AMOUNT.match(size)) is not None:
        candidates.add(float(lead.group(1)))
    if len(candidates) != 1:
        return None
    value = candidates.pop()
    return value if float(next(iter(amounts))) == value else None


def _serving_size(product: dict) -> float | None:
    """Grams/ml per serving, only from an explicit g/ml amount (never guess the unit)."""
    unit = _text(product.get("serving_quantity_unit"))
    if unit is not None and unit.lower() in ("g", "ml"):
        qty = _num(product.get("serving_quantity"))
        if qty is not None:
            return qty
    size = _text(product.get("serving_size"))
    return _serving_from_text(size) if size is not None else None


def _lang_prefix(value: Any) -> str | None:
    text = _text(value)
    return text.lower().replace("_", "-").split("-")[0] if text else None


def _looks_foreign(text: str) -> bool:
    return any(w in FOREIGN_INGREDIENT_WORDS for w in _WORD.findall(text.lower()))


def _ingredient_items(product: dict) -> tuple[str, ...]:
    """Union of every text the engine can read, main language first, de-duplicated.

    `ingredients_text` is used only when its language (ingredients_lc, else lang) is en/hi/mr;
    unreadable text (e.g. French) must not count as a known ingredient list.
    """
    texts: list[str | None] = []
    main_lang = _lang_prefix(product.get("ingredients_lc")) or _lang_prefix(product.get("lang"))
    if main_lang in READABLE_LANGS:
        texts.append(_text(product.get("ingredients_text")))
    texts += [_text(product.get(f"ingredients_text_{lang}")) for lang in ("en", "hi", "mr")]
    items: dict[str, None] = {}
    for text in texts:
        if text is not None and _looks_foreign(text):
            continue
        for item in split_ingredients(text):
            items.setdefault(item, None)
    return tuple(items)


def _contains_sweeteners(product: dict) -> bool:
    for tag in _tags(product, "additives_tags"):
        m = _ADDITIVE_TAG.match(tag)
        if m and int(m.group(1)) in SWEETENER_E_NUMBERS:
            return True
    return False


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
    claims = tuple(
        dict.fromkeys(CLAIM_TAGS[t] for t in _tags(product, "labels_tags") if t in CLAIM_TAGS)
    )
    return Product(
        name=_text(product.get("product_name")) or "",
        category=_category(_tags(product, "categories_tags")),
        per_100g=_nutriments(product),
        serving_size_g=_serving_size(product),
        ingredients=_ingredient_items(product),
        allergen_statement=_statement("Contains: ", _tags(product, "allergens_tags")),
        may_contain_statement=_statement("May contain: ", _tags(product, "traces_tags")),
        claims=claims,
        veg_mark=None,
        contains_sweeteners=_contains_sweeteners(product),
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
