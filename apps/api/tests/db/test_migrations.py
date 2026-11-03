from alembic.autogenerate import compare_metadata
from alembic.migration import MigrationContext
from sqlalchemy import create_engine, inspect, text
from sqlalchemy.pool import NullPool

from alembic import command
from tests.db.conftest import TABLES


def _sync_url(cfg) -> str:
    return cfg.get_main_option("sqlalchemy.url")


def test_head_is_latest(migrated):
    engine = create_engine(_sync_url(migrated), poolclass=NullPool)
    with engine.connect() as conn:
        assert (
            MigrationContext.configure(conn).get_current_revision() == "0004_plan8_deleted_accounts"
        )
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
    import app.features.scans.models  # noqa: F401
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
    from app.features.me.models import Account, DeletedAccount
    from app.features.meals.models import MealLog
    from app.features.members.models import Member
    from app.features.products.models import OffProductCache, Product
    from app.features.ratelimit.models import ExplanationCache, RateLimitCounter
    from app.features.reports.models import ProductReport
    from app.features.scans.models import Scan

    assert {
        c.__tablename__
        for c in (
            Account,
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
