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


@pytest.mark.parametrize(
    ("product", "member", "expected"), CASES, ids=[f"{p}.{m}" for p, m, _ in CASES]
)
def test_engine_matches_expected(product, member, expected):
    verdict = analyze(load_product(product), [load_member(member)]).verdicts[0]
    assert verdict.status.value == expected["status"]
    actual = [{"code": r.code, "severity": r.severity.value} for r in verdict.reasons]
    assert actual == expected["reasons"]
