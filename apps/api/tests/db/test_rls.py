"""Row-level security: account B can neither read nor write account A's rows."""

import uuid

import pytest
from sqlalchemy import text
from sqlalchemy.exc import DBAPIError

from tests.db.conftest import TABLES, as_anon, as_user

OWNED = ("members", "consents", "scans", "meal_logs", "product_reports")
SERVER_ONLY = ("off_product_cache", "rate_limit_counters", "explanation_cache")
INSUFFICIENT_PRIVILEGE = "42501"


async def _expect_denied(db, sql: str, params: dict | None = None) -> None:
    """The statement must fail with 42501 (RLS violation or missing privilege)."""
    with pytest.raises(DBAPIError) as exc_info:
        async with db.begin_nested():
            await db.execute(text(sql), params or {})
    assert exc_info.value.orig.sqlstate == INSUFFICIENT_PRIVILEGE, exc_info.value


async def _rowcount(db, sql: str, params: dict | None = None) -> int:
    async with db.begin_nested():
        return (await db.execute(text(sql), params or {})).rowcount


async def test_all_tables_have_rls(db):
    rows = await db.execute(
        text(
            "select relname, relrowsecurity, relforcerowsecurity from pg_class "
            "where relname = any(:t) and relnamespace = 'public'::regnamespace"
        ),
        {"t": list(TABLES)},
    )
    rows = rows.all()
    assert {r.relname: r.relrowsecurity for r in rows} == {t: True for t in TABLES}
    assert {r.relname: r.relforcerowsecurity for r in rows} == {t: True for t in TABLES}


async def test_policies_are_exactly_as_designed(db):
    rows = (
        await db.execute(
            text("select tablename, cmd, roles from pg_policies where schemaname = 'public'")
        )
    ).all()
    got = {(r.tablename, r.cmd) for r in rows}
    assert got == {
        ("accounts", "SELECT"),
        ("accounts", "UPDATE"),
        ("members", "ALL"),
        ("consents", "ALL"),
        ("scans", "ALL"),
        ("product_reports", "ALL"),
        ("meal_logs", "ALL"),
        ("products", "SELECT"),
    }
    assert all(list(r.roles) == ["authenticated"] for r in rows)


async def test_auth_uid_reads_jwt_claims(db, two_accounts):
    async with as_user(db, two_accounts.a):
        assert (await db.execute(text("select auth.uid()"))).scalar() == two_accounts.a
    await db.execute(
        text("select set_config('request.jwt.claim.sub', :s, true)"), {"s": str(two_accounts.b)}
    )
    assert (await db.execute(text("select auth.uid()"))).scalar() == two_accounts.b
    await db.execute(text("select set_config('request.jwt.claim.sub', '', true)"))
    assert (await db.execute(text("select auth.uid()"))).scalar() is None


async def test_member_isolation(db, two_accounts):
    async with as_user(db, two_accounts.b):
        names = (await db.execute(text("select name from members"))).scalars().all()
    assert names == ["B member"]


async def test_account_sees_only_itself(db, two_accounts):
    async with as_user(db, two_accounts.b):
        ids = (await db.execute(text("select id from accounts"))).scalars().all()
        assert ids == [two_accounts.b]
        n = await _rowcount(
            db, "update accounts set display_name = 'x' where id = :id", {"id": two_accounts.a}
        )
        assert n == 0
        assert (
            await _rowcount(db, "delete from accounts where id = :id", {"id": two_accounts.a}) == 0
        )
        await _expect_denied(db, "insert into accounts (id) values (:id)", {"id": uuid.uuid4()})
        await _expect_denied(
            db,
            "update accounts set id = :a where id = :b",
            {"a": uuid.uuid4(), "b": two_accounts.b},
        )
        assert (
            await _rowcount(
                db,
                "update accounts set display_name = 'mine' where id = :id",
                {"id": two_accounts.b},
            )
            == 1
        )


@pytest.mark.parametrize("table", OWNED)
async def test_owned_tables_hide_other_accounts_rows(db, two_accounts, table):
    async with as_user(db, two_accounts.b):
        ids = set((await db.execute(text(f"select id from {table}"))).scalars().all())
    seed_b, seed_a = two_accounts.seed_b, two_accounts.seed_a
    own = {
        "members": seed_b.member,
        "consents": seed_b.consent,
        "scans": seed_b.scan,
        "meal_logs": seed_b.meal_log,
        "product_reports": seed_b.report,
    }[table]
    other = {
        "members": seed_a.member,
        "consents": seed_a.consent,
        "scans": seed_a.scan,
        "meal_logs": seed_a.meal_log,
        "product_reports": seed_a.report,
    }[table]
    assert ids == {own}
    assert other not in ids


@pytest.mark.parametrize("table", OWNED)
async def test_owned_tables_block_update_and_delete_of_other_accounts_rows(db, two_accounts, table):
    other = {
        "members": two_accounts.seed_a.member,
        "consents": two_accounts.seed_a.consent,
        "scans": two_accounts.seed_a.scan,
        "meal_logs": two_accounts.seed_a.meal_log,
        "product_reports": two_accounts.seed_a.report,
    }[table]
    async with as_user(db, two_accounts.b):
        assert (
            await _rowcount(
                db, f"update {table} set account_id = account_id where id = :id", {"id": other}
            )
            == 0
        )
        assert await _rowcount(db, f"delete from {table} where id = :id", {"id": other}) == 0
    still = await db.execute(text(f"select count(*) from {table} where id = :id"), {"id": other})
    assert still.scalar() == 1


@pytest.mark.parametrize("table", OWNED)
async def test_owned_tables_block_moving_own_row_to_other_account(db, two_accounts, table):
    own = {
        "members": two_accounts.seed_b.member,
        "consents": two_accounts.seed_b.consent,
        "scans": two_accounts.seed_b.scan,
        "meal_logs": two_accounts.seed_b.meal_log,
        "product_reports": two_accounts.seed_b.report,
    }[table]
    async with as_user(db, two_accounts.b):
        await _expect_denied(
            db,
            f"update {table} set account_id = :a where id = :id",
            {"a": two_accounts.a, "id": own},
        )


async def test_inserts_into_other_account_are_denied(db, two_accounts):
    a, b, p = two_accounts.a, two_accounts.b, two_accounts.product
    async with as_user(db, b):
        await _expect_denied(
            db,
            "insert into members (account_id, name, relation) values (:a, 'evil', 'self')",
            {"a": a},
        )
        await _expect_denied(
            db,
            "insert into consents (account_id, purpose, version) values (:a, 'terms', 'v1')",
            {"a": a},
        )
        await _expect_denied(
            db,
            "insert into scans (account_id) values (:a)",
            {"a": a},
        )
        await _expect_denied(
            db,
            "insert into product_reports (account_id, product_id, reason) values (:a, :p, 'other')",
            {"a": a, "p": p},
        )
        await _expect_denied(
            db,
            "insert into meal_logs (account_id, member_id, product_id, grams, nutrients) "
            "values (:a, :m, :p, 10, '{}')",
            {"a": a, "m": two_accounts.seed_a.member, "p": p},
        )
        # Own account_id but somebody else's member: blocked by the members check.
        await _expect_denied(
            db,
            "insert into meal_logs (account_id, member_id, product_id, grams, nutrients) "
            "values (:b, :m, :p, 10, '{}')",
            {"b": b, "m": two_accounts.seed_a.member, "p": p},
        )
        # Own rows are allowed.
        assert (
            await _rowcount(
                db,
                "insert into meal_logs (account_id, member_id, product_id, grams, nutrients) "
                "values (:b, :m, :p, 10, '{}')",
                {"b": b, "m": two_accounts.seed_b.member, "p": p},
            )
            == 1
        )
        assert (
            await _rowcount(
                db,
                "insert into members (account_id, name, relation) values (:b, 'kid', 'child')",
                {"b": b},
            )
            == 1
        )


async def test_meal_logs_scoped_through_members(db, two_accounts):
    # Even a row stamped with B's account_id is hidden from B if the member is A's.
    await db.execute(
        text(
            "insert into meal_logs (account_id, member_id, product_id, grams, nutrients) "
            "values (:b, :m, :p, 5, '{}')"
        ),
        {"b": two_accounts.b, "m": two_accounts.seed_a.member, "p": two_accounts.product},
    )
    async with as_user(db, two_accounts.b):
        rows = (await db.execute(text("select id, member_id from meal_logs"))).all()
    assert [r.id for r in rows] == [two_accounts.seed_b.meal_log]
    assert all(r.member_id == two_accounts.seed_b.member for r in rows)


async def test_products_are_read_only_for_users(db, two_accounts):
    async with as_user(db, two_accounts.b):
        ids = (await db.execute(text("select id from products"))).scalars().all()
        assert ids == [two_accounts.product]
        await _expect_denied(
            db, "insert into products (name, category, source) values ('x', 'general', 'user')"
        )
        assert (
            await _rowcount(
                db,
                "update products set name = 'pwned' where id = :id",
                {"id": two_accounts.product},
            )
            == 0
        )
        assert (
            await _rowcount(db, "delete from products where id = :id", {"id": two_accounts.product})
            == 0
        )


@pytest.mark.parametrize("table", SERVER_ONLY)
async def test_server_only_tables_hidden(db, two_accounts, table):
    assert (await db.execute(text(f"select count(*) from {table}"))).scalar() == 1
    async with as_user(db, two_accounts.a):
        assert (await db.execute(text(f"select count(*) from {table}"))).scalar() == 0
        assert await _rowcount(db, f"delete from {table}") == 0
    assert (await db.execute(text(f"select count(*) from {table}"))).scalar() == 1


async def test_server_only_tables_reject_user_writes(db, two_accounts):
    async with as_user(db, two_accounts.a):
        await _expect_denied(
            db, "insert into off_product_cache (barcode, payload) values ('1', '{}')"
        )
        await _expect_denied(
            db,
            "insert into rate_limit_counters (key, bucket, window_start, count) "
            "values ('k', 'voice', now(), 0)",
        )
        await _expect_denied(
            db,
            "insert into explanation_cache (product_id, profile_hash, language, payload) "
            "values (:p, 'x', 'en', '{}')",
            {"p": two_accounts.product},
        )
        assert await _rowcount(db, "update rate_limit_counters set count = 0") == 0


async def test_user_without_jwt_sub_sees_nothing(db, two_accounts):
    async with as_user(db, None):
        for table in TABLES - {"products"}:
            count = (await db.execute(text(f"select count(*) from {table}"))).scalar()
            assert count == 0, table


@pytest.mark.parametrize("table", sorted(TABLES))
async def test_anon_has_no_access(db, two_accounts, table):
    async with as_anon(db):
        await _expect_denied(db, f"select count(*) from {table}")
