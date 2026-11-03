"""R21(c): packages/test-fixtures/drafts/ (shared confirm-screen fixtures) never drift.

The drafts and expected saves are regenerated in memory from the real normaliser and save
rules and compared with the committed files. Regenerate with
`uv run python scripts/export_draft_fixtures.py --write` and review the diff.
"""

import json

import pytest

from app.features.scans.normalize import ProductDraft
from scripts.export_draft_fixtures import CASES, DRAFTS, build_body, changes

REQUIRED_CASES = {
    "clean",
    "basis_mismatch_both_columns",
    "basis_mismatch_one_column",
    "derived_from_serving",
    "derived_basis_mismatch",
    "unit_unconfirmed_sodium_per_100g",
    "unit_unconfirmed_sodium_per_serving",
    "upper_bound_protein_per_100g",
    "upper_bound_protein_per_serving",
    "category_check",
    "low_confidence",
    "implausible_value",
    "devanagari",
}


def test_draft_fixtures_are_current():
    """CI fails if stale: regenerate with scripts/export_draft_fixtures.py --write."""
    _new, _old, tags = changes()
    assert tags == {}, f"stale drafts/ files (run export_draft_fixtures.py --write): {tags}"


def test_every_r21_case_is_covered():
    assert REQUIRED_CASES <= set(CASES)


def _expected() -> dict:
    return json.loads((DRAFTS / "expected.json").read_text(encoding="utf-8"))


def _ignored(name: str) -> dict:
    [save] = [s for s in _expected()["cases"][name]["saves"] if s["actions"] == {}]
    return save


@pytest.mark.parametrize("name", sorted(CASES))
def test_committed_draft_loads_and_keeps_its_hints(name):
    data = json.loads((DRAFTS / f"{name}.json").read_text(encoding="utf-8"))
    draft = ProductDraft.model_validate(data)
    assert draft.model_dump(mode="json") == data  # confirm is recomputed to the same value


@pytest.mark.parametrize("name", sorted(CASES))
def test_every_case_has_a_successful_save(name):
    saves = _expected()["cases"][name]["saves"]
    assert any(s["result"]["status"] == 201 for s in saves)


@pytest.mark.parametrize(
    ("name", "field"),
    [
        ("basis_mismatch_both_columns", "body.basis"),
        ("basis_mismatch_one_column", "body.basis"),
        ("derived_basis_mismatch", "body.basis"),
        ("category_check", "body.category"),
        ("category_unknown", "body.category"),
        ("unit_unconfirmed_sodium_per_100g", "body.sodium_unit"),
        ("unit_unconfirmed_sodium_per_serving", "body.sodium_unit"),
    ],
)
def test_ignoring_a_required_choice_is_a_422(name, field):
    result = _ignored(name)["result"]
    assert result["status"] == 422 and result["error"]["fields"] == [field]


@pytest.mark.parametrize(
    ("name", "nulls"),
    [
        ("derived_from_serving", "all"),
        ("upper_bound_protein_per_100g", ["protein_g"]),
        ("upper_bound_protein_per_serving", ["protein_g"]),
    ],
)
def test_ignoring_a_tick_stores_null(name, nulls):
    stored = _ignored(name)["result"]["stored"]
    per_100g = stored["per_100g"]
    fields = list(per_100g) if nulls == "all" else nulls
    assert all(per_100g[f] is None for f in fields)
    assert stored["serving_size_g"] is None


def test_actions_outside_the_hints_are_rejected():
    draft = ProductDraft.model_validate(
        json.loads((DRAFTS / "derived_from_serving.json").read_text(encoding="utf-8"))
    )
    with pytest.raises(ValueError, match="not offered"):
        build_body(draft, {"pick_basis": "per_100g"})
    with pytest.raises(ValueError, match="unknown actions"):
        build_body(draft, {"press": "save"})
