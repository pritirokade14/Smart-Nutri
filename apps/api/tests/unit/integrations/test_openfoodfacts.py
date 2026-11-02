import json
from pathlib import Path

import httpx
import pytest

from app.integrations.openfoodfacts import (
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
    ],
)
def test_normalize_barcode_accepts(raw, clean):
    assert normalize_barcode(raw) == clean


@pytest.mark.parametrize("raw", ["abc123", "1234567", "123456789012345", ""])
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
    assert seen["fields"] == (
        "code,product_name,brands,image_front_url,categories_tags,nutriments,"
        "serving_quantity,ingredients_text,allergens_tags,traces_tags,labels_tags"
    )


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
