"""The shared fixtures through the real endpoint: the source of truth for both clients."""

import json
from pathlib import Path

import pytest

from app.core.security import AccountContext
from app.features.me.service import ensure_account
from app.features.members.service import to_scoring_member
from app.features.products.service import record_to_product
from scripts.export_fixture_responses import (
    REFERENCE_DATE,
    fixture_member_record,
    fixture_product_record,
    write,
)
from tests.api.analyze.conftest import A, today
from tests.fixtures.loader import FIXTURES, expected_cases, load_member, load_product

CASES = expected_cases()
RESPONSES = FIXTURES / "responses"


def _pairs(expected: dict) -> list[tuple[str, str]]:
    return [(r["code"], r["severity"]) for r in expected["reasons"]]


def _files(base: Path) -> dict[str, str]:
    return {
        p.relative_to(base).as_posix(): p.read_text(encoding="utf-8")
        for p in sorted(base.rglob("*"))
        if p.is_file()
    }


@pytest.mark.parametrize(
    ("product", "member", "expected"), CASES, ids=[f"{p}.{m}" for p, m, _ in CASES]
)
async def test_fixture_verdicts(product, member, expected, auth_client, db_session):
    await ensure_account(db_session, AccountContext(A, None))
    p = fixture_product_record(product)
    m = fixture_member_record(member, account_id=A, reference=today())
    db_session.add_all([p, m])
    await db_session.flush()
    r = await auth_client.post(
        "/v1/analyze", json={"product_id": str(p.id), "member_ids": [str(m.id)]}
    )
    assert r.status_code == 200, r.text
    (v,) = r.json()["verdicts"]
    assert v["status"] == expected["status"]
    assert [(x["code"], x["severity"]) for x in v["reasons"]] == _pairs(expected)


def test_fixture_records_round_trip():
    """The DB-shaped fixture records give the engine exactly the fixture product and member."""
    for path in sorted((FIXTURES / "products").glob("*.json")):
        assert record_to_product(fixture_product_record(path.stem)) == load_product(path.stem)
    for path in sorted((FIXTURES / "members").glob("*.json")):
        record = fixture_member_record(path.stem, account_id=A)
        scoring_member = to_scoring_member(record, today=REFERENCE_DATE)
        fixture = load_member(path.stem)
        assert scoring_member.age == fixture.age
        assert scoring_member.diet == fixture.diet
        assert scoring_member.allergens == fixture.allergens
        assert scoring_member.conditions == fixture.conditions
        assert scoring_member.goal == fixture.goal


def test_fixture_responses_are_current(tmp_path):
    """CI fails if stale: regenerate with scripts/export_fixture_responses.py, never by hand."""
    write(tmp_path)
    assert _files(tmp_path) == _files(RESPONSES)


def test_golden_analyze_verdicts_match_expected():
    index = json.loads((RESPONSES / "index.json").read_text(encoding="utf-8"))
    for product, member, expected in CASES:
        body = json.loads((RESPONSES / "analyze" / f"{product}.json").read_text(encoding="utf-8"))
        (v,) = [v for v in body["verdicts"] if v["member_id"] == index["members"][member]]
        assert v["status"] == expected["status"], (product, member)
        assert [(x["code"], x["severity"]) for x in v["reasons"]] == _pairs(expected)


def test_golden_public_responses_have_no_member_data():
    for path in sorted((RESPONSES / "public").glob("*.json")):
        text = path.read_text(encoding="utf-8")
        assert "verdicts" not in text and "member" not in text
        assert json.loads(text)["score_label"] == "calculated_by_smartnutri"
