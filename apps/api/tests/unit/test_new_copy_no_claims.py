"""The new Diary copy has no medical claims, doses or judgement words (Plan 11 Task 8; AGENTS
rule 7; spec 7: neutral tone, no streaks, ratings or "good day" labels). Scans the new en, hi and
mr keys."""

import json
import re
from pathlib import Path

import pytest

from tests.fixtures.test_mode_layouts import BANNED, BANNED_NATIVE

MESSAGES = Path(__file__).resolve().parents[4] / "packages" / "i18n" / "messages"
JUDGING = re.compile(
    r"\b(streaks?|good day|bad day|well done|great job|on track|off track|cheat|guilt\w*|"
    r"clean eating|junk|healthy day)\b",
    re.IGNORECASE,
)
JUDGING_NATIVE = ("स्ट्रीक", "अच्छा दिन", "बुरा दिन", "चीट", "शाबाश", "छान दिवस", "वाईट दिवस")
ERROR_CODES = {
    "quick_add_energy_required",
    "copy_source_empty",
    "copy_too_many",
    "date_too_old",
    "meal_slot_not_found",
    "meal_slot_archived",
    "timezone_invalid",
}
NEW_FOODS = {"foods.blank_is_unknown", "foods.recent", "foods.quick_add"}


def _flat(node, prefix=""):
    if isinstance(node, dict):
        for k, v in node.items():
            yield from _flat(v, f"{prefix}{k}.")
    else:
        yield prefix[:-1], node


def _new(lang: str) -> dict[str, str]:
    data = json.loads((MESSAGES / f"{lang}.json").read_text(encoding="utf-8"))
    return {
        key: value
        for key, value in _flat(data)
        if key.startswith("diary.")
        or key in NEW_FOODS
        or key == "nav.diary"
        or (key.startswith("error.") and key.removeprefix("error.") in ERROR_CODES)
    }


@pytest.mark.parametrize("lang", ["en", "hi", "mr"])
def test_new_keys_exist(lang):
    keys = set(_new(lang))
    assert {"diary.title", "diary.copied", "diary.over", "diary.left", "nav.diary"} <= keys
    assert NEW_FOODS <= keys
    assert {f"error.{c}" for c in ERROR_CODES} <= keys


def test_new_keys_match_across_languages():
    assert set(_new("en")) == set(_new("hi")) == set(_new("mr"))


@pytest.mark.parametrize("lang", ["en", "hi", "mr"])
def test_no_claims_doses_or_judgement(lang):
    for key, value in _new(lang).items():
        assert not BANNED.search(value), (lang, key, value)
        assert not JUDGING.search(value), (lang, key, value)
        for word in (*BANNED_NATIVE, *JUDGING_NATIVE):
            assert word not in value, (lang, key, word)
        assert not re.search(r"\d+\s*(g|mg)\s*(per|a|/)\s*day", value, re.IGNORECASE), (lang, key)
