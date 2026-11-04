"""POST /v1/products/{product_id}/reports (Plan 7 Task 6, F14): report a problem."""

from uuid import UUID, uuid4

import pytest
from sqlalchemy import func, select, text

from app.core.security import AccountContext, current_account
from app.db.session import get_session
from app.features.me.service import ensure_account
from app.features.products.models import Product
from app.features.reports.models import ProductReport
from tests.db.conftest import as_user

A = UUID("11111111-1111-1111-1111-111111111111")
B = UUID("22222222-2222-2222-2222-222222222222")


def _url(product_id) -> str:
    return f"/v1/products/{product_id}/reports"


@pytest.fixture
def login(app, db_session):
    def _login(account_id: UUID = A) -> None:
        app.dependency_overrides[get_session] = lambda: db_session
        app.dependency_overrides[current_account] = lambda: AccountContext(account_id, None)

    return _login


async def _product(db_session, **kw) -> Product:
    values = {
        "name": "Biscuit",
        "source": "label",
        "verification_status": "verified",
        "category": "general",
        "per_100g": {"sugars_g": 12.5},
        "claims": [],
    }
    row = Product(**{**values, **kw})
    db_session.add(row)
    await db_session.flush()
    return row


@pytest.fixture
async def product(db_session) -> Product:
    return await _product(db_session)


async def _count(db_session) -> int:
    return await db_session.scalar(select(func.count()).select_from(ProductReport))


async def test_create_report_201(client, login, product, db_session):
    login(A)
    r = await client.post(_url(product.id), json={"reason": "wrong_values", "note": "  sugar  "})
    assert r.status_code == 201, r.json()
    body = r.json()
    assert body["product_id"] == str(product.id)
    assert body["reason"] == "wrong_values" and body["status"] == "open"
    assert set(body) == {"id", "product_id", "reason", "status", "created_at"}
    row = await db_session.get(ProductReport, UUID(body["id"]))
    assert row.account_id == A and row.note == "sugar"  # stripped


async def test_blank_note_is_stored_as_null(client, login, product, db_session):
    login(A)
    r = await client.post(_url(product.id), json={"reason": "other", "note": "   "})
    row = await db_session.get(ProductReport, UUID(r.json()["id"]))
    assert row.note is None


async def test_duplicate_open_report_returns_existing_200(client, login, product, db_session):
    login(A)
    first = await client.post(_url(product.id), json={"reason": "wrong_ingredients"})
    again = await client.post(_url(product.id), json={"reason": "wrong_ingredients", "note": "x"})
    assert (first.status_code, again.status_code) == (201, 200)
    assert again.json()["id"] == first.json()["id"]
    assert await _count(db_session) == 1


async def test_other_reason_or_resolved_is_a_new_report(client, login, product, db_session):
    login(A)
    first = await client.post(_url(product.id), json={"reason": "wrong_values"})
    assert (await client.post(_url(product.id), json={"reason": "other"})).status_code == 201
    await db_session.execute(
        text("update product_reports set status = 'resolved' where id = :i"),
        {"i": first.json()["id"]},
    )
    assert (await client.post(_url(product.id), json={"reason": "wrong_values"})).status_code == 201
    assert await _count(db_session) == 3


async def test_same_report_from_another_account_is_separate(client, login, product, db_session):
    login(A)
    await client.post(_url(product.id), json={"reason": "wrong_values"})
    login(B)
    r = await client.post(_url(product.id), json={"reason": "wrong_values"})
    assert r.status_code == 201
    assert await _count(db_session) == 2


async def test_unknown_product_404(client, login):
    login(A)
    r = await client.post(_url(uuid4()), json={"reason": "wrong_values"})
    assert (r.status_code, r.json()["error"]["code"]) == (404, "product_not_found")


async def test_other_accounts_pending_product_404(client, login, db_session):
    await ensure_account(db_session, AccountContext(B, None))
    pending = await _product(db_session, verification_status="pending", created_by=B)
    login(A)
    r = await client.post(_url(pending.id), json={"reason": "wrong_values"})
    assert (r.status_code, r.json()["error"]["code"]) == (404, "product_not_found")


async def test_own_pending_product_can_be_reported(client, login, db_session):
    await ensure_account(db_session, AccountContext(A, None))
    pending = await _product(db_session, verification_status="pending", created_by=A)
    login(A)
    assert (await client.post(_url(pending.id), json={"reason": "other"})).status_code == 201


async def test_note_over_500_chars_422(client, login, product):
    login(A)
    r = await client.post(_url(product.id), json={"reason": "other", "note": "x" * 501})
    assert (r.status_code, r.json()["error"]["code"]) == (422, "validation_error")
    ok = await client.post(_url(product.id), json={"reason": "other", "note": "x" * 500})
    assert ok.status_code == 201


@pytest.mark.parametrize(
    "body", [{"reason": "spam"}, {}, {"reason": "other", "extra": 1}, {"reason": None}]
)
async def test_invalid_body_422(client, login, product, body):
    login(A)
    r = await client.post(_url(product.id), json=body)
    assert (r.status_code, r.json()["error"]["code"]) == (422, "validation_error")


async def test_invalid_product_id_422(client, login):
    login(A)
    r = await client.post(_url("not-a-uuid"), json={"reason": "other"})
    assert r.status_code == 422


async def test_requires_auth_401(client, product):
    r = await client.post(_url(product.id), json={"reason": "wrong_values"})
    assert r.status_code == 401


async def test_11th_report_rate_limited(client, login, product, db_session):
    login(A)
    reasons = ["wrong_values", "wrong_ingredients", "wrong_product", "other"]
    codes = []
    for i in range(11):
        r = await client.post(_url(product.id), json={"reason": reasons[i % 4]})
        codes.append(r.status_code)
    assert all(c in (200, 201) for c in codes[:10]) and codes[10] == 429
    r = await client.post(_url(product.id), json={"reason": "other"})
    assert r.json()["error"]["code"] == "rate_limited"


async def test_report_rls_hides_other_accounts_rows(client, login, product, db):
    login(A)
    a_id = (await client.post(_url(product.id), json={"reason": "wrong_values"})).json()["id"]
    login(B)
    b_id = (await client.post(_url(product.id), json={"reason": "wrong_values"})).json()["id"]
    async with as_user(db, B):
        rows = (await db.execute(text("select id from product_reports"))).scalars().all()
    assert {str(r) for r in rows} == {b_id} and a_id not in {str(r) for r in rows}
