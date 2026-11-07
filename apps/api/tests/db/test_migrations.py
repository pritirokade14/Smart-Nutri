import pytest
from alembic.autogenerate import compare_metadata
from alembic.migration import MigrationContext
from sqlalchemy import create_engine, inspect, text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.pool import NullPool

from alembic import command
from tests.db.conftest import TABLES


def _sync_url(cfg) -> str:
    return cfg.get_main_option("sqlalchemy.url")


def test_head_is_latest(migrated):
    engine = create_engine(_sync_url(migrated), poolclass=NullPool)
    with engine.connect() as conn:
        assert MigrationContext.configure(conn).get_current_revision() == "0008_diary_goal_settings"
    engine.dispose()


def test_single_alembic_head():
    """0006, 0007 and 0008 are chained, so there is exactly one head, 0008."""
    from alembic.config import Config
    from alembic.script import ScriptDirectory

    script = ScriptDirectory.from_config(Config("alembic.ini"))
    assert script.get_heads() == ["0008_diary_goal_settings"]
    assert script.get_revision("0008_diary_goal_settings").down_revision == (
        "0007_plan9_supplement_category"
    )
    assert script.get_revision("0007_plan9_supplement_category").down_revision == (
        "0006_plan9_user_types"
    )


def test_user_types_downgrades_cleanly(migrated):
    """Plan 9 (P9-R1): account_user_types comes and goes with 0006, with forced RLS, its
    owner policy, SELECT-only for users and its check constraints."""
    engine = create_engine(_sync_url(migrated), poolclass=NullPool)
    try:
        command.downgrade(migrated, "0005_plan8_tombstone_auth")
        with engine.connect() as conn:
            assert "account_user_types" not in inspect(conn).get_table_names()
        command.upgrade(migrated, "head")
        with engine.connect() as conn:
            row = conn.execute(
                text(
                    "select relrowsecurity, relforcerowsecurity from pg_class "
                    "where oid = 'public.account_user_types'::regclass"
                )
            ).one()
            assert tuple(row) == (True, True)
            policies = conn.execute(
                text(
                    "select policyname, cmd from pg_policies where tablename = 'account_user_types'"
                )
            ).all()
            assert [tuple(p) for p in policies] == [("account_user_types_owner", "ALL")]
            checks = {c["name"] for c in inspect(conn).get_check_constraints("account_user_types")}
            assert checks == {
                "ck_account_user_types_user_types",
                "ck_account_user_types_active_type",
            }
            for role, expected in (("anon", False), ("authenticated", True)):
                granted = conn.execute(
                    text("select has_table_privilege(:r, 'public.account_user_types', 'SELECT')"),
                    {"r": role},
                ).scalar()
                assert granted is expected, role
    finally:
        command.upgrade(migrated, "head")
        engine.dispose()


def test_user_types_check_constraints(migrated):
    """The table refuses more than 3 types, unknown types and an unselected active type."""
    engine = create_engine(_sync_url(migrated), poolclass=NullPool)
    bad = (
        "'{gym,family,weight_loss,eat_better}', null",
        "'{yoga}', null",
        "'{gym}', 'family'",
        "'{}', 'eat_better'",
    )
    try:
        with engine.connect() as conn:
            acc = conn.execute(
                text("insert into accounts (id) values (gen_random_uuid()) returning id")
            ).scalar_one()
            for values in bad:
                with pytest.raises(IntegrityError), conn.begin_nested():
                    conn.execute(
                        text(
                            "insert into account_user_types (account_id, types, active_type) "
                            f"values (:a, {values})"
                        ),
                        {"a": acc},
                    )
            conn.execute(
                text(
                    "insert into account_user_types (account_id, types, active_type) "
                    "values (:a, '{gym,family}', 'family')"
                ),
                {"a": acc},
            )
            conn.rollback()
    finally:
        engine.dispose()


def test_diary_goal_settings_downgrades_cleanly(migrated):
    """Plan 10 (Ruling D1): the settings table, `members.body_fat_pct` and the unique
    constraint come and go with 0008, and the table has forced RLS and its owner policy."""
    engine = create_engine(_sync_url(migrated), poolclass=NullPool)
    try:
        command.downgrade(migrated, "0007_plan9_supplement_category")
        with engine.connect() as conn:
            insp = inspect(conn)
            assert "diary_goal_settings" not in insp.get_table_names()
            assert "body_fat_pct" not in {c["name"] for c in insp.get_columns("members")}
            assert "uq_members_id_account_id" not in {
                c["name"] for c in insp.get_unique_constraints("members")
            }
        command.upgrade(migrated, "head")
        with engine.connect() as conn:
            insp = inspect(conn)
            assert "body_fat_pct" in {c["name"] for c in insp.get_columns("members")}
            assert "uq_members_id_account_id" in {
                c["name"] for c in insp.get_unique_constraints("members")
            }
            row = conn.execute(
                text(
                    "select relrowsecurity, relforcerowsecurity from pg_class "
                    "where oid = 'public.diary_goal_settings'::regclass"
                )
            ).one()
            assert tuple(row) == (True, True)
            policies = conn.execute(
                text(
                    "select policyname, cmd from pg_policies "
                    "where tablename = 'diary_goal_settings'"
                )
            ).all()
            assert [tuple(p) for p in policies] == [("diary_goal_settings_owner", "ALL")]
            for role, expected in (("anon", False), ("authenticated", True)):
                granted = conn.execute(
                    text("select has_table_privilege(:r, 'public.diary_goal_settings', 'SELECT')"),
                    {"r": role},
                ).scalar()
                assert granted is expected, role
            writes = conn.execute(
                text(
                    "select has_table_privilege('authenticated', 'public.diary_goal_settings', 'INSERT')"
                )
            ).scalar()
            assert writes is False
    finally:
        command.upgrade(migrated, "head")
        engine.dispose()


def _insert_product(conn, category: str) -> None:
    conn.execute(
        text(
            "insert into products (id, name, source, verification_status, category, per_100g, "
            "claims) values (gen_random_uuid(), 'Whey', 'label', 'verified', :c, '{}', '{}')"
        ),
        {"c": category},
    )


def test_supplement_category_downgrades_cleanly(migrated):
    """Plan 9 Task 7: `supplement` comes and goes with 0007; the downgrade maps supplement
    rows to `general` first, so the old check constraint holds."""
    from sqlalchemy.exc import IntegrityError

    engine = create_engine(_sync_url(migrated), poolclass=NullPool)
    try:
        with engine.begin() as conn:
            conn.execute(text("delete from products where name = 'Whey'"))
            _insert_product(conn, "supplement")
        command.downgrade(migrated, "0006_plan9_user_types")
        with engine.begin() as conn:
            cats = conn.execute(text("select category from products where name = 'Whey'"))
            assert [r[0] for r in cats] == ["general"]
        try:
            with engine.begin() as conn:
                _insert_product(conn, "supplement")
            raise AssertionError("the old constraint accepted 'supplement'")
        except IntegrityError:
            pass
        command.upgrade(migrated, "head")
        with engine.begin() as conn:
            _insert_product(conn, "supplement")
            n = conn.execute(
                text("select count(*) from products where category = 'supplement'")
            ).scalar()
            assert n == 1
            conn.execute(text("delete from products where name = 'Whey'"))
    finally:
        command.upgrade(migrated, "head")
        engine.dispose()


def test_tombstone_auth_deleted_column_downgrades_cleanly(migrated):
    """m2: tombstones record when the Supabase auth user was removed (nullable: unknown for
    rows written before 0005, so the retention job retries those)."""
    engine = create_engine(_sync_url(migrated), poolclass=NullPool)
    try:
        command.downgrade(migrated, "0004_plan8_deleted_accounts")
        with engine.connect() as conn:
            cols = {c["name"] for c in inspect(conn).get_columns("deleted_accounts")}
            assert "auth_deleted_at" not in cols
        command.upgrade(migrated, "head")
        with engine.connect() as conn:
            cols = {c["name"]: c for c in inspect(conn).get_columns("deleted_accounts")}
            assert cols["auth_deleted_at"]["nullable"] is True
            assert "TIMESTAMP" in str(cols["auth_deleted_at"]["type"]).upper()
    finally:
        command.upgrade(migrated, "head")
        engine.dispose()


def test_deleted_accounts_downgrades_cleanly(migrated):
    """D1/B1: the tombstone table comes and goes with 0004, with forced RLS and no user grant."""
    engine = create_engine(_sync_url(migrated), poolclass=NullPool)
    try:
        command.downgrade(migrated, "0003_plan6_meal_logs_off")
        with engine.connect() as conn:
            assert "deleted_accounts" not in inspect(conn).get_table_names()
        command.upgrade(migrated, "head")
        with engine.connect() as conn:
            row = conn.execute(
                text(
                    "select relrowsecurity, relforcerowsecurity from pg_class "
                    "where oid = 'public.deleted_accounts'::regclass"
                )
            ).one()
            assert tuple(row) == (True, True)
            for role in ("anon", "authenticated"):
                granted = conn.execute(
                    text("select has_table_privilege(:r, 'public.deleted_accounts', 'SELECT')"),
                    {"r": role},
                ).scalar()
                assert granted is False, role
    finally:
        command.upgrade(migrated, "head")
        engine.dispose()


def test_meal_logs_off_columns_downgrade_cleanly(migrated):
    engine = create_engine(_sync_url(migrated), poolclass=NullPool)
    new = {"off_barcode", "product_name", "grade"}
    try:
        command.downgrade(migrated, "0002_scans_path_unique")
        with engine.connect() as conn:
            cols = {c["name"]: c for c in inspect(conn).get_columns("meal_logs")}
            assert new.isdisjoint(cols) and cols["product_id"]["nullable"] is False
        command.upgrade(migrated, "head")
        with engine.connect() as conn:
            cols = {c["name"]: c for c in inspect(conn).get_columns("meal_logs")}
            assert new <= set(cols) and cols["product_id"]["nullable"] is True
    finally:
        command.upgrade(migrated, "head")
        engine.dispose()


def test_scans_path_index_downgrades_cleanly(migrated):
    engine = create_engine(_sync_url(migrated), poolclass=NullPool)
    try:
        command.downgrade(migrated, "0001_baseline")
        with engine.connect() as conn:
            names = {ix["name"] for ix in inspect(conn).get_indexes("scans")}
            assert "uq_scans_account_id_image_path" not in names
        command.upgrade(migrated, "head")
        with engine.connect() as conn:
            [ix] = [
                ix
                for ix in inspect(conn).get_indexes("scans")
                if ix["name"] == "uq_scans_account_id_image_path"
            ]
            assert ix["unique"] and ix["column_names"] == ["account_id", "image_path"]
            where = ix.get("dialect_options", {}).get("postgresql_where")
            assert where is not None and "image_path IS NOT NULL" in str(where)
    finally:
        command.upgrade(migrated, "head")
        engine.dispose()


def test_downgrade_then_upgrade_is_clean(migrated):
    engine = create_engine(_sync_url(migrated), poolclass=NullPool)
    try:
        command.downgrade(migrated, "base")
        with engine.connect() as conn:
            assert TABLES.isdisjoint(inspect(conn).get_table_names())
            # The Supabase shim is not dropped on downgrade.
            assert conn.execute(text("select to_regprocedure('auth.uid()') is not null")).scalar()
        command.upgrade(migrated, "head")
        with engine.connect() as conn:
            assert TABLES <= set(inspect(conn).get_table_names())
    finally:
        command.upgrade(migrated, "head")
        engine.dispose()


def test_models_match_migration(migrated):
    import app.features.consents.models
    import app.features.me.models
    import app.features.meals.models
    import app.features.members.models
    import app.features.products.models
    import app.features.ratelimit.models
    import app.features.reports.models
    import app.features.scans.models
    import app.features.targets.models  # noqa: F401
    from app.db.base import Base

    assert set(Base.metadata.tables) == TABLES
    engine = create_engine(_sync_url(migrated), poolclass=NullPool)
    try:
        with engine.connect() as conn:
            ctx = MigrationContext.configure(conn, opts={"compare_type": True})
            diff = [
                d
                for d in compare_metadata(ctx, Base.metadata)
                if not (
                    isinstance(d, tuple)
                    and d[0] == "remove_table"
                    and d[1].name == "alembic_version"
                )
            ]
        assert diff == []
    finally:
        engine.dispose()


def test_orm_class_names():
    from app.features.consents.models import Consent
    from app.features.me.models import Account, AccountUserTypes, DeletedAccount
    from app.features.meals.models import MealLog
    from app.features.members.models import Member
    from app.features.products.models import OffProductCache, Product
    from app.features.ratelimit.models import ExplanationCache, RateLimitCounter
    from app.features.reports.models import ProductReport
    from app.features.scans.models import Scan
    from app.features.targets.models import DiaryGoalSettings

    assert {
        c.__tablename__
        for c in (
            Account,
            AccountUserTypes,
            DeletedAccount,
            Member,
            Consent,
            Product,
            OffProductCache,
            Scan,
            MealLog,
            ProductReport,
            RateLimitCounter,
            ExplanationCache,
            DiaryGoalSettings,
        )
    } == TABLES


def test_host_allowlist():
    import pytest

    from tests.db.conftest import _assert_disposable

    for ok in (
        "postgresql+psycopg://u:p@127.0.0.1:5432/db",
        "postgresql+psycopg://u:p@localhost/db",
        "postgresql+psycopg://u:p@[::1]:5432/db",
        "postgresql+psycopg://u:p@postgres:5432/db",
    ):
        _assert_disposable(ok)
    for bad in (
        "postgresql+psycopg://u:p@db.abc.supabase.co:5432/postgres",
        "postgresql+psycopg://u:p@10.0.0.5:5432/postgres",
        "postgresql+psycopg://u:p@evil.example.com/localhost",
    ):
        with pytest.raises(RuntimeError):
            _assert_disposable(bad)
