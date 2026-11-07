"""Exact privileges per role per table (ADR 0013): users get SELECT only, anon gets nothing.

The ``migrated`` fixture first emulates Supabase's default privileges (ALL to anon,
authenticated and service_role on every new public table), so these tests prove the
migration revokes them.
"""

import pytest
from sqlalchemy import text
from sqlalchemy.exc import DBAPIError

from tests.db.conftest import TABLES, as_anon, as_user

SELECT_ONLY_FOR_USERS = {
    "accounts",
    "members",
    "consents",
    "scans",
    "meal_logs",
    "product_reports",
    "products",
    "account_user_types",
    "diary_goal_settings",
    "meal_slots",
    "diary_days",
    "household_units",
    "foods",
    "food_portions",
    "custom_foods",
    "recipes",
    "recipe_ingredients",
    "favourites",
    "weight_logs",
}
ALL_PRIVILEGES = {
    "SELECT",
    "INSERT",
    "UPDATE",
    "DELETE",
    "TRUNCATE",
    "REFERENCES",
    "TRIGGER",
}
ALL_TABLES = TABLES | {"alembic_version"}


async def _grants(db, role: str) -> dict[str, set[str]]:
    rows = await db.execute(
        text(
            "select table_name, privilege_type from information_schema.role_table_grants "
            "where table_schema = 'public' and grantee = :r"
        ),
        {"r": role},
    )
    out: dict[str, set[str]] = {}
    for name, priv in rows.all():
        out.setdefault(name, set()).add(priv)
    return out


async def test_anon_has_no_privileges_anywhere(db):
    assert await _grants(db, "anon") == {}
    assert await _grants(db, "PUBLIC") == {}


async def test_authenticated_is_select_only_on_user_tables(db):
    assert await _grants(db, "authenticated") == {t: {"SELECT"} for t in SELECT_ONLY_FOR_USERS}


async def test_service_role_keeps_all_on_app_tables_but_not_alembic_version(db):
    assert await _grants(db, "service_role") == {t: ALL_PRIVILEGES for t in TABLES}


@pytest.mark.parametrize("role", ["anon", "authenticated"])
@pytest.mark.parametrize("table", sorted(ALL_TABLES))
async def test_has_table_privilege_matrix(db, role, table):
    for priv in sorted(ALL_PRIVILEGES):
        got = (
            await db.execute(
                text("select has_table_privilege(:r, :t, :p)"),
                {"r": role, "t": f"public.{table}", "p": priv},
            )
        ).scalar()
        expected = role == "authenticated" and priv == "SELECT" and table in SELECT_ONLY_FOR_USERS
        assert got is expected, (role, table, priv)


async def test_alembic_version_has_rls_and_is_unreadable(db):
    row = (
        await db.execute(
            text(
                "select relrowsecurity from pg_class where oid = 'public.alembic_version'::regclass"
            )
        )
    ).scalar()
    assert row is True
    async with as_anon(db):
        await _denied(db, "select * from alembic_version")
    async with as_user(db, None):
        await _denied(db, "select * from alembic_version")


async def _denied(db, sql: str) -> None:
    with pytest.raises(DBAPIError) as exc_info:
        async with db.begin_nested():
            await db.execute(text(sql))
    assert exc_info.value.orig.sqlstate == "42501"


@pytest.mark.parametrize("table", sorted(ALL_TABLES))
async def test_authenticated_cannot_truncate(db, two_accounts, table):
    async with as_user(db, two_accounts.a):
        await _denied(db, f"truncate table {table} cascade")


async def test_anon_cannot_truncate(db):
    async with as_anon(db):
        await _denied(db, "truncate table members")
