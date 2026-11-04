"""Member-chosen ingredient alerts (palm oil, maida, added sugar, sweeteners, MSG).

Alerts are preferences, not safety rules, but unknown is never OK (Ruling P7):

- a match adds one CAUTION `custom_alert` reason per enabled alert. A match is reported at
  any extraction confidence, because a match is evidence;
- the Open Food Facts `contains_sweeteners` flag raises `artificial_sweetener` with an empty
  `ingredients` list when no term matched;
- when the ingredients are not known (no usable list, or extraction confidence below
  `min_extraction_confidence`), every enabled alert that did not match is listed in one
  UNKNOWN `custom_alert_unknown` reason, so the member never gets `ok` by default.

Alerts never lower another reason.
"""

from __future__ import annotations

from app.scoring.allergens import ingredients_known
from app.scoring.config import ScoringConfig
from app.scoring.ingredients import find_terms, has_ingredient_content
from app.scoring.models import CUSTOM_ALERT_KEYS, Member, Product, Reason, Status
from app.scoring.warnings import added_sugar_terms

CUSTOM_ALERT_CODE = "custom_alert"
CUSTOM_ALERT_UNKNOWN_CODE = "custom_alert_unknown"
_SWEETENER_ALERT = "artificial_sweetener"


def _hits(product: Product, key: str, cfg: ScoringConfig) -> list[str]:
    if key == "added_sugar":
        return sorted(added_sugar_terms(product, cfg))
    entry = cfg.ingredient_lists["custom_alerts"][key]
    return sorted(find_terms(product.ingredients, entry["terms"], entry.get("exclude") or ()))


def custom_alert_reasons(product: Product, member: Member, cfg: ScoringConfig) -> list[Reason]:
    """CAUTION `custom_alert` reasons for enabled alerts that match, in CUSTOM_ALERT_KEYS
    order, then one UNKNOWN `custom_alert_unknown` for the unmatched enabled alerts when
    the ingredients are not known.

    Unknown alert keys on the member are ignored, never raised.
    """
    enabled = set(member.custom_alerts)
    keys = [k for k in CUSTOM_ALERT_KEYS if k in enabled]
    if not keys:
        return []
    readable = has_ingredient_content(product.ingredients)
    reasons: list[Reason] = []
    unmatched: list[str] = []
    for key in keys:
        hits = _hits(product, key, cfg) if readable else []
        if hits or (key == _SWEETENER_ALERT and product.contains_sweeteners):
            reasons.append(
                Reason(CUSTOM_ALERT_CODE, Status.CAUTION, {"alert": key, "ingredients": hits})
            )
        else:
            unmatched.append(key)
    if unmatched and not ingredients_known(product, cfg):
        reasons.append(Reason(CUSTOM_ALERT_UNKNOWN_CODE, Status.UNKNOWN, {"alerts": unmatched}))
    return reasons
