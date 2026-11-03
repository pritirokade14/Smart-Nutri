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
    protein isolate/concentrate) or has at least `suspect_min_protein_g` protein per 100 g."""
    if product.category == Category.SUPPLEMENT:
        return False
    s = (cfg or load_config()).thresholds["supplements"]
    protein = product.per_100g.protein_g
    if protein is not None and protein >= s["suspect_min_protein_g"]:
        return True
    return bool(find_terms(product.ingredients, s["suspect_terms"]))


def hides_supplement_suspects(member: Member, cfg: ScoringConfig | None = None) -> bool:
    """Protein-sorted lists for this member leave suspects out: a known age under
    `supplements.child_max_age`, or an unknown age (the protective reading)."""
    limit = (cfg or load_config()).thresholds["supplements"]["child_max_age"]
    return member.age is None or member.age < limit
