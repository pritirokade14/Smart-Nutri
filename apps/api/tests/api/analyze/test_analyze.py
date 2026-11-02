from datetime import date
from uuid import UUID, uuid4

import httpx
import pytest
from sqlalchemy import func, select

from app.core.config import Settings
from app.core.security import AccountContext, current_account
from app.db.session import get_session
from app.features.me.service import ensure_account
from app.features.members.models import Member
from app.features.members.service import get_or_create_primary, to_scoring_member
from app.features.scans.models import Scan
from app.integrations.openfoodfacts import get_off_client
from app.main import create_app
from app.scoring import Diet
from scripts.export_fixture_responses import fixture_product_record
from tests.api.analyze.conftest import OFF_BARCODE, A, B, today
from tests.api.products.test_lookup_service import FakeOff

URL = "/v1/analyze"


async def _scans(db_session, account_id: UUID) -> list[Scan]:
    rows = await db_session.scalars(
        select(Scan).where(Scan.account_id == account_id).execution_options(populate_existing=True)
    )
    return list(rows)


# --- members/service helpers -------------------------------------------------------------


def test_to_scoring_member_maps_fields():
    record = Member(
        id=uuid4(),
        account_id=A,
        name="Ravi",
        relation="parent",
        birth_year=1966,
        diet="jain",
        allergens=["peanut"],
        conditions=["diabetes"],
        custom_alerts=[],
        goal="weight_loss",
    )
    m = to_scoring_member(record, today=date(2026, 11, 3))
    assert m.id == str(record.id)
    assert m.age == 59  # youngest possible age (birthday may still be ahead)
    assert m.diet is Diet.JAIN
    assert m.allergens == ("peanut",) and m.conditions == ("diabetes",)
    assert m.goal == "weight_loss"


def test_to_scoring_member_without_birth_year_has_no_age():
    record = Member(id=uuid4(), account_id=A, name="X", relation="self", diet="non_veg")
    assert to_scoring_member(record, today=date(2026, 1, 1)).age is None


def test_to_scoring_member_future_birth_year_is_unknown_age():
    record = Member(
        id=uuid4(), account_id=A, name="X", relation="child", birth_year=2030, diet="non_veg"
    )
    assert to_scoring_member(record, today=date(2026, 1, 1)).age is None


@pytest.mark.parametrize(
    ("birth_year", "age"), [(2024, 1), (2026, 0), (2025, 0), (2013, 12), (2027, None)]
)
def test_to_scoring_member_uses_youngest_possible_age(birth_year, age):
    """Younger age bands are stricter, so a birth year maps to the youngest age it allows."""
    record = Member(
        id=uuid4(), account_id=A, name="X", relation="child", birth_year=birth_year, diet="non_veg"
    )
    assert to_scoring_member(record, today=date(2026, 1, 1)).age == age


async def test_get_or_create_primary_is_idempotent(db_session, count_members, member_no_birth_year):
    first = await get_or_create_primary(db_session, A)
    second = await get_or_create_primary(db_session, A)
    assert first.id == second.id != member_no_birth_year.id
    assert first.is_primary and first.relation == "self" and first.diet == "non_veg"
    assert first.allergens == [] and first.conditions == [] and first.custom_alerts == []
    assert await count_members(A) == 2


# --- POST /v1/analyze ----------------------------------------------------------------------


async def test_requires_auth(client):
    r = await client.post(URL, json={"barcode": OFF_BARCODE})
    assert r.status_code == 401


async def test_requires_exactly_one_product_ref(auth_client, seeded_product):
    r = await auth_client.post(URL, json={"language": "en"})
    assert r.status_code == 422
    assert r.json()["error"]["code"] == "invalid_product_ref"
    r = await auth_client.post(
        URL, json={"product_id": str(seeded_product.id), "barcode": OFF_BARCODE}
    )
    assert r.status_code == 422
    assert r.json()["error"]["code"] == "invalid_product_ref"


async def test_rejects_unknown_language(auth_client, seeded_product):
    r = await auth_client.post(URL, json={"product_id": str(seeded_product.id), "language": "fr"})
    assert r.status_code == 422 and r.json()["error"]["code"] == "validation_error"


async def test_first_call_for_new_account_succeeds(auth_client, seeded_product, count_members):
    """current_account_row creates the account row before the primary member is inserted."""
    r = await auth_client.post(URL, json={"product_id": str(seeded_product.id)})
    assert r.status_code == 200, r.text
    assert await count_members(A) == 1


async def test_primary_member_created_once(auth_client, seeded_product, count_members):
    r1 = await auth_client.post(URL, json={"product_id": str(seeded_product.id)})
    r2 = await auth_client.post(URL, json={"product_id": str(seeded_product.id)})
    assert r1.status_code == r2.status_code == 200
    assert await count_members(auth_client.account_id) == 1
    v1, v2 = r1.json()["verdicts"], r2.json()["verdicts"]
    assert len(v1) == len(v2) == 1 and v1[0]["member_id"] == v2[0]["member_id"]


async def test_response_shape(auth_client, seeded_product):
    r = await auth_client.post(URL, json={"product_id": str(seeded_product.id), "language": "hi"})
    assert r.status_code == 200
    body = r.json()
    assert UUID(body["scan_id"])
    assert body["product"]["source"] == "smartnutri"
    assert body["product"]["product_id"] == str(seeded_product.id)
    assert body["product"]["attribution"] is None
    assert "nutriscore" in body["report"]
    assert body["explanation"] is None and body["tips"] == []
    (v,) = body["verdicts"]
    assert v["status"] in {"ok", "caution", "unknown", "avoid"}
    assert set(v) == {"member_id", "member_name", "status", "reasons"}
    for reason in v["reasons"]:
        assert set(reason) == {"code", "severity", "params"}


async def test_unknown_product_id_is_404(auth_client):
    r = await auth_client.post(URL, json={"product_id": str(uuid4())})
    assert r.status_code == 404 and r.json()["error"]["code"] == "product_not_found"


async def test_rejected_product_is_404(auth_client, seeded_product, db_session):
    seeded_product.verification_status = "rejected"
    await db_session.flush()
    r = await auth_client.post(URL, json={"product_id": str(seeded_product.id)})
    assert r.status_code == 404 and r.json()["error"]["code"] == "product_not_found"


async def test_foreign_member_is_404(auth_client, other_account_member, seeded_product):
    r = await auth_client.post(
        URL,
        json={"product_id": str(seeded_product.id), "member_ids": [str(other_account_member.id)]},
    )
    assert r.status_code == 404
    assert r.json()["error"]["code"] == "member_not_found"
    assert "Other" not in r.text


async def test_unknown_member_is_same_404(auth_client, seeded_product, own_member):
    r = await auth_client.post(
        URL,
        json={
            "product_id": str(seeded_product.id),
            "member_ids": [str(own_member.id), str(uuid4())],
        },
    )
    assert r.status_code == 404
    assert r.json()["error"] == {
        "code": "member_not_found",
        "message_key": "error.member_not_found",
        "details": {},
    }


async def test_member_ids_order_and_names(
    auth_client, seeded_product, own_member, member_no_birth_year
):
    ids = [str(member_no_birth_year.id), str(own_member.id)]
    r = await auth_client.post(URL, json={"product_id": str(seeded_product.id), "member_ids": ids})
    assert r.status_code == 200
    verdicts = r.json()["verdicts"]
    assert [v["member_id"] for v in verdicts] == ids
    assert [v["member_name"] for v in verdicts] == ["Asha", "Ravi"]
    r = await auth_client.post(
        URL, json={"product_id": str(seeded_product.id), "member_ids": ids[::-1]}
    )
    assert [v["member_id"] for v in r.json()["verdicts"]] == ids[::-1]


async def test_explicit_members_do_not_create_primary(
    auth_client, seeded_product, own_member, count_members
):
    r = await auth_client.post(
        URL, json={"product_id": str(seeded_product.id), "member_ids": [str(own_member.id)]}
    )
    assert r.status_code == 200
    assert await count_members(A) == 1


async def test_member_without_birth_year_does_not_crash(
    auth_client, member_no_birth_year, cola_product
):
    r = await auth_client.post(
        URL,
        json={"product_id": str(cola_product.id), "member_ids": [str(member_no_birth_year.id)]},
    )
    assert r.status_code == 200
    (v,) = r.json()["verdicts"]
    codes = [x["code"] for x in v["reasons"]]
    assert not [c for c in codes if c.startswith(("child_", "infant_"))]
    assert "age_unknown" in codes
    assert v["status"] == "unknown"


async def test_scan_row_written(auth_client, seeded_product, db_session):
    r = await auth_client.post(URL, json={"product_id": str(seeded_product.id)})
    assert r.status_code == 200
    (scan,) = await _scans(db_session, A)
    assert str(scan.id) == r.json()["scan_id"]
    assert scan.product_id == seeded_product.id
    assert scan.analysis["barcode"] == seeded_product.barcode
    assert set(scan.analysis) == {"report", "verdicts", "barcode"}
    assert scan.analysis["verdicts"][0]["member_id"] == r.json()["verdicts"][0]["member_id"]
    # Member names never go into the stored analysis.
    assert "member_name" not in str(scan.analysis) and "name" not in scan.analysis["verdicts"][0]


async def test_off_barcode_analyze(auth_client, fake_off, db_session):
    r = await auth_client.post(URL, json={"barcode": " 8901 0632 0108 9 "})
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["product"]["source"] == "openfoodfacts"
    assert body["product"]["product_id"] is None
    assert body["product"]["attribution"] == "attribution.off"
    assert body["report"]["nutriscore"]["grade"] == "D"
    (scan,) = await _scans(db_session, A)
    assert scan.product_id is None and scan.analysis["barcode"] == OFF_BARCODE
    # The OFF cache write was committed with the scan: a second analyze is a cache hit.
    r = await auth_client.post(URL, json={"barcode": OFF_BARCODE})
    assert r.status_code == 200 and fake_off.calls == 1


async def test_off_not_found(auth_client, login):
    login(A, off=FakeOff(None))
    r = await auth_client.post(URL, json={"barcode": OFF_BARCODE})
    assert r.status_code == 404 and r.json()["error"]["code"] == "product_not_found"


async def test_off_unavailable_is_503(auth_client, login):
    login(A, off=FakeOff(fail=True))
    r = await auth_client.post(URL, json={"barcode": OFF_BARCODE})
    assert r.status_code == 503 and r.json()["error"]["code"] == "off_unavailable"


async def test_invalid_barcode(auth_client, fake_off):
    r = await auth_client.post(URL, json={"barcode": "abc123"})
    assert r.status_code == 422 and r.json()["error"]["code"] == "invalid_barcode"
    assert fake_off.calls == 0


async def test_foreign_member_with_off_barcode_never_calls_off(
    auth_client, fake_off, other_account_member
):
    r = await auth_client.post(
        URL, json={"barcode": OFF_BARCODE, "member_ids": [str(other_account_member.id)]}
    )
    assert r.status_code == 404 and fake_off.calls == 0


async def test_other_account_cannot_see_scans(auth_client, seeded_product, db_session, login):
    r = await auth_client.post(URL, json={"product_id": str(seeded_product.id)})
    assert r.status_code == 200
    login(B)
    r = await auth_client.post(URL, json={"product_id": str(seeded_product.id)})
    assert r.status_code == 200
    assert len(await _scans(db_session, A)) == 1 and len(await _scans(db_session, B)) == 1
    total = await db_session.scalar(select(func.count()).select_from(Scan))
    assert total == 2


async def test_analyze_rate_limited(db_session, seeded_product):
    app = create_app(Settings(_env_file=None, environment="test", rate_limit_analyze_per_hour=1))
    app.dependency_overrides[get_session] = lambda: db_session
    app.dependency_overrides[get_off_client] = lambda: FakeOff(None)
    app.dependency_overrides[current_account] = lambda: AccountContext(A, None)
    body = {"product_id": str(seeded_product.id)}
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://t") as c:
        assert (await c.post(URL, json=body)).status_code == 200
        r = await c.post(URL, json=body)
    assert r.status_code == 429 and r.json()["error"]["code"] == "rate_limited"


def _reason_pairs(verdict: dict) -> list[tuple[str, str]]:
    return [(r["code"], r["severity"]) for r in verdict["reasons"]]


async def _child(db_session, birth_year: int) -> Member:
    await ensure_account(db_session, AccountContext(A, None))
    member = Member(
        account_id=A, name="Kid", relation="child", birth_year=birth_year, diet="non_veg"
    )
    db_session.add(member)
    await db_session.flush()
    return member


async def test_birth_year_two_years_ago_is_treated_as_infant(auth_client, db_session):
    """Born today.year - 2: may still be 1, so the infant rules apply."""
    product = fixture_product_record("sf_biscuit")
    db_session.add(product)
    member = await _child(db_session, today().year - 2)
    r = await auth_client.post(
        URL, json={"product_id": str(product.id), "member_ids": [str(member.id)]}
    )
    assert r.status_code == 200
    (v,) = r.json()["verdicts"]
    assert v["status"] == "avoid"
    assert _reason_pairs(v) == [
        ("infant_added_salt", "avoid"),
        ("infant_added_sugar", "avoid"),
        ("infant_salt_high", "avoid"),
    ]


async def test_birth_year_thirteen_years_ago_is_treated_as_child(
    auth_client, db_session, cola_product
):
    """Born today.year - 13: may still be 12, so the child rules apply."""
    member = await _child(db_session, today().year - 13)
    r = await auth_client.post(
        URL, json={"product_id": str(cola_product.id), "member_ids": [str(member.id)]}
    )
    assert r.status_code == 200
    (v,) = r.json()["verdicts"]
    assert v["status"] == "avoid"
    assert _reason_pairs(v) == [("child_caffeine", "avoid"), ("child_sugar_high", "avoid")]


async def test_primary_member_on_cola_is_age_unknown(auth_client, cola_product):
    """A new account's primary member has no birth year: cola is unknown (age_unknown) only."""
    r = await auth_client.post(URL, json={"product_id": str(cola_product.id)})
    assert r.status_code == 200
    (v,) = r.json()["verdicts"]
    assert v["status"] == "unknown"
    assert _reason_pairs(v) == [("age_unknown", "unknown")]


async def test_duplicate_member_ids_rejected(auth_client, seeded_product, own_member):
    mid = str(own_member.id)
    r = await auth_client.post(
        URL, json={"product_id": str(seeded_product.id), "member_ids": [mid, mid]}
    )
    assert r.status_code == 422
    assert r.json()["error"]["code"] == "validation_error"
