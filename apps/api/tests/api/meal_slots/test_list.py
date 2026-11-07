from sqlalchemy import select

from app.features.meal_slots.models import MealSlot
from tests.api.meal_slots.conftest import ACC_A, ACC_B, URL


async def test_defaults_created_once(client, terms_only, db_session):
    for _ in range(2):
        r = await client.get(URL)
        assert r.status_code == 200, r.text
    items = r.json()["items"]
    assert [i["position"] for i in items] == [0, 1, 2, 3]
    assert [i["label_key"] for i in items] == [
        "diary.slot.breakfast",
        "diary.slot.lunch",
        "diary.slot.snack",
        "diary.slot.dinner",
    ]
    assert all(i["is_default"] and i["custom_label"] is None and not i["archived"] for i in items)
    assert items[3]["default_time_window"] == {"start": "19:00", "end": "03:59"}
    rows = list(await db_session.scalars(select(MealSlot)))
    assert len(rows) == 4


async def test_suggested_slot_from_local_time(client, terms_only, clock):
    clock.set("2026-11-07T05:29:00+00:00")  # 10:59 IST
    r = (await client.get(URL)).json()
    by_id = {i["id"]: i["label_key"] for i in r["items"]}
    assert by_id[r["suggested_slot_id"]] == "diary.slot.breakfast"
    clock.set("2026-11-07T05:30:00+00:00")  # 11:00 IST
    r = (await client.get(URL)).json()
    assert by_id[r["suggested_slot_id"]] == "diary.slot.lunch"


async def test_suggested_slot_in_new_york(client, terms_only, clock):
    assert (
        await client.put("/v1/me/timezone", json={"timezone": "America/New_York"})
    ).status_code == 200
    clock.set("2026-11-07T13:00:00+00:00")  # 08:00 EST; 18:30 IST would be dinner
    r = (await client.get(URL)).json()
    by_id = {i["id"]: i["label_key"] for i in r["items"]}
    assert by_id[r["suggested_slot_id"]] == "diary.slot.breakfast"


async def test_archived_hidden_unless_requested(client, terms_only, db_session):
    first = (await client.get(URL)).json()["items"]
    row = await db_session.get(MealSlot, first[1]["id"])
    from datetime import UTC, datetime

    row.archived_at = datetime.now(UTC)
    await db_session.flush()
    assert len((await client.get(URL)).json()["items"]) == 3
    r = await client.get(URL, params={"include_archived": "true"})
    items = r.json()["items"]
    assert len(items) == 4
    assert [i["archived"] for i in items] == [False, True, False, False]


async def test_foreign_member_404(client, terms_only, add_member):
    foreign = await add_member(ACC_B)
    r = await client.get(URL, params={"member_id": str(foreign.id)})
    assert r.status_code == 404
    assert r.json()["error"]["code"] == "member_not_found"


async def test_non_primary_422_until_flag_on(client, app, terms_only, add_member, monkeypatch):
    other = await add_member(ACC_A, name="Dad")
    r = await client.get(URL, params={"member_id": str(other.id)})
    assert r.status_code == 422
    assert r.json()["error"]["code"] == "diary_member_not_enabled"
    monkeypatch.setattr(app.state.settings, "diary_family_enabled", True)
    r = await client.get(URL, params={"member_id": str(other.id)})
    assert r.status_code == 200
    assert len(r.json()["items"]) == 4


async def test_meal_slots_need_only_terms(client, login, grant):
    await grant(ACC_A, ("terms",))
    login(ACC_A)
    assert (await client.get(URL)).status_code == 200
    await grant(ACC_B, ("health_data", "ai_processing"))
    login(ACC_B)
    r = await client.get(URL)
    assert r.status_code == 403
    assert r.json()["error"]["details"]["purposes"] == ["terms"]
