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


def test_export_never_reads_process_settings(monkeypatch):
    """The export must not fall back to get_settings() (which reads apps/api/.env)."""

    def boom():
        raise AssertionError("export must not call get_settings()")

    monkeypatch.setattr("app.main.get_settings", boom)
    assert render_openapi() == COMMITTED.read_text()


ERROR_STATUSES = ("401", "404", "422", "429", "500")
ENVELOPE_REF = "#/components/schemas/ErrorEnvelope"


def _operations(spec: dict):
    for path, item in spec["paths"].items():
        for method, op in item.items():
            yield path, method, op


def test_bearer_security_scheme_replaces_authorization_header():
    spec = _spec()
    assert spec["components"]["securitySchemes"] == {
        "bearerAuth": {"type": "http", "scheme": "bearer"}
    }
    assert spec["paths"]["/v1/me"]["get"]["security"] == [{"bearerAuth": []}]
    for _, _, op in _operations(spec):
        params = [p["name"].lower() for p in op.get("parameters", [])]
        assert "authorization" not in params


def test_public_routes_have_no_security():
    assert "security" not in _spec()["paths"]["/v1/health"]["get"]


def test_error_envelope_schema():
    schemas = _spec()["components"]["schemas"]
    envelope = schemas["ErrorEnvelope"]
    assert envelope["required"] == ["error"]
    body = schemas[envelope["properties"]["error"]["$ref"].rsplit("/", 1)[1]]
    assert set(body["required"]) == {"code", "message_key", "details"}
    assert body["properties"]["code"]["type"] == "string"
    assert body["properties"]["message_key"]["type"] == "string"
    assert body["properties"]["details"]["type"] == "object"


def test_every_operation_documents_error_envelope():
    for path, method, op in _operations(_spec()):
        for status in ERROR_STATUSES:
            content = op["responses"][status]["content"]["application/json"]
            assert content["schema"] == {"$ref": ENVELOPE_REF}, (path, method, status)


def test_default_validation_error_schema_is_gone():
    spec = _spec()
    assert "HTTPValidationError" not in spec["components"]["schemas"]
    assert "ValidationError" not in spec["components"]["schemas"]
    assert "HTTPValidationError" not in json.dumps(spec)


def test_validation_error_is_documented_even_for_routes_with_params():
    """FastAPI's default 422 (HTTPValidationError) must not reappear on routes with params."""
    from fastapi import FastAPI

    app: FastAPI = create_app(Settings(environment="test", _env_file=None))

    @app.get("/v1/probe/{n}", operation_id="probe_get")
    async def _(n: int) -> dict:
        return {}

    spec = app.openapi()
    op = spec["paths"]["/v1/probe/{n}"]["get"]
    assert op["responses"]["422"]["content"]["application/json"]["schema"] == {"$ref": ENVELOPE_REF}
    assert "HTTPValidationError" not in json.dumps(spec)


def test_health_keeps_its_503_model():
    responses = _spec()["paths"]["/v1/health"]["get"]["responses"]
    assert responses["503"]["content"]["application/json"]["schema"] == {
        "$ref": "#/components/schemas/HealthOut"
    }
