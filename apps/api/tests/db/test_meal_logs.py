"""meal_logs: RLS, the offline idempotency key and the product reference (Plan 6 T2).

The table itself is in 0001_baseline (CROSS-PLAN-NOTES 12); 0003_plan6_meal_logs_off lets a
log point at an Open Food Facts product by barcode (CROSS-PLAN-NOTES 11, ADR 0017).
"""

import uuid
from datetime import date

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
        "local_date": date(2026, 11, 7),
        "meal_slot_id": seed.slot,
        "source_kind": "product" if product else "off",
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
    assert "ck_meal_logs_ref" in str(exc_info.value)


async def test_grade_is_a_to_e(db, two_accounts):
    await _insert(db, two_accounts.seed_a, two_accounts.product, grade="A")
    with pytest.raises(IntegrityError) as exc_info:
        await _insert(db, two_accounts.seed_a, two_accounts.product, grade="F")
    assert "ck_meal_logs_grade" in str(exc_info.value)


def test_summary_identical_after_backfill(migrated):
    """Plan 11 Task 1: the week_family rows inserted BEFORE migration 0009 give the same
    `summarise` totals after the back-fill (the legacy summary rule is unchanged)."""
    from sqlalchemy import create_engine, select
    from sqlalchemy.orm import Session
    from sqlalchemy.pool import NullPool

    from alembic import command
    from app import scoring
    from app.core.time import IST
    from app.features.meals.models import MealLog
    from app.features.meals.summary import summarise
    from app.features.members.service import to_scoring_member
    from scripts.export_meal_fixtures import WEEK_FAMILY_ACCOUNT, load_week_family

    family = load_week_family()
    dad = family.members["dad"]
    dad_id = dad.id
    limits = scoring.daily_limits_for(to_scoring_member(dad, today=family.end_date), dad.weight_kg)
    before = summarise(
        [m for m in family.meals if m.member_id == dad.id],
        limits,
        "week",
        family.end_date,
        IST,
        member_id=dad.id,
    ).model_dump(mode="json")

    url = migrated.get_main_option("sqlalchemy.url")
    engine = create_engine(url, poolclass=NullPool)
    try:
        command.downgrade(migrated, "0008_diary_goal_settings")
        with Session(engine, expire_on_commit=False) as s, s.begin():
            s.execute(text("insert into accounts (id) values (:a)"), {"a": WEEK_FAMILY_ACCOUNT})
            s.add_all(list(family.members.values()))
            s.add_all(family.products)
            s.flush()
            for m in family.meals:
                s.execute(
                    text(
                        "insert into meal_logs (id, account_id, member_id, product_id, "
                        "off_barcode, product_name, grade, grams, eaten_at, nutrients) values "
                        "(:id, :a, :m, :p, :b, :n, :g, :gr, :at, cast(:nu as jsonb))"
                    ),
                    {
                        "id": m.id,
                        "a": m.account_id,
                        "m": m.member_id,
                        "p": m.product_id,
                        "b": m.off_barcode,
                        "n": m.product_name,
                        "g": m.grade,
                        "gr": m.grams,
                        "at": m.eaten_at,
                        "nu": __import__("json").dumps(m.nutrients),
                    },
                )
        command.upgrade(migrated, "head")
        with Session(engine) as s:
            rows = list(s.scalars(select(MealLog).where(MealLog.member_id == dad_id)))
            assert rows and all(r.meal_slot_id and r.local_date for r in rows)
            after = summarise(
                rows, limits, "week", family.end_date, IST, member_id=dad_id
            ).model_dump(mode="json")
        assert after == before
        with Session(engine) as s, s.begin():
            s.execute(text("delete from accounts where id = :a"), {"a": WEEK_FAMILY_ACCOUNT})
            for p in family.products:
                s.execute(text("delete from products where id = :p"), {"p": p.id})
    finally:
        command.upgrade(migrated, "head")
        engine.dispose()
