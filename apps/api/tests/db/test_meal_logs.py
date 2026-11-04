"""meal_logs: RLS, the offline idempotency key and the product reference (Plan 6 T2).

The table itself is in 0001_baseline (CROSS-PLAN-NOTES 12); 0003_plan6_meal_logs_off lets a
log point at an Open Food Facts product by barcode (CROSS-PLAN-NOTES 11, ADR 0017).
"""

import uuid

import pytest
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError

OFF_BARCODE = "8901063201089"


async def _insert(db, seed, product, **cols):
    values = {
        "account_id": seed.account,
        "member_id": seed.member,
        "product_id": product,
        "grams": 30,
        "nutrients": "{}",
        **cols,
    }
    names = ", ".join(values)
    params = ", ".join(f"cast(:{k} as jsonb)" if k == "nutrients" else f":{k}" for k in values)
    async with db.begin_nested():
        await db.execute(text(f"insert into meal_logs ({names}) values ({params})"), values)


async def test_meal_logs_rls_and_unique_client_id(db, two_accounts):
    rls = (
        await db.execute(
            text(
                "select relrowsecurity, relforcerowsecurity from pg_class "
                "where relname = 'meal_logs' and relnamespace = 'public'::regnamespace"
            )
        )
    ).one()
    assert tuple(rls) == (True, True)
    policies = (
        await db.execute(text("select policyname from pg_policies where tablename = 'meal_logs'"))
    ).scalars()
    assert list(policies) == ["meal_logs_owner"]

    seed, product = two_accounts.seed_a, two_accounts.product
    client_id = uuid.uuid4()
    await _insert(db, seed, product, client_id=client_id)
    with pytest.raises(IntegrityError) as exc_info:
        await _insert(db, seed, product, client_id=client_id)
    assert "uq_meal_logs_account_id_client_id" in str(exc_info.value)
    # Another account may use the same client id; null client ids are never constrained.
    await _insert(db, two_accounts.seed_b, product, client_id=client_id)
    await _insert(db, seed, product, client_id=None)
    await _insert(db, seed, product, client_id=None)


async def test_off_product_by_barcode_without_product_id(db, two_accounts):
    await _insert(
        db,
        two_accounts.seed_a,
        None,
        off_barcode=OFF_BARCODE,
        product_name="OFF Biscuit",
        grade="D",
    )


@pytest.mark.parametrize("both", [True, False])
async def test_exactly_one_product_reference(db, two_accounts, both):
    product = two_accounts.product if both else None
    barcode = OFF_BARCODE if both else None
    with pytest.raises(IntegrityError) as exc_info:
        await _insert(db, two_accounts.seed_a, product, off_barcode=barcode)
    assert "ck_meal_logs_product_ref" in str(exc_info.value)


async def test_grade_is_a_to_e(db, two_accounts):
    await _insert(db, two_accounts.seed_a, two_accounts.product, grade="A")
    with pytest.raises(IntegrityError) as exc_info:
        await _insert(db, two_accounts.seed_a, two_accounts.product, grade="F")
    assert "ck_meal_logs_grade" in str(exc_info.value)
