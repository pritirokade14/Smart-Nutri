import json
import re
from pathlib import Path

from app.core.config import Settings
from app.main import create_app
from scripts.export_openapi import render_openapi

COMMITTED = Path(__file__).resolve().parents[4] / "packages" / "api-contract" / "openapi.json"


def _spec() -> dict:
    return create_app(Settings(environment="test", _env_file=None)).openapi()


def test_every_route_has_feature_operation_id():
    spec = _spec()
    ids = [op["operationId"] for p in spec["paths"].values() for op in p.values()]
    assert ids and len(ids) == len(set(ids))
    assert all(re.fullmatch(r"[a-z]+_[a-z_]+", i) for i in ids)
    assert {"health_get", "me_get"} <= set(ids)


def test_committed_openapi_matches_app():
    """Drift check: run `just contract` and commit if this fails."""
    assert COMMITTED.read_text() == render_openapi()
    assert json.loads(COMMITTED.read_text()) == _spec()
