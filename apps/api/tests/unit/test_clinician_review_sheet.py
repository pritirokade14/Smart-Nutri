"""The clinician review sheet (scripts/clinician_review_sheet.py) gives every threshold its real
unit, includes the daily limits, and the committed docs/launch copy is current (cleanup c2)."""

import importlib.util
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[4]
SCRIPT = ROOT / "scripts" / "clinician_review_sheet.py"
SHEET = ROOT / "docs" / "launch" / "clinician-review.md"


@pytest.fixture(scope="module")
def sheet():
    spec = importlib.util.spec_from_file_location("clinician_review_sheet", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.mark.parametrize(
    ("path", "unit"),
    [
        (("daily_limits", "adult", "sugar_g"), "g per day"),
        (("daily_limits", "adult", "salt_g"), "g per day"),
        (("daily_limits", "adult", "protein_g_per_kg"), "g per kg body weight per day"),
        (("daily_limits", "protein_min_age"), "years (minimum age)"),
        (
            ("daily_limits", "protein_g_per_kg_by_goal", "build_muscle"),
            "g per kg body weight per day",
        ),
        (("conditions", "build_muscle", "good_protein_g_per_100kcal"), "g per 100 kcal"),
        (
            ("daily_limits", "child_salt_g_by_min_age", "4"),
            "g salt per day (key = minimum age in years)",
        ),
        (("daily_limits", "infant", "sugar_g"), "g per day"),
        (("daily_limits", "infant", "salt_g"), "g per day"),
        (("daily_limits", "near_pct"), "% of daily limit"),
        # Unchanged per-100 g units keep working.
        (("high_in", "food", "sugars_g"), "g per 100 g"),
        (("high_in", "drink", "salt_g"), "g per 100 ml"),
        (("conditions", "child", "caution_pct_of_limit"), "% of daily limit"),
        (("claims", "high_protein_min_energy_pct"), "% of energy"),
        (("claims", "protein_amount_shortfall_pct"), "% below the claimed protein amount"),
        (("conditions", "infant", "avoid_salt_g"), "g per 100 g"),
    ],
)
def test_units(sheet, path, unit):
    assert sheet.unit_of(path) == unit


def test_every_row_has_a_unit(sheet):
    from app.scoring import load_config

    rows = sheet.numeric_leaves(load_config().thresholds)
    missing = [".".join(p) for p, _ in rows if not sheet.unit_of(p)]
    assert missing == []


def test_daily_limit_questions(sheet):
    assert sheet.question_of(("daily_limits", "child_salt_g_by_min_age", "2")) == (
        sheet.QUESTION_CHILD
    )
    assert sheet.question_of(("daily_limits", "infant", "salt_g")) == sheet.QUESTION_INFANT
    assert sheet.question_of(("daily_limits", "adult", "sugar_g")) == sheet.QUESTION_ADULT


def test_build_muscle_protein_target_questions(sheet):
    q = sheet.question_of(("daily_limits", "protein_g_per_kg_by_goal", "build_muscle"))
    assert "Is 1.6 g/kg right" in q
    assert "diabetes or hypertension" in q
    assert "kidney" in q
    assert "If you have kidney disease, ask your doctor before eating more protein." in q
    assert "1.2 g/kg" in q
    row = next(
        line
        for line in sheet.render().splitlines()
        if "`daily_limits.protein_g_per_kg_by_goal.build_muscle`" in line
    )
    assert "| 1.6 | g per kg body weight per day |" in row
    assert "ISSN position stand" in row and "kidney" in row


# --- S4: each row cites the sources of ITS number, not every source of its section ---------


@pytest.fixture(scope="module")
def meta():
    from app.scoring import load_config, methodology

    return methodology(load_config())


def _sources(sheet, meta, path):
    sections = {s["id"]: s for s in meta["sections"]}
    return sheet.source_keys(path, sections)


@pytest.mark.parametrize("leaf", ["sugar_g", "salt_g"])
def test_infant_daily_limits_cite_who_under_2_only(sheet, meta, leaf):
    thresholds, rationale = _sources(sheet, meta, ("daily_limits", "infant", leaf))
    assert thresholds == ["who_infant"] and rationale == []


@pytest.mark.parametrize("leaf", ["avoid_sugars_g", "avoid_salt_g"])
def test_infant_per_100g_values_are_ours_with_who_as_the_reason(sheet, meta, leaf):
    # Ruling R27: 5 g and 0.3 g are SmartNutri values, NOT WHO numbers.
    thresholds, rationale = _sources(sheet, meta, ("conditions", "infant", leaf))
    assert thresholds == ["smartnutri_working_values"] and rationale == ["who_infant"]


@pytest.mark.parametrize(
    ("path", "expected"),
    [
        (("daily_limits", "adult", "sugar_g"), ["who_free_sugars"]),
        (("daily_limits", "adult", "salt_g"), ["who_sodium"]),
        (("daily_limits", "adult", "protein_g_per_kg"), ["who_protein_2007"]),
        (("daily_limits", "protein_g_per_kg_by_goal", "build_muscle"), ["issn_protein_2017"]),
        (
            ("conditions", "build_muscle", "good_protein_g_per_100kcal"),
            ["smartnutri_working_values"],
        ),
        (("daily_limits", "child_salt_g_by_min_age", "4"), ["nhs_child_salt"]),
        (("daily_limits", "near_pct"), ["smartnutri_working_values"]),
        (("conditions", "blood_sugar", "avoid_sugars_g", "food"), ["uk_fsa_front_of_pack"]),
        (("conditions", "blood_sugar", "avoid_sugars_g", "drink"), ["uk_sdil"]),
        (("conditions", "blood_sugar", "caution_sugars_g", "food"), ["fssai_claims_2018"]),
        (
            ("conditions", "blood_sugar", "caution_carbs_per_serving_g"),
            ["smartnutri_working_values"],
        ),
        (("conditions", "child", "free_sugar_daily_limit_g", "7"), ["nhs_child_sugar"]),
        (("conditions", "child", "avoid_pct_of_limit"), ["smartnutri_working_values"]),
        (("claims", "protein_amount_shortfall_pct"), ["smartnutri_working_values"]),
        (("claims", "low_fat_max_g", "food"), ["fssai_claims_2018"]),
        # Single-source sections keep their section source.
        (("high_in", "food", "salt_g"), ["uk_fsa_front_of_pack"]),
    ],
)
def test_per_key_threshold_sources(sheet, meta, path, expected):
    assert _sources(sheet, meta, path)[0] == expected


def test_every_row_of_a_multi_source_section_has_its_own_sources(sheet, meta):
    """A section citing several sources must say which one backs each number."""
    from app.scoring import load_config

    sections = {s["id"]: s for s in meta["sections"]}
    rows = sheet.numeric_leaves(load_config().thresholds)
    unresolved = [
        ".".join(p)
        for p, _ in rows
        if len((sections.get(sheet.section_of(p)) or {}).get("threshold_sources") or []) > 1
        and sheet.key_entry(p) is None
    ]
    assert unresolved == []


def test_key_sources_name_real_sources_and_real_thresholds(sheet, meta):
    from app.scoring import load_config

    paths = [p for p, _ in sheet.numeric_leaves(load_config().thresholds)]
    for prefix, (thresholds, rationale) in sheet.KEY_SOURCES.items():
        assert set(thresholds) | set(rationale) <= set(meta["sources"]), prefix
        assert any(p[: len(prefix)] == prefix for p in paths), f"stale entry {prefix}"


def test_sheet_shows_the_reason_separately(sheet):
    text = sheet.render()
    row = next(line for line in text.splitlines() if "`conditions.infant.avoid_salt_g`" in line)
    assert "SmartNutri working values" in row
    assert "why: WHO guidance: no added sugar or salt under 2" in row
    infant_daily = next(
        line for line in text.splitlines() if "`daily_limits.infant.salt_g`" in line
    )
    assert "WHO guidance: no added sugar or salt under 2" in infant_daily
    assert "sodium intake" not in infant_daily and "protein" not in infant_daily


def test_committed_sheet_is_current(sheet):
    """Regenerate with: cd apps/api && uv run python ../../scripts/clinician_review_sheet.py
    > ../../docs/launch/clinician-review.md"""
    text = SHEET.read_text(encoding="utf-8")
    assert "`daily_limits.adult.sugar_g` | 25 | g per day" in text
    assert text == sheet.render()
