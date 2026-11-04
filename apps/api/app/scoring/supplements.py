"""Supplement-suspect hint (P9 safety S5). Pure and deterministic: never an LLM.

Not a verdict rule: `analyze()` never reads it. It drives two things only:
- the confirm screen's `category_suggestion` ("supplement"), which never sets the category;
- leaving suspects out of protein-sorted search and alternatives for members under
  `supplements.child_max_age` (or of unknown age).
"""

from __future__ import annotations

from app.scoring.config import ScoringConfig, load_config
from app.scoring.ingredients import find_terms
from app.scoring.models import Category, Member, Product


def supplement_suspect(product: Product, cfg: ScoringConfig | None = None) -> bool:
    """A product not already a supplement that lists a `suspect_terms` ingredient (a whey or
    protein isolate/concentrate), or has at least `suspect_min_protein_g` protein per 100 g and
    is not a naturally high-protein whole food (`_whole_food`: legumes, soya chunks, dairy)."""
    if product.category == Category.SUPPLEMENT:
        return False
    s = (cfg or load_config()).thresholds["supplements"]
    if find_terms(product.ingredients, s["suspect_terms"]):
        return True
    protein = product.per_100g.protein_g
    return (
        protein is not None
        and protein >= s["suspect_min_protein_g"]
        and not _whole_food(product, s)
    )


def _whole_food(product: Product, s: dict) -> bool:
    """A dairy category, or a first ingredient that is a legume, soya or dairy food, with no
    ingredient naming a protein ("pea protein", "soy protein": then it may be a powder)."""
    if find_terms(product.ingredients, s["suspect_protein_words"]):
        return False
    if product.category.value in s["suspect_whole_food_categories"]:
        return True
    first = product.ingredients[:1]
    return bool(first and find_terms(first, s["suspect_whole_food_terms"]))


def hides_supplement_suspects(member: Member, cfg: ScoringConfig | None = None) -> bool:
    """Protein-sorted lists for this member leave suspects out: a known age under
    `supplements.child_max_age`, or an unknown age (the protective reading)."""
    limit = (cfg or load_config()).thresholds["supplements"]["child_max_age"]
    return member.age is None or member.age < limit
