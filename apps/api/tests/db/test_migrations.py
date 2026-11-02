from alembic.autogenerate import compare_metadata
from alembic.migration import MigrationContext
from sqlalchemy import create_engine, inspect, text
from sqlalchemy.pool import NullPool

from alembic import command
from tests.db.conftest import TABLES


def _sync_url(cfg) -> str:
    return cfg.get_main_option("sqlalchemy.url")


def test_head_is_baseline(migrated):
    engine = create_engine(_sync_url(migrated), poolclass=NullPool)
    with engine.connect() as conn:
        assert MigrationContext.configure(conn).get_current_revision() == "0001_baseline"
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
    from app.features.me.models import Account
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
