"""Diet checks (veg / eggetarian / vegan / jain) and veg-mark mismatch."""

from __future__ import annotations

from app.scoring.allergens import ingredients_known
from app.scoring.config import ScoringConfig
from app.scoring.ingredients import find_terms
from app.scoring.models import Diet, Member, Product, Reason, Status

_TERM_LISTS: dict[Diet, tuple[str, ...]] = {
    Diet.VEG: ("non_veg", "egg"),
    Diet.EGGETARIAN: ("non_veg",),
    Diet.VEGAN: ("non_veg", "egg", "dairy", "animal_other"),
    Diet.JAIN: ("non_veg", "egg", "animal_other", "jain_exclusions"),
    Diet.NON_VEG: (),
}


def diet_violations(product: Product, cfg: ScoringConfig) -> dict[Diet, tuple[str, ...]]:
    result: dict[Diet, tuple[str, ...]] = {}
    for diet, lists in _TERM_LISTS.items():
        terms = [t for name in lists for t in cfg.diet.get(name, [])]
        if not terms or not product.ingredients:
            result[diet] = ()
        else:
            result[diet] = tuple(find_terms(product.ingredients, terms))
    return result


def veg_mark_mismatch(product: Product, cfg: ScoringConfig) -> bool:
    return product.veg_mark == "veg" and bool(diet_violations(product, cfg)[Diet.VEG])


def diet_reasons(product: Product, member: Member, cfg: ScoringConfig) -> list[Reason]:
    diet = member.diet
    reasons: list[Reason] = []
    violations = diet_violations(product, cfg)[diet]
    if violations:
        reasons.append(
            Reason(
                "diet_violation",
                Status.AVOID,
                {"diet": diet.value, "ingredients": list(violations)},
            )
        )
    if diet != Diet.NON_VEG and not ingredients_known(product, cfg):
        trusted_mark = diet in (Diet.VEG, Diet.EGGETARIAN) and product.veg_mark == "veg"
        if not trusted_mark:
            reasons.append(Reason("diet_unknown", Status.UNKNOWN, {"diet": diet.value}))
    return reasons
