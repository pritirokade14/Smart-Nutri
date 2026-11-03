"""Plan 8 Task 6: security pass (code side).

JWT edge cases (expired, wrong audience, alg none, HS256, forged) live in test_security.py and
the error envelope basics in test_errors.py. These tests are structural: they introspect every
route, so routes added later by other plans are checked too.
"""

import httpx
import pytest
from pydantic import ValidationError

from app.core.config import Settings
from app.core.security import current_account
from app.db.session import get_session
from app.features.me.dependencies import current_account_row
from app.integrations.openfoodfacts import get_off_client
from app.main import create_app
from tests.api.products.test_lookup_service import OFF_PAYLOAD, FakeOff
from tests.api.routes import api_routes

# Routes that are deliberately reachable without a user JWT.
PUBLIC = {
    ("GET", "/v1/health"),
    ("GET", "/v1/products/{barcode}/public"),
    ("GET", "/v1/methodology"),  # Plan 7
    ("POST", "/v1/auth/hooks/send-sms"),  # Standard Webhooks signature instead
}
# Public routes that must carry an IP rate limit (the hook is signed; health is a probe).
PUBLIC_LIMITED = {("GET", "/v1/products/{barcode}/public"), ("GET", "/v1/methodology")}
# Writes that may use current_account instead of current_account_row.
WRITES_WITHOUT_ACCOUNT_ROW = {
    ("DELETE", "/v1/me"),  # must not re-create the row it deletes
    ("POST", "/v1/auth/hooks/send-sms"),
}
# Routes that cost money (CallMissed), call third parties, or write shared data.
EXPENSIVE = {
    ("POST", "/v1/scans/label"),
    ("POST", "/v1/scans/upload-url"),
    ("POST", "/v1/analyze"),
    ("POST", "/v1/products"),
    ("GET", "/v1/products/barcode/{code}"),  # Open Food Facts lookups
    ("POST", "/v1/voice/ask"),  # Plan 7
    ("POST", "/v1/products/{product_id}/reports"),  # Plan 7
}
ALWAYS_PRESENT = {
    ("POST", "/v1/scans/label"),
    ("POST", "/v1/analyze"),
    ("GET", "/v1/products/{barcode}/public"),
}
_DOCS = {"/openapi.json", "/docs", "/docs/oauth2-redirect", "/redoc"}


def _routes(app):
    for route in api_routes(app):
        for method in route.methods - {"HEAD", "OPTIONS"}:
            yield method, route


def _is_rate_limited(route) -> bool:
    return any(getattr(c, "__qualname__", "").startswith("limit.<locals>.") for c in route.calls())


def test_every_route_requires_auth_unless_public(app):
    seen = set()
    for method, route in _routes(app):
        key = (method, route.path)
        seen.add(key)
        if key in PUBLIC:
            assert current_account not in route.calls(), f"{key} is public but asks for a JWT"
        else:
            assert current_account in route.calls(), f"{key} has no current_account"
    assert ALWAYS_PRESENT <= seen


def test_every_write_ensures_the_account_row(app):
    for method, route in _routes(app):
        key = (method, route.path)
        if method == "GET" or key in PUBLIC - WRITES_WITHOUT_ACCOUNT_ROW:
            continue
        if key in WRITES_WITHOUT_ACCOUNT_ROW:
            continue
        assert current_account_row in route.calls(), f"{key} writes without current_account_row"


def test_every_expensive_route_has_a_rate_limit(app):
    present = {(m, r.path): r for m, r in _routes(app)}
    for key in (EXPENSIVE | PUBLIC_LIMITED) & present.keys():
        assert _is_rate_limited(present[key]), f"{key} has no limit(...) dependency"


def test_rate_limit_runs_before_the_route_body(app):
    """limit() commits the session; it must be a route dependency, never called mid-route
    with staged writes (consume() guards that case)."""
    for method, route in _routes(app):
        if (method, route.path) in EXPENSIVE and _is_rate_limited(route):
            top = route.top_level_calls()
            limits = [i for i, c in enumerate(top) if "limit.<locals>" in c.__qualname__]
            assert limits and limits[0] <= 1, (method, route.path)  # after the consent gate


async def test_cors_rejects_unknown_origin(client):
    for method in ("GET", "POST", "DELETE"):
        r = await client.options(
            "/v1/me",
            headers={"Origin": "https://evil.example", "Access-Control-Request-Method": method},
        )
        assert "access-control-allow-origin" not in r.headers
    r = await client.get("/v1/health", headers={"Origin": "https://evil.example"})
    assert "access-control-allow-origin" not in r.headers


def test_prod_rejects_plain_http_or_empty_origins():
    with pytest.raises(ValidationError):
        Settings(_env_file=None, environment="prod", allowed_origins=["http://app.example"])
    with pytest.raises(ValidationError):
        Settings(_env_file=None, environment="prod", allowed_origins="*")
    ok = Settings(_env_file=None, environment="prod", allowed_origins="https://app.example")
    assert ok.allowed_origins == ["https://app.example"]
    # Local web dev keeps working outside prod.
    Settings(_env_file=None, environment="dev", allowed_origins=["http://localhost:3000"])


async def test_error_body_has_no_exception_text(app):
    @app.get("/boom-sec")
    async def _():
        raise ValueError("password=hunter2 for user asha@example.com")

    transport = httpx.ASGITransport(app=app, raise_app_exceptions=False)
    async with httpx.AsyncClient(transport=transport, base_url="http://t") as c:
        r = await c.get("/boom-sec")
    assert r.status_code == 500
    assert r.json() == {
        "error": {"code": "internal_error", "message_key": "error.internal_error", "details": {}}
    }


async def test_security_headers_on_api_responses(client):
    for path in ("/v1/health", "/v1/me", "/nope"):
        r = await client.get(path)
        assert r.headers["x-content-type-options"] == "nosniff", path
        assert r.headers["x-frame-options"] == "DENY", path
        assert r.headers["referrer-policy"] == "no-referrer", path
        assert "frame-ancestors 'none'" in r.headers["content-security-policy"], path
        assert r.headers["cache-control"] == "no-store", path
        assert "strict-transport-security" not in r.headers  # only in prod


async def test_public_cache_header_is_kept_and_hsts_in_prod(db_session):
    app = create_app(
        Settings(
            _env_file=None,
            environment="prod",
            allowed_origins=["https://app.example"],
        )
    )
    app.dependency_overrides[get_session] = lambda: db_session
    app.dependency_overrides[get_off_client] = lambda: FakeOff(OFF_PAYLOAD)
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://t") as c:
        r = await c.get(f"/v1/products/{OFF_PAYLOAD['code']}/public")
        assert r.status_code == 200
        assert r.headers["cache-control"] == "public, max-age=3600"
        assert r.headers["strict-transport-security"].startswith("max-age=31536000")
        # No interactive docs in prod (the contract is exported by script, not served).
        assert (await c.get("/docs")).status_code == 404
        assert (await c.get("/openapi.json")).status_code == 404


_BANNED_KEYS = {
    "member",
    "members",
    "member_id",
    "member_name",
    "verdict",
    "verdicts",
    "allergen_state",
    "account_id",
    "created_by",
    "email",
}


def _keys(node, path=()):
    if isinstance(node, dict):
        for k, v in node.items():
            yield (*path, k)
            yield from _keys(v, (*path, k))
    elif isinstance(node, list):
        for item in node:
            yield from _keys(item, path)


async def test_public_endpoints_expose_no_member_fields(app, client, db_session):
    app.dependency_overrides[get_session] = lambda: db_session
    app.dependency_overrides[get_off_client] = lambda: FakeOff(OFF_PAYLOAD)
    bodies = [(await client.get(f"/v1/products/{OFF_PAYLOAD['code']}/public")).json()]
    if any(r.path == "/v1/methodology" for r in api_routes(app)):
        bodies.append((await client.get("/v1/methodology")).json())
    for body in bodies:
        for path in _keys(body):
            assert path[-1] not in _BANNED_KEYS, path
            if path[-1] == "name":
                assert path == ("product", "name"), path


def test_no_route_outside_docs_is_unlisted(app):
    """Every route is either in the contract or deliberately hidden (the signed hook)."""
    documented = set(app.openapi()["paths"])
    for method, route in _routes(app):
        if route.path in _DOCS or (method, route.path) == ("POST", "/v1/auth/hooks/send-sms"):
            continue
        assert route.path in documented, (method, route.path)
