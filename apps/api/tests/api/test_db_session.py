from app.core.config import Settings
from app.db.session import build_engine


def test_engine_hides_sql_parameters():
    engine = build_engine(Settings(_env_file=None, environment="test"))
    assert engine.sync_engine.hide_parameters is True
