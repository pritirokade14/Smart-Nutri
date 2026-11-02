import httpx

from app.core.errors import ApiError


async def test_api_error_envelope(app, client):
    @app.get("/boom-api")
    async def _():
        raise ApiError("not_found", 404)

    r = await client.get("/boom-api")
    assert r.status_code == 404
    assert r.json() == {
        "error": {"code": "not_found", "message_key": "error.not_found", "details": {}}
    }


async def test_unhandled_exception_hides_text(app):
    @app.get("/boom")
    async def _():
        raise RuntimeError("secret db password in message")

    transport = httpx.ASGITransport(app=app, raise_app_exceptions=False)
    async with httpx.AsyncClient(transport=transport, base_url="http://t") as c:
        r = await c.get("/boom")
    assert r.status_code == 500 and r.json()["error"]["code"] == "internal_error"
    assert "secret" not in r.text


async def test_validation_error_envelope(app, client):
    @app.get("/v")
    async def _(n: int):
        return {}

    r = await client.get("/v?n=abc")
    assert r.status_code == 422 and r.json()["error"]["code"] == "validation_error"
    assert r.json()["error"]["details"]["fields"] == ["query.n"]


async def test_unknown_route_is_not_found_envelope(client):
    r = await client.get("/nope")
    assert r.status_code == 404 and r.json()["error"]["code"] == "not_found"


async def test_cors_allow_list(client):
    r = await client.options(
        "/anything",
        headers={"Origin": "https://evil.example", "Access-Control-Request-Method": "GET"},
    )
    assert "access-control-allow-origin" not in r.headers


async def test_http_exception_headers_preserved(app, client):
    @app.get("/only-get")
    async def _():
        return {}

    r = await client.post("/only-get")
    assert r.status_code == 405
    assert "GET" in r.headers["allow"]


async def test_500_carries_cors_headers(app):
    @app.get("/boom-cors")
    async def _():
        raise RuntimeError("secret")

    transport = httpx.ASGITransport(app=app, raise_app_exceptions=False)
    async with httpx.AsyncClient(transport=transport, base_url="http://t") as c:
        r = await c.get("/boom-cors", headers={"Origin": "http://localhost:3000"})
    assert r.status_code == 500
    assert r.json()["error"]["code"] == "internal_error"
    assert r.headers["access-control-allow-origin"] == "http://localhost:3000"
    assert "secret" not in r.text
