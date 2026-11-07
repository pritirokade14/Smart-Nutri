import json
from dataclasses import replace

from app.scoring import CUSTOM_ALERT_KEYS, methodology
from app.scoring.nutriscore import GRADE_BANDS, GRADE_BANDS_BEVERAGE, GRADE_BANDS_FAT

SECTION_IDS = [
    "nutriscore_2023",
    "high_in",
    "allergens",
    "diet",
    "claims",
    "blood_sugar",
    "hypertension",
    "weight_loss",
    "build_muscle",
    "child",
    "infant",
    "supplements",
    "custom_alerts",
    "daily_limits",
    "energy_targets",
]


def _section(m, sid):
    return next(s for s in m["sections"] if s["id"] == sid)


# --- plan tests --------------------------------------------------------------------------


def _keys(section):
    return [*(section["threshold_sources"] or []), *(section["rationale_sources"] or [])]


def test_sections_in_order_with_sources(cfg):
    m = methodology(cfg)
    assert [s["id"] for s in m["sections"]] == SECTION_IDS
    assert all(k in m["sources"] for s in m["sections"] for k in _keys(s))


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
    yaml_map = cfg.thresholds["section_sources"]
    assert set(yaml_map) == set(SECTION_IDS)
    for s in m["sections"]:
        entry = yaml_map[s["id"]]
        if entry is None:
            assert s["threshold_sources"] is None and s["rationale_sources"] is None
        else:
            assert s["threshold_sources"] == entry["thresholds"]
            assert s["rationale_sources"] == entry.get("rationale", [])


def test_section_source_lists_are_lists_of_known_keys(cfg):
    sources = cfg.thresholds["sources"]
    for sid, entry in cfg.thresholds["section_sources"].items():
        if entry is None:
            continue
        assert set(entry) <= {"thresholds", "rationale"}, sid
        assert isinstance(entry["thresholds"], list) and entry["thresholds"], sid
        assert isinstance(entry.get("rationale", []), list), sid
        for key in [*entry["thresholds"], *entry.get("rationale", [])]:
            assert key in sources, (sid, key)


def test_sources_are_honest_ruling_p7(cfg):
    # blood_sugar numbers are UK FSA high-in / FSSAI low-sugar bands and the UK SDIL drink
    # threshold (thresholds.yaml comments), not ICMR-NIN.
    m = methodology(cfg)
    blood = _section(m, "blood_sugar")
    # The 30 g carbs-per-serving caution is our own number (controller, c2897fd re-review).
    assert blood["threshold_sources"] == [
        "uk_fsa_front_of_pack",
        "fssai_claims_2018",
        "uk_sdil",
        "smartnutri_working_values",
    ]
    assert "icmr_nin_2024" not in blood["threshold_sources"]
    # thresholds.yaml cites ADA Standards of Care as a rationale for cardio_high_in.
    assert blood["rationale_sources"] == ["icmr_nin_2024", "ada_standards_of_care"]
    assert "American Diabetes Association" in m["sources"]["ada_standards_of_care"]["title"]
    # The infant numbers are SmartNutri working values, not WHO numbers. WHO is only the
    # rationale (no added sugar or salt under 2).
    infant = _section(m, "infant")
    assert infant["threshold_sources"] == ["smartnutri_working_values"]
    assert infant["rationale_sources"] == ["who_infant"]
    working = m["sources"]["smartnutri_working_values"]
    assert "pending clinician review" in working["title"].lower()
    assert "who" not in working["title"].lower()
    # A member's own alerts are a preference, not a health rule: no source.
    alerts = _section(m, "custom_alerts")
    assert alerts["threshold_sources"] is None and alerts["rationale_sources"] is None
    # No section cites ICMR-NIN as the source of its numbers, except the daily guides, whose
    # 30 % fat maximum is ICMR-NIN 2024 (read via news coverage, marked [verify]).
    assert all(
        "icmr_nin_2024" not in (s["threshold_sources"] or [])
        for s in m["sections"]
        if s["id"] != "energy_targets"
    )


def test_sources_have_title_url_and_are_unverified(cfg):
    # Ruling P5-R10: no link ships as verified until a human has checked it.
    m = methodology(cfg)
    assert m["sources"]
    for key, src in m["sources"].items():
        assert set(src) == {"title", "url", "url_verified"}, key
        assert src["title"], key
        # Internal working values, and Devine 1974 (original not read, no stable link), have
        # no external link.
        if key in ("smartnutri_working_values", "devine_1974"):
            assert src["url"] is None
        else:
            assert src["url"].startswith("https://"), key
        assert src["url_verified"] is False, key


def test_every_section_has_exactly_id_sources_thresholds(cfg):
    for s in methodology(cfg)["sections"]:
        assert set(s) == {"id", "threshold_sources", "rationale_sources", "thresholds"}


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
        "fat": [{"grade": g, "max_points": p} for g, p in GRADE_BANDS_FAT],
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


def test_daily_limits_section_mirrors_config(cfg):
    sec = _section(methodology(cfg), "daily_limits")
    t, dl = sec["thresholds"], cfg.thresholds["daily_limits"]
    assert t["adult"] == dl["adult"]
    assert t["child_salt_g_by_min_age"] == dl["child_salt_g_by_min_age"]
    assert (
        t["child_sugar_g_by_min_age"]
        == (cfg.thresholds["conditions"]["child"]["free_sugar_daily_limit_g"])
    )
    assert sec["threshold_sources"][0] == "who_free_sugars"
    assert sec["rationale_sources"] == ["who_infant"]


def test_build_muscle_section_plan9(cfg):
    # Plan 9 Task 3: the 5 g per 100 kcal density is ours; ISSN 2017 is the reason for the
    # 1.6 g/kg target. The section shows the live values from the yaml.
    m = methodology(cfg)
    muscle = _section(m, "build_muscle")
    assert muscle["threshold_sources"] == ["smartnutri_working_values"]
    assert muscle["rationale_sources"] == ["issn_protein_2017"]
    assert muscle["thresholds"] == cfg.thresholds["conditions"]["build_muscle"]
    daily = _section(m, "daily_limits")
    assert "issn_protein_2017" in daily["threshold_sources"]
    assert "protein_g_per_kg_by_goal" not in daily["thresholds"]  # moved to targets.yaml
    assert m["sources"]["issn_protein_2017"]["url_verified"] is False


def test_energy_targets_section(cfg):
    sec = _section(methodology(cfg), "energy_targets")
    assert "mifflin_1990" in sec["threshold_sources"]
    assert sec["thresholds"]["protein"]["lean_mass_g_per_kg_by_goal"]["build_muscle"] == 2.0
    assert "version" not in sec["thresholds"]
    expected = {k: v for k, v in cfg.targets.items() if k != "version"}
    assert sec["thresholds"] == expected
    from app.scoring import targets

    assert targets.sources(cfg) == tuple(
        dict.fromkeys([*sec["threshold_sources"], *sec["rationale_sources"]])
    )
    assert sec["threshold_sources"] == [
        "mifflin_1990",
        "cdc_weight_loss",
        "iom_2005_dri",
        "issn_protein_2017",
        "morton_2018",
        "icmr_nin_2024",
        "who_protein_2007",
        "devine_1974",
        "smartnutri_working_values",
    ]
    assert sec["rationale_sources"] == ["issn_protein_2017", "iom_2005_dri"]
    for k in ("mifflin_1990", "cdc_weight_loss", "iom_2005_dri", "morton_2018", "devine_1974"):
        assert methodology(cfg)["sources"][k]["url_verified"] is False
