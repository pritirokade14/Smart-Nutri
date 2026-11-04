import json
from pathlib import Path

import httpx
import pytest

from app.integrations.openfoodfacts import (
    DEFAULT_USER_AGENT,
    PRODUCT_FIELDS,
    InvalidBarcode,
    OffClient,
    OffUnavailable,
    normalize_barcode,
)

FIXTURES = Path(__file__).resolve().parents[2] / "fixtures" / "off"
UA = "SmartNutri/0.1 (contact: t@example.com)"


def _load(name: str) -> dict:
    return json.loads((FIXTURES / name).read_text())


def _client(handler) -> OffClient:
    http = httpx.AsyncClient(transport=httpx.MockTransport(handler))
    return OffClient(http, base_url="https://x", user_agent=UA)


@pytest.mark.parametrize(
    "raw,clean",
    [
        (" 8901 0632 0108 9 ", "8901063201089"),
        ("036000291452", "036000291452"),
        ("12345670", "12345670"),
        ("8901-0632-0108-9", "8901063201089"),
        ("00012345678905", "00012345678905"),
    ],
)
def test_normalize_barcode_accepts(raw, clean):
    assert normalize_barcode(raw) == clean


@pytest.mark.parametrize(
    "raw", ["abc123", "1234567", "123456789", "1234567890", "12345678901", "123456789012345", ""]
)
def test_normalize_barcode_rejects(raw):
    with pytest.raises(InvalidBarcode):
        normalize_barcode(raw)


async def test_sends_user_agent_v3_path_and_fields():
    seen = {}

    def handler(req):
        seen["ua"] = req.headers["user-agent"]
        seen["path"] = req.url.path
        seen["fields"] = req.url.params["fields"]
        return httpx.Response(200, json=_load("client_found.json"))

    product = await _client(handler).get_product("8901063201089")
    assert product is not None and product["code"] == "8901063201089"
    assert seen["ua"] == UA
    assert seen["path"] == "/api/v3/product/8901063201089"
    assert set(seen["fields"].split(",")) == set(PRODUCT_FIELDS.split(","))


def test_fields_cover_everything_the_mapper_reads():
    import re

    src = (Path(__file__).resolve().parents[3] / "app/features/products/off_mapping.py").read_text()
    read = set(re.findall(r'(?:product|p|payload)\.get\("([a-z_]+)"', src))
    read -= {"product"}  # the v3 envelope key, not a product field
    missing = read - set(PRODUCT_FIELDS.split(","))
    assert not missing, f"OFF fields read by the mapper but not requested: {sorted(missing)}"


@pytest.mark.parametrize("ua", ["", "   ", "SmartNutri/0.1 (contact: your-team-email@example.com)"])
async def test_blank_or_placeholder_user_agent_falls_back(ua):
    seen = {}

    def handler(req):
        seen["ua"] = req.headers["user-agent"]
        return httpx.Response(200, json=_load("client_found.json"))

    client = OffClient(
        httpx.AsyncClient(transport=httpx.MockTransport(handler)),
        base_url="https://off.test",
        user_agent=ua,
    )
    await client.get_product("8901063201089")
    assert seen["ua"] == DEFAULT_USER_AGENT


async def test_404_with_non_json_body_is_not_found():
    def handler(req):
        return httpx.Response(404, content=b"<html>nope</html>")

    assert await _client(handler).get_product("8901063201089") is None


async def test_429_raises_unavailable():
    def handler(req):
        return httpx.Response(429, json={"status": "failure"})

    with pytest.raises(OffUnavailable):
        await _client(handler).get_product("8901063201089")


async def test_get_product_rejects_unnormalised_input():
    with pytest.raises(InvalidBarcode):
        await _client(lambda req: httpx.Response(200)).get_product("../../admin")


async def test_not_found_returns_none():
    def handler(req):
        return httpx.Response(404, json=_load("client_not_found.json"))

    assert await _client(handler).get_product("0000000000000") is None


async def test_failure_status_with_200_and_not_found_returns_none():
    def handler(req):
        return httpx.Response(200, json=_load("client_not_found.json"))

    assert await _client(handler).get_product("0000000000000") is None


async def test_server_error_raises_unavailable():
    with pytest.raises(OffUnavailable):
        await _client(lambda req: httpx.Response(503)).get_product("8901063201089")


async def test_timeout_raises_unavailable():
    def handler(req):
        raise httpx.ReadTimeout("slow", request=req)

    with pytest.raises(OffUnavailable):
        await _client(handler).get_product("8901063201089")


async def test_network_error_raises_unavailable():
    def handler(req):
        raise httpx.ConnectError("down", request=req)

    with pytest.raises(OffUnavailable):
        await _client(handler).get_product("8901063201089")


@pytest.mark.parametrize(
    "response",
    [
        httpx.Response(200, content=b"<html>not json</html>"),
        httpx.Response(200, json=["a list"]),
        httpx.Response(200, json={"status": "success"}),
        httpx.Response(200, json={"status": "success", "product": "x"}),
        httpx.Response(200, json={"status": "failure", "result": {"id": "other"}}),
    ],
)
async def test_malformed_body_raises_unavailable(response):
    with pytest.raises(OffUnavailable):
        await _client(lambda req: response).get_product("8901063201089")


# --- search (Plan 6 T5/T6) ----------------------------------------------------------------


async def test_search_by_category_sends_ua_tag_and_fields():
    seen = {}

    def handler(req):
        seen.update(ua=req.headers["user-agent"], path=req.url.path, params=dict(req.url.params))
        return httpx.Response(200, json={"count": 1, "products": [{"code": "1"}, "bad"]})

    products = await _client(handler).search_by_category("en:namkeen", page_size=10)
    assert products == [{"code": "1"}]  # non-objects dropped
    assert seen["ua"] == UA and seen["path"] == "/api/v2/search"
    assert seen["params"]["categories_tags"] == "en:namkeen"
    assert seen["params"]["page_size"] == "10"
    assert seen["params"]["fields"] == PRODUCT_FIELDS


async def test_search_text_uses_search_terms():
    seen = {}

    def handler(req):
        seen.update(path=req.url.path, params=dict(req.url.params))
        return httpx.Response(200, json={"products": [{"code": "2"}]})

    assert await _client(handler).search_text("marie biscuit", page_size=5) == [{"code": "2"}]
    assert seen["path"] == "/cgi/search.pl"
    assert seen["params"]["search_terms"] == "marie biscuit"
    assert seen["params"]["json"] == "1" and seen["params"]["page_size"] == "5"


@pytest.mark.parametrize(
    "response",
    [
        httpx.Response(503),
        httpx.Response(200, content=b"<html>"),
        httpx.Response(200, json={"products": "x"}),
        httpx.Response(404, json={}),
    ],
)
async def test_search_failures_raise_unavailable(response):
    with pytest.raises(OffUnavailable):
        await _client(lambda req: response).search_by_category("en:x")
    with pytest.raises(OffUnavailable):
        await _client(lambda req: response).search_text("abc")


async def test_search_network_error_raises_unavailable():
    def handler(req):
        raise httpx.ConnectError("down", request=req)

    with pytest.raises(OffUnavailable):
        await _client(handler).search_by_category("en:x")
