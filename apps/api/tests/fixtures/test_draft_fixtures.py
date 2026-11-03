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


@pytest.mark.parametrize("name", sorted(CASES))
def test_every_case_keeps_a_save_that_changes_nothing(name):
    """R23(a): the "unconfirmed -> stored None" control."""
    assert any(s["actions"] == {} for s in _expected()["cases"][name]["saves"])


def _save(name: str, actions: dict) -> dict:
    [save] = [s for s in _expected()["cases"][name]["saves"] if s["actions"] == actions]
    return save


def test_an_edit_of_the_serving_is_a_confirmation_without_a_tick():
    """R23(a): per_serving_only_no_serving save 1 edits the serving and ticks nothing."""
    save = _save(
        "per_serving_only_no_serving",
        {"pick_basis": "per_serving", "edit": {"serving_size_g": 30.0}},
    )
    assert save["body"]["confirmed_fields"] == ["serving_size_g"]
    assert save["result"]["stored"]["serving_size_g"] == 30.0
    assert "client_blocks" not in save


def test_an_edit_of_a_hinted_field_is_a_confirmation_in_contract_order():
    save = _save("upper_bound_protein_per_100g", {"edit": {"protein_g": 0.4}})
    assert save["body"]["confirmed_fields"] == ["protein_g"]
    assert save["result"]["stored"]["per_100g"]["protein_g"] == 0.4


def test_an_edit_of_a_field_the_column_does_not_ask_about_confirms_nothing():
    save = _save("implausible_value", {"edit": {"sugars_g": 10.0}})
    assert save["body"]["confirmed_fields"] == []


def test_edit_and_tick_merge_in_contract_order():
    draft = ProductDraft.model_validate(
        json.loads((DRAFTS / "upper_bound_protein_per_serving.json").read_text(encoding="utf-8"))
    )
    body = build_body(
        draft, {"pick_basis": "per_serving", "tick": ["serving_size_g"], "edit": {"protein_g": 0.4}}
    )
    assert body["confirmed_fields"] == ["protein_g", "serving_size_g"]


def test_client_blocks_marks_exactly_the_saves_with_serving_required_and_no_serving():
    """R23(b): save is disabled client-side while the serving is unconfirmed."""
    blocked = 0
    for name, case in _expected()["cases"].items():
        draft = ProductDraft.model_validate(
            json.loads((DRAFTS / case["draft"]).read_text(encoding="utf-8"))
        )
        for save in case["saves"]:
            body = save["body"]
            column = getattr(draft.confirm.columns, body["basis"]) if "basis" in body else None
            expect = bool(
                column is not None
                and column.serving_required
                and "serving_size_g" not in body["confirmed_fields"]
            )
            assert save.get("client_blocks", False) is expect, (name, save["actions"])
            blocked += expect
    assert blocked > 0
    assert _save("derived_from_serving", {})["client_blocks"] is True
    assert _save("derived_from_serving", {"tick": ["serving_size_g"]}).get("client_blocks") is None


def test_actions_outside_the_hints_are_rejected():
    draft = ProductDraft.model_validate(
        json.loads((DRAFTS / "derived_from_serving.json").read_text(encoding="utf-8"))
    )
    with pytest.raises(ValueError, match="not offered"):
        build_body(draft, {"pick_basis": "per_100g"})
    with pytest.raises(ValueError, match="unknown actions"):
        build_body(draft, {"press": "save"})
