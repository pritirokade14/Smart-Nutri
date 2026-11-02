from app.core.config import Settings
from app.db.session import build_engine


def test_engine_hides_sql_parameters():
    engine = build_engine(Settings(_env_file=None, environment="test"))
    assert engine.sync_engine.hide_parameters is True


def test_pool_fits_the_session_pooler_budget():
    """3 Cloud Run instances x (pool + overflow) must stay <= 15 connections."""
    engine = build_engine(Settings(_env_file=None, environment="test"))
    pool = engine.sync_engine.pool
    assert pool.size() == 3 and pool._max_overflow == 2
    assert 3 * (pool.size() + pool._max_overflow) <= 15
