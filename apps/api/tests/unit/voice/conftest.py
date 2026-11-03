"""Engine results for the golden products (Plan 1 fixtures), for voice answer tests."""

from dataclasses import dataclass

import pytest

from app import scoring
from app.features.analyze import service as analyze_service
from app.features.members.models import Member
from app.features.products import service as products_service
from scripts.export_fixture_responses import (
    REFERENCE_DATE,
    fixture_member_record,
    fixture_product_record,
)


@dataclass(frozen=True)
class Case:
    result: scoring.AnalysisResult
    member: Member

    @property
    def verdict(self) -> scoring.MemberVerdict:
        return self.result.verdicts[0]


def case(product: str, member: str, *, name: str = "Asha") -> Case:
    record = fixture_member_record(member)
    record.name = name
    found = products_service.lookup_from_record(fixture_product_record(product))
    result = analyze_service.evaluate(found, [record], today=REFERENCE_DATE)
    return Case(result=result, member=record)


@pytest.fixture
def avoid_case() -> Case:
    c = case("sf_biscuit", "diabetic_adult")
    assert c.verdict.status is scoring.Status.AVOID
    return c


@pytest.fixture
def peanut_avoid_case() -> Case:
    c = case("namkeen", "peanut_allergic")
    assert c.verdict.status is scoring.Status.AVOID
    return c


@pytest.fixture
def unknown_case() -> Case:
    c = case("no_ingredients", "peanut_allergic")
    assert c.verdict.status is scoring.Status.UNKNOWN
    return c


@pytest.fixture
def ok_case() -> Case:
    c = case("water", "diabetic_adult")
    assert c.verdict.status is scoring.Status.OK
    return c
