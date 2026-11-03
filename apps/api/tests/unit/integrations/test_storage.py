"""SupabaseStorage over httpx.MockTransport: never calls real Supabase."""

import json

import httpx
import pytest
from pydantic import SecretStr

from app.core.config import Settings
from app.integrations.storage import (
    StorageNotFound,
    StorageUnavailable,
    SupabaseStorage,
    get_storage,
)

URL = "https://proj.supabase.co"
KEY = "sb_secret_test_value"
PATH = "11111111-1111-1111-1111-111111111111/5b0a5e8e-8a5e-4d0e-9a39-0f9a2f6b8c11.jpg"


def make(handler, **kw) -> tuple[SupabaseStorage, list[httpx.Request]]:
    seen: list[httpx.Request] = []

    def _h(request: httpx.Request) -> httpx.Response:
        seen.append(request)
        return handler(request)

    http = httpx.AsyncClient(transport=httpx.MockTransport(_h))
    return SupabaseStorage(
        http, url=URL, secret_key=SecretStr(KEY), bucket="label-photos", **kw
    ), seen


async def test_signed_upload_request_and_absolute_url():
    storage, seen = make(
        lambda r: httpx.Response(
            200, json={"url": f"/object/upload/sign/label-photos/{PATH}?token=abc", "token": "abc"}
        )
    )
    url = await storage.create_signed_upload(PATH, 600)
    assert url == f"{URL}/storage/v1/object/upload/sign/label-photos/{PATH}?token=abc"
    [req] = seen
    assert req.method == "POST"
    assert str(req.url) == f"{URL}/storage/v1/object/upload/sign/label-photos/{PATH}"
    assert req.headers["authorization"] == f"Bearer {KEY}"
    assert req.headers["apikey"] == KEY
    assert req.headers.get("x-upsert") != "true"  # never overwrite an existing photo
    assert json.loads(req.content or b"{}") is not None


async def test_download_returns_bytes():
    storage, seen = make(lambda r: httpx.Response(200, content=b"\xff\xd8\xffdata"))
    assert await storage.download(PATH) == b"\xff\xd8\xffdata"
    [req] = seen
    assert req.method == "GET"
    assert str(req.url) == f"{URL}/storage/v1/object/authenticated/label-photos/{PATH}"
    assert req.headers["authorization"] == f"Bearer {KEY}"


async def test_download_returns_at_most_cap_plus_one():
    storage, _ = make(lambda r: httpx.Response(200, content=b"x" * 5000), max_download_bytes=1000)
    assert len(await storage.download(PATH)) == 1001  # enough to know it is too large


async def test_download_stops_streaming_past_the_cap():
    pulled: list[int] = []

    async def body():
        for i in range(50):
            pulled.append(i)
            yield b"x" * 100

    storage, _ = make(lambda r: httpx.Response(200, content=body()), max_download_bytes=1000)
    assert len(await storage.download(PATH)) == 1001
    assert len(pulled) < 50  # the rest of a huge body is never read


@pytest.mark.parametrize(
    "response",
    [
        httpx.Response(404, json={"statusCode": "404", "error": "not_found"}),
        httpx.Response(400, json={"statusCode": "404", "error": "not_found", "message": "x"}),
        httpx.Response(400, json={"statusCode": "404", "error": "Object not found"}),
    ],
)
async def test_download_not_found(response):
    storage, _ = make(lambda r: response)
    with pytest.raises(StorageNotFound):
        await storage.download(PATH)


@pytest.mark.parametrize("status", [400, 401, 403, 500, 503])
async def test_other_errors_unavailable(status):
    storage, _ = make(lambda r: httpx.Response(status, json={"error": "boom"}))
    with pytest.raises(StorageUnavailable):
        await storage.download(PATH)
    with pytest.raises(StorageUnavailable):
        await storage.create_signed_upload(PATH, 600)


async def test_network_error_unavailable():
    def _boom(request):
        raise httpx.ConnectError("down")

    storage, _ = make(_boom)
    with pytest.raises(StorageUnavailable):
        await storage.download(PATH)
    with pytest.raises(StorageUnavailable):
        await storage.create_signed_upload(PATH, 600)


async def test_malformed_sign_response_unavailable():
    storage, _ = make(lambda r: httpx.Response(200, json={"nope": 1}))
    with pytest.raises(StorageUnavailable):
        await storage.create_signed_upload(PATH, 600)


def test_secret_not_in_repr():
    storage, _ = make(lambda r: httpx.Response(200))
    assert KEY not in repr(storage)


async def test_unconfigured_storage_is_unavailable():
    settings = Settings(_env_file=None, supabase_url="", supabase_secret_key=None)
    gen = get_storage(settings)
    storage = await anext(gen)
    with pytest.raises(StorageUnavailable):
        await storage.create_signed_upload(PATH, 600)
    with pytest.raises(StorageUnavailable):
        await storage.download(PATH)
    await gen.aclose()
