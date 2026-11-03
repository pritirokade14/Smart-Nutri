import json
from dataclasses import replace

from app.scoring import CUSTOM_ALERT_KEYS, methodology
from app.scoring.nutriscore import GRADE_BANDS, GRADE_BANDS_BEVERAGE

SECTION_IDS = [
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
]


def _section(m, sid):
    return next(s for s in m["sections"] if s["id"] == sid)


# --- plan tests --------------------------------------------------------------------------


def test_sections_in_order_with_sources(cfg):
    m = methodology(cfg)
    assert [s["id"] for s in m["sections"]] == SECTION_IDS
    assert all(s["source"] in m["sources"] for s in m["sections"])


def test_thresholds_mirror_config(cfg):
    m = methodology(cfg)
    high = next(s for s in m["sections"] if s["id"] == "high_in")
    assert high["thresholds"] == cfg.thresholds["high_in"]


def test_flags_pending_review_and_stable_version(cfg):
    a, b = methodology(cfg), methodology(cfg)
    assert a["pending_clinician_review"] is True
    assert a["version"] == b["version"] and len(a["version"]) == 12


def test_json_serialisable(cfg):
    json.dumps(methodology(cfg))


# --- extra checks ------------------------------------------------------------------------


def test_section_sources_match_the_yaml_map(cfg):
    m = methodology(cfg)
    assert {s["id"]: s["source"] for s in m["sections"]} == cfg.thresholds["section_sources"]
    assert set(cfg.thresholds["section_sources"]) == set(SECTION_IDS)


def test_sources_have_title_url_and_are_unverified(cfg):
    # Ruling P5-R10: no link ships as verified until a human has checked it.
    m = methodology(cfg)
    assert m["sources"]
    for key, src in m["sources"].items():
        assert set(src) == {"title", "url", "url_verified"}, key
        assert src["title"] and src["url"].startswith("https://"), key
        assert src["url_verified"] is False, key


def test_every_section_has_exactly_id_source_thresholds(cfg):
    for s in methodology(cfg)["sections"]:
        assert set(s) == {"id", "source", "thresholds"}


def test_condition_sections_mirror_config(cfg):
    m = methodology(cfg)
    for group in ("blood_sugar", "hypertension", "weight_loss", "child", "infant"):
        assert _section(m, group)["thresholds"] == cfg.thresholds["conditions"][group]


def test_term_sections_mirror_config(cfg):
    m = methodology(cfg)
    assert _section(m, "allergens")["thresholds"] == cfg.allergens
    assert _section(m, "diet")["thresholds"] == cfg.diet
    assert _section(m, "claims")["thresholds"] == cfg.thresholds["claims"]


def test_custom_alerts_section_lists_every_alert_in_order(cfg):
    alerts = _section(methodology(cfg), "custom_alerts")["thresholds"]
    assert list(alerts) == list(CUSTOM_ALERT_KEYS)
    for key in ("palm_oil", "maida", "artificial_sweetener", "msg"):
        assert alerts[key] == cfg.ingredient_lists["custom_alerts"][key]
    lists = cfg.ingredient_lists
    assert alerts["added_sugar"] == {
        "terms": [*lists["added_sugars"], *lists["hidden_sugars"]],
        "exclude": [],
    }


def test_nutriscore_section_uses_the_engine_grade_bands(cfg):
    bands = _section(methodology(cfg), "nutriscore_2023")["thresholds"]
    assert bands == {
        "food": [{"grade": g, "max_points": p} for g, p in GRADE_BANDS],
        "beverage": [{"grade": g, "max_points": p} for g, p in GRADE_BANDS_BEVERAGE],
    }


def test_output_is_a_copy_of_the_config(cfg):
    m = methodology(cfg)
    _section(m, "high_in")["thresholds"]["food"]["sugars_g"] = 999
    _section(m, "allergens")["thresholds"]["milk"]["contains"].append("x")
    assert cfg.thresholds["high_in"]["food"]["sugars_g"] != 999
    assert "x" not in cfg.allergens["milk"]["contains"]
    assert methodology(cfg)["version"] == m["version"]


def test_version_changes_with_the_config(cfg):
    high = {**cfg.thresholds["high_in"], "food": {**cfg.thresholds["high_in"]["food"]}}
    high["food"]["sugars_g"] = 1.0
    other = replace(cfg, thresholds={**cfg.thresholds, "high_in": high})
    assert methodology(other)["version"] != methodology(cfg)["version"]


def test_default_config_is_used_when_none(cfg):
    assert methodology()["version"] == methodology(cfg)["version"]
