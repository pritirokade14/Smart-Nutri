from uuid import UUID

import httpx
import pytest

from app.core.config import Settings
from app.core.security import AccountContext, current_account
from app.db.session import get_session
from app.integrations.openfoodfacts import get_off_client
from app.main import create_app
from tests.api.products.test_lookup_service import BARCODE, FakeOff

A = UUID("11111111-1111-1111-1111-111111111111")
BARCODE_URL = f"/v1/products/barcode/{BARCODE}"
PUBLIC_URL = f"/v1/products/{BARCODE}/public"


# Ingredients need a language tag, and a Nutri-Score grade needs the full nutrient set.
PAYLOAD = {
    "code": BARCODE,
    "product_name": "OFF Biscuit",
    "brands": "Acme",
    "ingredients_text": "wheat flour, sugar",
    "ingredients_lc": "en",
    "nutriments": {
        "energy-kcal_100g": 480,
        "sugars_100g": 15,
        "carbohydrates_100g": 70,
        "saturated-fat_100g": 4,
        "fat_100g": 20,
        "salt_100g": 0.5,
        "fiber_100g": 1,
        "proteins_100g": 6,
    },
}


@pytest.fixture
def fake_off():
    return FakeOff(PAYLOAD)


@pytest.fixture
def fake_off_empty():
    return FakeOff(None)


@pytest.fixture
def failing_off():
    return FakeOff(fail=True)


@pytest.fixture
def wire(app, db_session):
    def _wire(off, *, auth=True):
        app.dependency_overrides[get_session] = lambda: db_session
        app.dependency_overrides[get_off_client] = lambda: off
        if auth:
            app.dependency_overrides[current_account] = lambda: AccountContext(A, "a@example.com")

    return _wire


async def test_barcode_requires_auth(client):
    r = await client.get(BARCODE_URL)
    assert r.status_code == 401


async def test_barcode_found_from_off(client, wire, fake_off):
    wire(fake_off)
    r = await client.get(BARCODE_URL)
    assert r.status_code == 200
    body = r.json()
    assert body["source"] == "openfoodfacts" and body["attribution"] == "attribution.off"
    assert body["barcode"] == BARCODE and body["name"] == "OFF Biscuit"
    assert body["product_id"] is None
    assert body["per_100g"]["sugars_g"] == 15
    assert body["per_100g"]["sodium_mg"] is None
    assert body["ingredients"] == ["wheat flour", "sugar"]
    assert "cache-control" not in r.headers


async def test_barcode_invalid(client, wire, fake_off):
    wire(fake_off)
    r = await client.get("/v1/products/barcode/abc123")
    assert r.status_code == 422 and r.json()["error"]["code"] == "invalid_barcode"
    assert fake_off.calls == 0


async def test_barcode_not_found(client, wire, fake_off_empty):
    wire(fake_off_empty)
    r = await client.get(BARCODE_URL)
    assert r.status_code == 404 and r.json()["error"]["code"] == "product_not_found"


async def test_off_unavailable_is_503(client, wire, failing_off):
    wire(failing_off)
    r = await client.get(BARCODE_URL)
    assert r.status_code == 503 and r.json()["error"]["code"] == "off_unavailable"
    assert "down" not in r.text


async def test_second_request_is_a_cache_hit(client, wire, fake_off):
    wire(fake_off)
    assert (await client.get(BARCODE_URL)).status_code == 200
    assert (await client.get(BARCODE_URL)).status_code == 200
    assert fake_off.calls == 1


async def test_public_needs_no_auth_and_has_no_verdicts(client, wire, fake_off):
    wire(fake_off, auth=False)
    r = await client.get(PUBLIC_URL)
    assert r.status_code == 200
    assert r.headers["cache-control"] == "public, max-age=3600"
    assert "verdicts" not in r.text
    body = r.json()
    assert body["score_label"] == "calculated_by_smartnutri"
    assert body["product"]["attribution"] == "attribution.off"
    assert body["report"]["nutriscore"]["grade"] == "D"


@pytest.mark.parametrize("language", ["en", "hi", "mr"])
async def test_public_accepts_language(client, wire, fake_off, language):
    wire(fake_off, auth=False)
    r = await client.get(PUBLIC_URL, params={"language": language})
    assert r.status_code == 200


async def test_public_rejects_unknown_language(client, wire, fake_off):
    wire(fake_off, auth=False)
    r = await client.get(PUBLIC_URL, params={"language": "fr"})
    assert r.status_code == 422


async def test_public_errors_have_no_cache_header(client, wire, fake_off_empty):
    wire(fake_off_empty, auth=False)
    r = await client.get(PUBLIC_URL)
    assert r.status_code == 404 and "cache-control" not in r.headers
    r = await client.get("/v1/products/abc/public")
    assert r.status_code == 422 and "cache-control" not in r.headers


async def test_public_rate_limited(db_session, fake_off):
    app = create_app(Settings(_env_file=None, environment="test", rate_limit_public_per_minute=2))
    app.dependency_overrides[get_session] = lambda: db_session
    app.dependency_overrides[get_off_client] = lambda: fake_off
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://t") as c:
        assert (await c.get(PUBLIC_URL)).status_code == 200
        assert (await c.get(PUBLIC_URL)).status_code == 200
        r = await c.get(PUBLIC_URL)
    assert r.status_code == 429 and r.json()["error"]["code"] == "rate_limited"
    assert "cache-control" not in r.headers


async def test_off_client_dependency_works_without_lifespan():
    """ASGITransport does not run lifespan; get_off_client must still resolve (no 500)."""
    import httpx as _httpx

    from app.core.config import Settings
    from app.integrations.openfoodfacts import get_off_client
    from app.main import create_app

    app = create_app(Settings(_env_file=None, environment="test"))
    assert isinstance(app.state.off_http, _httpx.AsyncClient)

    class _Req:
        pass

    req = _Req()
    req.app = app
    client = get_off_client(req)
    assert client is not None
    await app.state.off_http.aclose()
