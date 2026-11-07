"""PATCH /v1/meal-slots/{id} (Plan 11 Task 14)."""

from sqlalchemy import select

from app.features.meals.models import MealLog
from tests.api.meal_slots.helpers import URL, add, listing, log_quick


async def _lunch(client):
    return next(i for i in await listing(client) if i["label_key"] == "diary.slot.lunch")


async def test_rename_changes_label_not_entries(client, consented, db_session):
    lunch = await _lunch(client)
    await log_quick(client, lunch["id"])
    before = [
        (r.meal_slot_id, r.nutrients, r.eaten_at, r.local_date)
        for r in await db_session.scalars(select(MealLog))
    ]
    r = await client.patch(f"{URL}/{lunch['id']}", json={"custom_label": "Tiffin"})
    assert r.status_code == 200 and r.json()["custom_label"] == "Tiffin"
    assert r.json()["label_key"] == "diary.slot.lunch"
    db_session.expire_all()
    after = [
        (r.meal_slot_id, r.nutrients, r.eaten_at, r.local_date)
        for r in await db_session.scalars(select(MealLog))
    ]
    assert after == before


async def test_clear_restores_default_name(client, consented):
    lunch = await _lunch(client)
    await client.patch(f"{URL}/{lunch['id']}", json={"custom_label": "Tiffin"})
    r = await client.patch(f"{URL}/{lunch['id']}", json={"clear_custom_label": True})
    assert r.status_code == 200
    assert r.json()["custom_label"] is None and r.json()["label_key"] == "diary.slot.lunch"


async def test_clear_on_custom_slot_422(client, consented):
    row = (await add(client, "Chai")).json()
    r = await client.patch(f"{URL}/{row['id']}", json={"clear_custom_label": True})
    assert r.status_code == 422 and r.json()["error"]["code"] == "validation_error"


async def test_value_with_its_clear_flag_422(client, consented):
    lunch = await _lunch(client)
    r = await client.patch(
        f"{URL}/{lunch['id']}", json={"custom_label": "T", "clear_custom_label": True}
    )
    assert r.status_code == 422 and r.json()["error"]["code"] == "validation_error"
    r = await client.patch(
        f"{URL}/{lunch['id']}",
        json={"default_time_window": {"start": "12:00", "end": "13:00"}, "clear_time_window": True},
    )
    assert r.status_code == 422


async def test_null_fields_unchanged(client, consented):
    row = (await add(client, "Mine", default_time_window={"start": "10:00", "end": "11:00"})).json()
    r = await client.patch(
        f"{URL}/{row['id']}", json={"custom_label": "Chai", "default_time_window": None}
    )
    assert r.json()["custom_label"] == "Chai"
    assert r.json()["default_time_window"] == {"start": "10:00", "end": "11:00"}
    r = await client.patch(f"{URL}/{row['id']}", json={"clear_time_window": True})
    assert r.json()["default_time_window"] is None and r.json()["custom_label"] == "Chai"


async def test_rename_archived_422(client, consented):
    row = (await add(client, "Chai")).json()
    await log_quick(client, row["id"])
    await client.delete(f"{URL}/{row['id']}")
    r = await client.patch(f"{URL}/{row['id']}", json={"custom_label": "Tea"})
    assert r.status_code == 422 and r.json()["error"]["code"] == "meal_slot_archived"


async def test_rename_duplicate_422(client, consented):
    await add(client, "Chai")
    other = (await add(client, "Tea")).json()
    r = await client.patch(f"{URL}/{other['id']}", json={"custom_label": "CHAI"})
    assert r.status_code == 422 and r.json()["error"]["code"] == "meal_slot_label_duplicate"
    same = await client.patch(f"{URL}/{other['id']}", json={"custom_label": "tea"})
    assert same.status_code == 200  # its own name in another case is fine


async def test_rename_unknown_404(client, consented):
    r = await client.patch(
        f"{URL}/00000000-0000-0000-0000-000000000001", json={"custom_label": "x"}
    )
    assert r.status_code == 404 and r.json()["error"]["code"] == "meal_slot_not_found"
