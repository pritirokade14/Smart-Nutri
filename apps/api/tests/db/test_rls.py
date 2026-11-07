"""Row-level security and privileges (ADR 0013).

``authenticated`` has SELECT only, and RLS filters reads to the caller's own rows. Every
write by ``authenticated`` fails with 42501 (permission denied): the policies remain only
as defence in depth, and the API writes through a BYPASSRLS role.
"""

import uuid

import pytest
from sqlalchemy import text
from sqlalchemy.exc import DBAPIError

from tests.db.conftest import TABLES, as_anon, as_user

OWNED = (
    "members",
    "consents",
    "scans",
    "meal_logs",
    "product_reports",
    "account_user_types",
    "diary_goal_settings",
    "meal_slots",
    "diary_days",
)
# The column that identifies a row. account_user_types has one row per account (P9-R1).
KEY = {t: "id" for t in OWNED} | {
    "account_user_types": "account_id",
    "diary_goal_settings": "member_id",  # one row per member (Plan 10)
    "diary_days": "member_id",  # one row per member and local day (Plan 11)
}
# Reference tables (Plan 12): readable by every signed-in user, never writable by one.
REFERENCE = ("household_units", "foods", "food_portions")
SERVER_ONLY = (
    "off_product_cache",
    "rate_limit_counters",
    "explanation_cache",
    "deleted_accounts",
)
INSUFFICIENT_PRIVILEGE = "42501"


async def _expect_denied(db, sql: str, params: dict | None = None) -> None:
    """The statement must fail with 42501 (RLS violation or missing privilege)."""
    with pytest.raises(DBAPIError) as exc_info:
        async with db.begin_nested():
            await db.execute(text(sql), params or {})
    assert exc_info.value.orig.sqlstate == INSUFFICIENT_PRIVILEGE, exc_info.value


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
        ("account_user_types", "ALL"),
        ("diary_goal_settings", "ALL"),
        ("diary_days", "ALL"),
        ("meal_slots", "ALL"),
        ("household_units", "SELECT"),
        ("foods", "SELECT"),
        ("food_portions", "SELECT"),
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
        # Writes are denied outright: no write grant for authenticated.
        await _expect_denied(
            db, "update accounts set display_name = 'x' where id = :id", {"id": two_accounts.a}
        )
        await _expect_denied(
            db, "update accounts set display_name = 'mine' where id = :id", {"id": two_accounts.b}
        )
        await _expect_denied(db, "delete from accounts where id = :id", {"id": two_accounts.a})
        await _expect_denied(db, "insert into accounts (id) values (:id)", {"id": uuid.uuid4()})


@pytest.mark.parametrize("table", OWNED)
async def test_owned_tables_hide_other_accounts_rows(db, two_accounts, table):
    async with as_user(db, two_accounts.b):
        ids = set((await db.execute(text(f"select {KEY[table]} from {table}"))).scalars().all())
    own = _row_of(two_accounts.seed_b, table)
    other = _row_of(two_accounts.seed_a, table)
    assert ids == {own}
    assert other not in ids


def _row_of(seed, table):
    return {
        "members": seed.member,
        "consents": seed.consent,
        "scans": seed.scan,
        "meal_logs": seed.meal_log,
        "product_reports": seed.report,
        "account_user_types": seed.account,
        "diary_goal_settings": seed.member,
        "meal_slots": seed.slot,
        "diary_days": seed.member,
    }[table]


@pytest.mark.parametrize("table", OWNED)
async def test_owned_tables_deny_update_and_delete(db, two_accounts, table):
    for seed in (two_accounts.seed_a, two_accounts.seed_b):  # foreign row and own row
        row = _row_of(seed, table)
        async with as_user(db, two_accounts.b):
            key = KEY[table]
            await _expect_denied(
                db, f"update {table} set account_id = account_id where {key} = :id", {"id": row}
            )
            await _expect_denied(db, f"delete from {table} where {key} = :id", {"id": row})
        still = await db.execute(
            text(f"select count(*) from {table} where {KEY[table]} = :id"), {"id": row}
        )
        assert still.scalar() == 1


@pytest.mark.parametrize("table", OWNED)
async def test_owned_tables_deny_moving_row_to_other_account(db, two_accounts, table):
    async with as_user(db, two_accounts.b):
        await _expect_denied(
            db,
            f"update {table} set account_id = :a where {KEY[table]} = :id",
            {"a": two_accounts.a, "id": _row_of(two_accounts.seed_b, table)},
        )


async def test_all_inserts_by_authenticated_are_denied(db, two_accounts):
    a, b, p = two_accounts.a, two_accounts.b, two_accounts.product
    m_b = two_accounts.seed_b.member
    async with as_user(db, b):
        for owner in (a, b):  # someone else's account and its own
            await _expect_denied(
                db,
                "insert into members (account_id, name, relation) values (:o, 'x', 'self')",
                {"o": owner},
            )
            await _expect_denied(
                db,
                "insert into consents (account_id, purpose, version) values (:o, 'terms', 'v1')",
                {"o": owner},
            )
            await _expect_denied(db, "insert into scans (account_id) values (:o)", {"o": owner})
            await _expect_denied(
                db,
                "insert into product_reports (account_id, product_id, reason) "
                "values (:o, :p, 'other')",
                {"o": owner, "p": p},
            )
            await _expect_denied(
                db,
                "insert into meal_logs (account_id, member_id, product_id, grams, nutrients, "
                "local_date, meal_slot_id) values (:o, :m, :p, 10, '{}', current_date, :s)",
                {"o": owner, "m": m_b, "p": p, "s": two_accounts.seed_b.slot},
            )
            await _expect_denied(
                db,
                "insert into account_user_types (account_id, types) values (:o, '{gym}')",
                {"o": owner},
            )
            await _expect_denied(
                db,
                "insert into diary_goal_settings (member_id, account_id, direction, "
                "activity_level) values (:m, :o, 'maintain', 'light')",
                {"o": owner, "m": m_b},
            )
            await _expect_denied(
                db,
                "insert into meal_slots (account_id, member_id, position, custom_label) "
                "values (:o, :m, 1, 'x')",
                {"o": owner, "m": m_b},
            )
            await _expect_denied(
                db,
                "insert into diary_days (member_id, local_date, account_id, status) "
                "values (:m, current_date + 1, :o, 'none')",
                {"o": owner, "m": m_b},
            )


async def test_meal_logs_scoped_through_members(db, two_accounts):
    # Even a row stamped with B's account_id is hidden from B if the member is A's.
    await db.execute(
        text(
            "insert into meal_logs (account_id, member_id, product_id, grams, nutrients, "
            "local_date, meal_slot_id) values (:b, :m, :p, 5, '{}', current_date, :s)"
        ),
        {
            "b": two_accounts.b,
            "m": two_accounts.seed_a.member,
            "p": two_accounts.product,
            "s": two_accounts.seed_a.slot,
        },
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
        await _expect_denied(
            db, "update products set name = 'pwned' where id = :id", {"id": two_accounts.product}
        )
        await _expect_denied(
            db, "delete from products where id = :id", {"id": two_accounts.product}
        )


@pytest.mark.parametrize("table", SERVER_ONLY)
async def test_server_only_tables_are_inaccessible(db, two_accounts, table):
    assert (await db.execute(text(f"select count(*) from {table}"))).scalar() == 1
    async with as_user(db, two_accounts.a):
        await _expect_denied(db, f"select count(*) from {table}")
        await _expect_denied(db, f"delete from {table}")
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
        await _expect_denied(db, "update rate_limit_counters set count = 0")
        # Deletion tombstones (D1/B1): a user can neither lift one nor plant one.
        await _expect_denied(
            db, "insert into deleted_accounts (id) values (:id)", {"id": two_accounts.a}
        )
        await _expect_denied(db, "delete from deleted_accounts")
        await _expect_denied(db, "update deleted_accounts set deleted_at = now()")


async def test_user_without_jwt_sub_sees_nothing(db, two_accounts):
    async with as_user(db, None):
        for table in TABLES - {"products", "household_units", "foods", *SERVER_ONLY}:
            count = (await db.execute(text(f"select count(*) from {table}"))).scalar()
            assert count == 0, table


@pytest.mark.parametrize("table", sorted(TABLES))
async def test_anon_has_no_access(db, two_accounts, table):
    async with as_anon(db):
        await _expect_denied(db, f"select count(*) from {table}")


async def _seed_reference(db, two_accounts) -> None:
    food = (
        await db.execute(
            text(
                "insert into foods (source, source_code, name_en, search_text, basis, per_100, "
                "licence, data_version) values ('usda_fdc', 'rls-1', 'RLS dal', 'rls dal', 'g', "
                "'{}', 'CC0 1.0', 'v') returning id"
            )
        )
    ).scalar_one()
    for acc, source, unit in (
        (None, "reference_table", "roti"),
        (two_accounts.a, "user", "piece"),
        (two_accounts.b, "user", "piece"),
    ):
        await db.execute(
            text(
                "insert into food_portions (account_id, food_id, unit, grams_per_unit, source) "
                "values (:acc, :f, :u, 40, :s)"
            ),
            {"acc": acc, "f": food, "u": unit, "s": source},
        )


async def test_reference_tables_read_only(db, two_accounts):
    await _seed_reference(db, two_accounts)
    async with as_user(db, two_accounts.a):
        assert (await db.execute(text("select count(*) from household_units"))).scalar() == 17
        assert (await db.execute(text("select count(*) from foods"))).scalar() == 1
        await _expect_denied(
            db,
            "insert into household_units (code, kind, sort) values ('x', 'count', 99)",
        )
        await _expect_denied(db, "update household_units set sort = 0 where code = 'g'")
        await _expect_denied(db, "delete from household_units where code = 'g'")
        await _expect_denied(
            db,
            "insert into foods (source, source_code, name_en, search_text, basis, per_100, "
            "licence, data_version) values ('usda_fdc', 'x', 'x', 'x', 'g', '{}', 'l', 'v')",
        )
        await _expect_denied(db, "update foods set name_en = 'pwned'")
        await _expect_denied(db, "delete from foods")
        await _expect_denied(
            db,
            "insert into food_portions (account_id, food_id, unit, grams_per_unit, source) "
            "select :a, id, 'slice', 30, 'user' from foods",
            {"a": two_accounts.a},
        )
        await _expect_denied(db, "update food_portions set grams_per_unit = 1")
        await _expect_denied(db, "delete from food_portions")


async def test_food_portions_global_and_own_rows_only(db, two_accounts):
    await _seed_reference(db, two_accounts)
    for me, other in ((two_accounts.a, two_accounts.b), (two_accounts.b, two_accounts.a)):
        async with as_user(db, me):
            owners = (
                (await db.execute(text("select account_id from food_portions"))).scalars().all()
            )
        assert sorted(owners, key=str) == sorted([None, me], key=str)
        assert other not in owners
    async with as_user(db, None):
        owners = (await db.execute(text("select account_id from food_portions"))).scalars().all()
    assert owners == [None]  # a user with no sub sees the global row only
