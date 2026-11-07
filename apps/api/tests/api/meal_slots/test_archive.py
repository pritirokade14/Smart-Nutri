"""DELETE /v1/meal-slots/{id} (Plan 11 Task 14)."""

from sqlalchemy import select

from app.features.meal_slots.models import MealSlot
from tests.api.meal_slots.helpers import URL, add, listing, log_quick

DAY = "/v1/diary/day"


async def test_archive_with_entries_keeps_them_on_their_day(client, consented):
    row = (await add(client, "Chai")).json()
    await log_quick(client, row["id"], name="cutting")
    r = await client.delete(f"{URL}/{row['id']}")
    assert r.status_code == 200 and r.json() == {"result": "archived"}
    day = (await client.get(DAY, params={"date": "2026-11-07"})).json()
    mine = [s for s in day["slots"] if s["slot_id"] == row["id"]]
    assert len(mine) == 1 and mine[0]["archived"] is True and len(mine[0]["entries"]) == 1
    assert row["id"] not in [i["id"] for i in await listing(client)]


async def test_delete_unused_removes_row(client, consented, db_session):
    row = (await add(client, "Chai")).json()
    r = await client.delete(f"{URL}/{row['id']}")
    assert r.json() == {"result": "deleted"}
    assert await db_session.scalar(select(MealSlot).where(MealSlot.id == row["id"])) is None


async def test_last_active_refused(client, consented):
    ids = [i["id"] for i in await listing(client)]
    for i in ids[:3]:
        assert (await client.delete(f"{URL}/{i}")).status_code == 200
    r = await client.delete(f"{URL}/{ids[3]}")
    assert r.status_code == 422 and r.json()["error"]["code"] == "meal_slot_last_active"


async def test_archive_twice_idempotent(client, consented):
    row = (await add(client, "Chai")).json()
    await log_quick(client, row["id"])
    assert (await client.delete(f"{URL}/{row['id']}")).json() == {"result": "archived"}
    assert (await client.delete(f"{URL}/{row['id']}")).json() == {"result": "archived"}


async def test_archived_not_suggested(client, consented, clock):
    clock.set("2026-11-07T05:30:00+00:00")  # 11:00 IST: lunch
    lunch = next(i for i in await listing(client) if i["label_key"] == "diary.slot.lunch")
    await log_quick(client, lunch["id"])
    await client.delete(f"{URL}/{lunch['id']}")
    j = (await client.get(URL)).json()
    assert j["suggested_slot_id"] != lunch["id"]
    assert j["suggested_slot_id"] in [i["id"] for i in j["items"]]


async def test_log_into_archived_refused(client, consented):
    row = (await add(client, "Chai")).json()
    await log_quick(client, row["id"])
    await client.delete(f"{URL}/{row['id']}")
    r = await client.post(
        "/v1/meals",
        json={"meal_slot_id": row["id"], "quick": {"energy_kcal": 50}, "local_date": "2026-11-07"},
    )
    assert r.status_code == 422 and r.json()["error"]["code"] == "meal_slot_archived"


async def test_foreign_slot_404(client, consented, db_session):
    r = await client.delete(f"{URL}/00000000-0000-0000-0000-000000000001")
    assert r.status_code == 404 and r.json()["error"]["code"] == "meal_slot_not_found"


async def test_unused_default_is_archived_not_resurrected(client, consented):
    ids = [i["id"] for i in await listing(client)]
    assert (await client.delete(f"{URL}/{ids[1]}")).json() == {"result": "archived"}
    assert ids[1] not in [i["id"] for i in await listing(client)]  # defaults not recreated
    assert len(await listing(client)) == 3
