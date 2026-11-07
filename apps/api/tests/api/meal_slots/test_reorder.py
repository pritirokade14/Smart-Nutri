"""PUT /v1/meal-slots/order (Plan 11 Task 14)."""

from tests.api.meal_slots.helpers import URL, add, listing, log_quick


async def test_reorder_rewrites_positions(client, consented):
    await add(client, "Chai")
    ids = [i["id"] for i in await listing(client)]
    want = list(reversed(ids))
    r = await client.put(f"{URL}/order", json={"ids": want})
    assert r.status_code == 200
    assert [i["id"] for i in r.json()["items"]] == want
    assert [i["position"] for i in r.json()["items"]] == [0, 1, 2, 3, 4]
    assert [i["id"] for i in await listing(client)] == want


async def test_partial_list_refused(client, consented):
    ids = [i["id"] for i in await listing(client)]
    r = await client.put(f"{URL}/order", json={"ids": ids[:3]})
    assert r.status_code == 422
    assert r.json()["error"]["details"] == {"fields": ["body.ids"]}


async def test_duplicate_id_refused(client, consented):
    ids = [i["id"] for i in await listing(client)]
    r = await client.put(f"{URL}/order", json={"ids": [ids[0], *ids[:3]]})
    assert r.status_code == 422 and r.json()["error"]["code"] == "validation_error"


async def test_archived_id_refused(client, consented):
    row = (await add(client, "Chai")).json()
    await log_quick(client, row["id"])
    await client.delete(f"{URL}/{row['id']}")
    ids = [i["id"] for i in await listing(client)]
    r = await client.put(f"{URL}/order", json={"ids": [*ids, row["id"]]})
    assert r.status_code == 422 and r.json()["error"]["details"] == {"fields": ["body.ids"]}


async def test_unknown_id_404(client, consented):
    ids = [i["id"] for i in await listing(client)]
    r = await client.put(
        f"{URL}/order", json={"ids": [*ids[:3], "00000000-0000-0000-0000-000000000009"]}
    )
    assert r.status_code == 404 and r.json()["error"]["code"] == "meal_slot_not_found"
