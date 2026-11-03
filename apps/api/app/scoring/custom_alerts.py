"""Member-chosen ingredient alerts (palm oil, maida, added sugar, sweeteners, MSG).

Alerts are preferences, not safety rules: a match adds one CAUTION `custom_alert` reason
per enabled alert, and never lowers another reason. With no usable ingredient list there is
no alert reason; the existing rules already report what unknown ingredients mean for the
member (Ruling P4). A match is reported at any extraction confidence, because a match is
evidence; the low-confidence UNKNOWN comes from the other rules.
"""

from __future__ import annotations

from app.scoring.config import ScoringConfig
from app.scoring.ingredients import find_terms, has_ingredient_content
from app.scoring.models import CUSTOM_ALERT_KEYS, Member, Product, Reason, Status
from app.scoring.warnings import added_sugar_terms

CUSTOM_ALERT_CODE = "custom_alert"


def _hits(product: Product, key: str, cfg: ScoringConfig) -> list[str]:
    if key == "added_sugar":
        return sorted(added_sugar_terms(product, cfg))
    entry = cfg.ingredient_lists["custom_alerts"][key]
    return sorted(find_terms(product.ingredients, entry["terms"], entry.get("exclude") or ()))


def custom_alert_reasons(product: Product, member: Member, cfg: ScoringConfig) -> list[Reason]:
    """One CAUTION reason per enabled alert that matches, in CUSTOM_ALERT_KEYS order.

    Unknown alert keys on the member are ignored, never raised.
    """
    if not member.custom_alerts or not has_ingredient_content(product.ingredients):
        return []
    enabled = set(member.custom_alerts)
    reasons: list[Reason] = []
    for key in CUSTOM_ALERT_KEYS:
        if key not in enabled:
            continue
        hits = _hits(product, key, cfg)
        if hits:
            reasons.append(
                Reason(CUSTOM_ALERT_CODE, Status.CAUTION, {"alert": key, "ingredients": hits})
            )
    return reasons
