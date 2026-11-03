"""SupabaseStorage.list_prefix / delete_paths (Plan 8 Tasks 2-3) over httpx.MockTransport."""

import json
import logging
from datetime import UTC, datetime

import httpx
import pytest
from pydantic import SecretStr

from app.integrations.storage import StorageUnavailable, SupabaseStorage, _UnconfiguredStorage

URL = "https://proj.supabase.co"
KEY = "sb_secret_test_value"
LIST_URL = f"{URL}/storage/v1/object/list/label-photos"
A = "11111111-1111-1111-1111-111111111111"


def make(handler) -> tuple[SupabaseStorage, list[httpx.Request]]:
    seen: list[httpx.Request] = []

    def _h(request: httpx.Request) -> httpx.Response:
        seen.append(request)
        return handler(request)

    http = httpx.AsyncClient(transport=httpx.MockTransport(_h))
    return SupabaseStorage(http, url=URL, secret_key=SecretStr(KEY), bucket="label-photos"), seen


def _file(name: str, created: str = "2026-10-01T00:00:00.000Z") -> dict:
    return {"name": name, "id": f"id-{name}", "created_at": created, "metadata": {"size": 1}}


def _folder(name: str) -> dict:
    return {"name": name, "id": None, "created_at": None, "metadata": None}


def tree(listing: dict[str, list[dict]]):
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.method == "POST" and str(request.url) == LIST_URL
        body = json.loads(request.content)
        items = listing.get(body["prefix"], [])
        start = body["offset"]
        return httpx.Response(200, json=items[start : start + body["limit"]])

    return handler


async def test_list_prefix_recurses_into_folders():
    storage, seen = make(
        tree(
            {
                "voice": [_folder(A)],
                f"voice/{A}": [_file("a.mp3"), _file("b.mp3")],
            }
        )
    )
    assert await storage.list_prefix("voice") == [f"voice/{A}/a.mp3", f"voice/{A}/b.mp3"]
    assert seen[0].headers["authorization"] == f"Bearer {KEY}"
    assert seen[0].headers["apikey"] == KEY


async def test_list_prefix_of_the_whole_bucket():
    storage, _ = make(tree({"": [_folder(A)], A: [_file("x.jpg")]}))
    assert await storage.list_prefix("") == [f"{A}/x.jpg"]


async def test_list_prefix_filters_by_age():
    storage, _ = make(
        tree(
            {
                A: [
                    _file("old.jpg", "2026-09-01T00:00:00Z"),
                    _file("new.jpg", "2026-11-02T23:59:59.999+00:00"),
                    {"name": "nodate.jpg", "id": "n", "created_at": None, "metadata": {}},
                ]
            }
        )
    )
    cutoff = datetime(2026, 10, 4, tzinfo=UTC)
    # An object without a timestamp is never treated as old (retention skips it).
    assert await storage.list_prefix(A, older_than=cutoff) == [f"{A}/old.jpg"]
    assert len(await storage.list_prefix(A)) == 3


async def test_list_prefix_pages_through_large_folders():
    files = [_file(f"{i:04}.jpg") for i in range(2500)]
    storage, seen = make(tree({A: files}))
    assert len(await storage.list_prefix(A)) == 2500
    assert [json.loads(r.content)["offset"] for r in seen] == [0, 1000, 2000]


async def test_list_prefix_strips_slashes():
    storage, seen = make(tree({}))
    assert await storage.list_prefix(f"/{A}/") == []
    assert json.loads(seen[0].content)["prefix"] == A


async def test_list_failure_raises_unavailable_without_body(caplog):
    storage, _ = make(lambda r: httpx.Response(500, text=f"boom {KEY}"))
    with caplog.at_level(logging.DEBUG), pytest.raises(StorageUnavailable):
        await storage.list_prefix(A)
    assert KEY not in caplog.text and "boom" not in caplog.text


async def test_delete_paths_batches_and_sends_prefixes():
    storage, seen = make(lambda r: httpx.Response(200, json=[]))
    paths = [f"{A}/{i}.jpg" for i in range(1500)]
    await storage.delete_paths(paths)
    assert [r.method for r in seen] == ["DELETE", "DELETE"]
    assert str(seen[0].url) == f"{URL}/storage/v1/object/label-photos"
    assert json.loads(seen[0].content)["prefixes"] == paths[:1000]
    assert json.loads(seen[1].content)["prefixes"] == paths[1000:]


async def test_delete_paths_empty_makes_no_call():
    storage, seen = make(lambda r: httpx.Response(200, json=[]))
    await storage.delete_paths([])
    assert seen == []


async def test_delete_failure_raises_unavailable():
    storage, _ = make(lambda r: httpx.Response(503))
    with pytest.raises(StorageUnavailable):
        await storage.delete_paths([f"{A}/x.jpg"])


async def test_network_error_raises_unavailable():
    def boom(request):
        raise httpx.ConnectError("down")

    storage, _ = make(boom)
    with pytest.raises(StorageUnavailable):
        await storage.list_prefix(A)
    with pytest.raises(StorageUnavailable):
        await storage.delete_paths([f"{A}/x.jpg"])


async def test_unconfigured_storage_refuses():
    with pytest.raises(StorageUnavailable):
        await _UnconfiguredStorage().list_prefix(A)
    with pytest.raises(StorageUnavailable):
        await _UnconfiguredStorage().delete_paths([A])
