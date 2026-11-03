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


def test_committed_sheet_is_current(sheet):
    """Regenerate with: cd apps/api && uv run python ../../scripts/clinician_review_sheet.py
    > ../../docs/launch/clinician-review.md"""
    text = SHEET.read_text(encoding="utf-8")
    assert "`daily_limits.adult.sugar_g` | 25 | g per day" in text
    assert text == sheet.render()
