import pytest

from app.scoring import analyze
from tests.fixtures.loader import FIXTURES, expected_cases, load_member, load_product

CASES = expected_cases()


def test_expected_files_exist():
    assert len(CASES) >= 10


def test_every_product_and_member_has_expectations():
    products = {p.stem for p in (FIXTURES / "products").glob("*.json")}
    members = {m.stem for m in (FIXTURES / "members").glob("*.json")}
    assert {(p, m) for p, m, _ in CASES} == {(p, m) for p in products for m in members}


def test_meal_and_share_fixtures_are_current():
    """Plan 6: meals/expected/ and share/ are generated; regenerate with
    `uv run python scripts/export_meal_fixtures.py --write` and review the diff."""
    from scripts.export_meal_fixtures import changes

    stale = sorted(p.name for p in changes())
    assert stale == [], f"stale meal/share fixtures (run export_meal_fixtures.py --write): {stale}"


def test_share_texts_never_leak_health_data():
    import json

    data = json.loads((FIXTURES / "share" / "share_result.sf_biscuit.json").read_text("utf-8"))
    for locale, text in data["expected"].items():
        assert data["forbidden_substrings"][locale]
        assert not [w for w in data["forbidden_substrings"][locale] if w in text.casefold()]
    # The verdict statuses in the share input are the engine's, as in expected/.
    for v in data["input"]["verdicts"]:
        expected = json.loads(
            (FIXTURES / "expected" / f"sf_biscuit.{v['fixture_member']}.json").read_text("utf-8")
        )
        assert v["status"] == expected["status"]


@pytest.mark.parametrize(
    ("product", "member", "expected"), CASES, ids=[f"{p}.{m}" for p, m, _ in CASES]
)
def test_engine_matches_expected(product, member, expected):
    verdict = analyze(load_product(product), [load_member(member)]).verdicts[0]
    assert verdict.status.value == expected["status"]
    actual = [{"code": r.code, "severity": r.severity.value} for r in verdict.reasons]
    assert actual == expected["reasons"]


# --- family coverage (Plan 5 Task 8) -----------------------------------------------------------


def _codes(expected: dict) -> set[str]:
    return {r["code"] for r in expected["reasons"]}


def _members():
    return [load_member(m.stem) for m in sorted((FIXTURES / "members").glob("*.json"))]


def test_custom_alert_reasons_are_covered():
    """Both clients render custom_alert and custom_alert_unknown from these fixtures."""
    assert any("custom_alert" in _codes(e) for _, _, e in CASES)
    assert any("custom_alert_unknown" in _codes(e) for _, _, e in CASES)


def test_alert_members_cover_adult_child_infant_and_unknown_age():
    """Controller ruling: an adult, a child, an infant and an age=None member with alerts."""
    ages = [m.age for m in _members() if m.custom_alerts]
    assert None in ages
    assert any(a is not None and a < 2 for a in ages)  # infant
    assert any(a is not None and 2 <= a < 13 for a in ages)  # child
    assert any(a is not None and a >= 18 for a in ages)  # adult


def test_free_text_allergen_fixture_is_avoid():
    """kiwi_child: a typed-in (non-canonical) allergen reaches the engine as `avoid`."""
    assert load_member("kiwi_child").allergens == ("kiwi",)
    expected = next(e for p, m, e in CASES if (p, m) == ("kiwi_yogurt", "kiwi_child"))
    assert expected["status"] == "avoid"
    assert expected["reasons"][0] == {"code": "allergen_contains", "severity": "avoid"}
