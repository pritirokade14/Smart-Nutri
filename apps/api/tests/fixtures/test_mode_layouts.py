"""The mode table (packages/test-fixtures/modes/layouts.json) is the single source of truth
for tabs, Home cards and More. Both clients mirror it; this pins its invariants (Plan 9 T8)."""

import json
import re
from pathlib import Path

from app.features.me.schemas import DEFAULT_TYPE, USER_TYPE_PRIORITY

ROOT = Path(__file__).resolve().parents[4] / "packages"
LAYOUTS = json.loads((ROOT / "test-fixtures/modes/layouts.json").read_text(encoding="utf-8"))
MODES = LAYOUTS["modes"]


def more(mode: str) -> list[str]:
    tabs = MODES[mode]["tabs"]
    return [d for d in LAYOUTS["destinations"] if d not in tabs]


def test_priority_matches_api():
    assert tuple(LAYOUTS["priority"]) == USER_TYPE_PRIORITY
    assert LAYOUTS["default_type"] == DEFAULT_TYPE
    assert set(MODES) == set(USER_TYPE_PRIORITY)


def test_every_mode_has_five_tabs_scan_second_profile_last():
    for name, mode in MODES.items():
        tabs = mode["tabs"]
        assert len(tabs) == 5 and len(set(tabs)) == 5, name
        assert tabs[0] == "home" and tabs[1] == "scan" and tabs[-1] == "profile", name
        assert set(tabs) <= set(LAYOUTS["destinations"]), name


def test_every_destination_reachable_in_every_mode():
    for name, mode in MODES.items():
        assert set(mode["tabs"]) | set(more(name)) == set(LAYOUTS["destinations"]), name
        assert not set(mode["tabs"]) & set(more(name)), name


def test_scan_result_and_allergy_entry_points_in_every_mode():
    # scan is a tab; a result opens from scan (and from history / search / the Home recent
    # list); allergies are entered on a family member (or the profile's own member).
    for name, mode in MODES.items():
        assert mode["tabs"][1] == "scan", name
        assert "recent_scans" in mode["home_cards"], name  # opens a result
        assert "family" in mode["tabs"] or "family" in more(name), name  # allergy entry
        assert "profile" in mode["tabs"], name


def test_gym_more_is_history_family_search_how_we_score():
    assert more("gym") == ["history", "family", "search", "how_we_score"]


def test_recent_scans_last():
    for name, mode in MODES.items():
        assert mode["home_cards"][-1] == "recent_scans", name
        assert mode["home_cards"].count("recent_scans") == 1, name


def test_allergy_card_rule():
    assert LAYOUTS["always_first_card_when_any_member_has_allergens"] == "allergy_check"
    assert MODES["allergy_diet"]["home_cards"][0] == "allergy_check"
    for name, mode in MODES.items():
        if name != "allergy_diet":
            assert "allergy_check" not in mode["home_cards"], name  # injected by the client rule


def test_home_cards_are_documented():
    readme = (ROOT / "test-fixtures/README.md").read_text(encoding="utf-8")
    for mode in MODES.values():
        for card in mode["home_cards"]:
            assert f"`{card}`" in readme, card


# --- copy -----------------------------------------------------------------------------------
BANNED = re.compile(
    r"\b(manage[sd]?|managing|treat(s|ed|ing|ment)?|cure[sd]?|curing|reverse[sd]?|"
    r"you need|diagnos\w*|prescri\w*|dose|dosage)\b",
    re.IGNORECASE,
)
BANNED_NATIVE = (
    "इलाज",
    "उपचार",
    "रोग मुक्त",
    "उलट",
    "आपको चाहिए",
    "खुराक",
    "डोस",
    "तुम्हाला हवे",
    "बरा करत",
)
NEW_ROOTS = ("user_types", "modes", "protein")


def _flat(node, prefix=""):
    if isinstance(node, dict):
        for k, v in node.items():
            yield from _flat(v, f"{prefix}{k}.")
    else:
        yield prefix[:-1], node


def _new_strings(lang: str):
    data = json.loads((ROOT / f"i18n/messages/{lang}.json").read_text(encoding="utf-8"))
    for key, value in _flat(data):
        root = key.split(".")[0]
        if root in NEW_ROOTS or key.startswith(("home.cards.", "goal.", "nav.protein", "nav.more")):
            yield key, value


def test_copy_has_no_medical_claims_or_doses():
    for lang in ("en", "hi", "mr"):
        seen = list(_new_strings(lang))
        assert seen, lang
        for key, value in seen:
            assert not BANNED.search(value), (lang, key, value)
            for word in BANNED_NATIVE:
                assert word not in value, (lang, key, word)
            assert not re.search(r"\d+\s*(g|mg)\s*(per|a|/)\s*day", value, re.IGNORECASE), (
                lang,
                key,
            )


def test_new_keys_exist_in_all_languages():
    def keys(lang):
        return {k for k, _ in _new_strings(lang)}

    assert keys("en") == keys("hi") == keys("mr")
    assert {"user_types.title", "modes.more", "protein.title", "goal.build_muscle"} <= keys("en")
