"""custom_foods_list (Plan 12 Task 11): newest change first, an opaque stable cursor."""

import pytest
from sqlalchemy import text

from tests.api.custom_foods.conftest import bar

URL = "/v1/custom-foods"


async def _make(client, n: int) -> list[str]:
    ids = []
    for i in range(n):
        r = await client.post(URL, json=bar(name=f"Food {i}"))
        assert r.status_code == 201
        ids.append(r.json()["id"])
    return ids


async def test_cursor_stable(client, consented, db_session):
    ids = await _make(client, 5)
    # Two rows share one timestamp: the id breaks the tie, no row is skipped or repeated.
    await db_session.execute(text("update custom_foods set updated_at = '2026-11-07T00:00:00Z'"))
    await db_session.flush()
    seen: list[str] = []
    cursor = None
    pages = 0
    while True:
        params = {"limit": 2} | ({"cursor": cursor} if cursor else {})
        r = await client.get(URL, params=params)
        assert r.status_code == 200, r.text
        body = r.json()
        seen += [i["id"] for i in body["items"]]
        pages += 1
        cursor = body["next_cursor"]
        if cursor is None:
            break
    assert pages == 3 and sorted(seen) == sorted(ids) and len(set(seen)) == 5
    assert seen == sorted(ids, reverse=True)  # same timestamp: id descending


async def test_newest_change_first(client, consented, clock):
    ids = await _make(client, 3)
    clock.set("2026-11-07T07:00:00+00:00")  # later than the creates
    r = await client.put(f"{URL}/{ids[0]}", json=bar(name="Edited"))
    assert r.status_code == 200, r.text
    items = (await client.get(URL)).json()["items"]
    names = [i["name"] for i in items]
    assert names[0] == "Edited" and len(names) == 3


@pytest.mark.parametrize("limit", [0, 101, -1])
async def test_limit_bounds(client, consented, limit):
    r = await client.get(URL, params={"limit": limit})
    assert r.status_code == 422 and r.json()["error"]["code"] == "validation_error"
    assert (await client.get(URL, params={"limit": 100})).status_code == 200
    assert (await client.get(URL, params={"limit": 1})).status_code == 200


async def test_bad_cursor_422(client, consented):
    r = await client.get(URL, params={"cursor": "not-a-cursor"})
    assert r.status_code == 422 and r.json()["error"]["code"] == "validation_error"
