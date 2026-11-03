"""The data behind "How we score": live rule values plus their sources.

Every value is copied from the loaded config or the Nutri-Score constants, never written by
hand here. The `/v1/methodology` route that serves this is M5 (Plan 7).
"""

from __future__ import annotations

import copy
import hashlib
import json
from dataclasses import asdict
from typing import Any

from app.scoring.config import ScoringConfig, load_config
from app.scoring.models import CUSTOM_ALERT_KEYS
from app.scoring.nutriscore import GRADE_BANDS, GRADE_BANDS_BEVERAGE

SECTION_IDS: tuple[str, ...] = (
    "nutriscore_2023",
    "high_in",
    "allergens",
    "diet",
    "claims",
    "blood_sugar",
    "hypertension",
    "weight_loss",
    "child",
    "infant",
    "custom_alerts",
)
_CONDITION_GROUPS = ("blood_sugar", "hypertension", "weight_loss", "child", "infant")

# Health thresholds stay PENDING CLINICIAN REVIEW (thresholds.yaml header) until a clinician
# signs off in an ADR; flip this in the same change.
PENDING_CLINICIAN_REVIEW = True


def _bands(bands: tuple[tuple[str, int], ...]) -> list[dict[str, Any]]:
    return [{"grade": grade, "max_points": points} for grade, points in bands]


def _nutriscore() -> dict[str, Any]:
    return {"food": _bands(GRADE_BANDS), "beverage": _bands(GRADE_BANDS_BEVERAGE)}


def _custom_alerts(cfg: ScoringConfig) -> dict[str, Any]:
    lists = cfg.ingredient_lists
    out: dict[str, Any] = {}
    for key in CUSTOM_ALERT_KEYS:
        if key == "added_sugar":
            out[key] = {"terms": [*lists["added_sugars"], *lists["hidden_sugars"]], "exclude": []}
        else:
            out[key] = lists["custom_alerts"][key]
    return out


def _thresholds(section_id: str, cfg: ScoringConfig) -> Any:
    if section_id == "nutriscore_2023":
        return _nutriscore()
    if section_id in ("high_in", "claims"):
        return cfg.thresholds[section_id]
    if section_id in _CONDITION_GROUPS:
        return cfg.thresholds["conditions"][section_id]
    if section_id == "allergens":
        return cfg.allergens
    if section_id == "diet":
        return cfg.diet
    if section_id == "custom_alerts":
        return _custom_alerts(cfg)
    raise KeyError(section_id)


def _version(cfg: ScoringConfig) -> str:
    """sha256[:12] of the whole config plus the Nutri-Score bands (Ruling P5-R9).

    Deterministic for any `cfg`, and it changes whenever a shown value changes.
    """
    payload = {"config": asdict(cfg), "nutriscore_2023": _nutriscore()}
    text = json.dumps(payload, sort_keys=True, ensure_ascii=False, separators=(",", ":"))
    return hashlib.sha256(text.encode("utf-8")).hexdigest()[:12]


def methodology(cfg: ScoringConfig | None = None) -> dict[str, Any]:
    """{version, pending_clinician_review, sections: [{id, source, thresholds}], sources}.

    Returns fresh copies: mutating the result never changes the (cached) config.
    """
    if cfg is None:
        cfg = load_config()
    section_sources = cfg.thresholds["section_sources"]
    sections = [
        {
            "id": sid,
            "source": section_sources[sid],
            "thresholds": copy.deepcopy(_thresholds(sid, cfg)),
        }
        for sid in SECTION_IDS
    ]
    return {
        "version": _version(cfg),
        "pending_clinician_review": PENDING_CLINICIAN_REVIEW,
        "sections": sections,
        "sources": copy.deepcopy(cfg.thresholds["sources"]),
    }
