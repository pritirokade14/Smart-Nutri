"""POST /v1/meal-slots (Plan 11 Task 14)."""

import pytest
from sqlalchemy import event, select

from app.features.meal_slots.models import MealSlot
from tests.api.meal_slots.conftest import ACC_A, ACC_B
from tests.api.meal_slots.helpers import URL, add, listing


async def test_add_fifth_and_sixth(client, consented):
    r5 = await add(client, "Chai", default_time_window={"start": "16:00", "end": "17:00"})
    assert r5.status_code == 201, r5.text
    j = r5.json()
    assert j["custom_label"] == "Chai" and j["label_key"] is None and not j["is_default"]
    assert j["position"] == 4 and j["default_time_window"] == {"start": "16:00", "end": "17:00"}
    r6 = await add(client, "Late snack")
    assert r6.status_code == 201 and r6.json()["position"] == 5
    assert len(await listing(client)) == 6


async def test_seventh_refused(client, consented):
    await add(client, "A")
    await add(client, "B")
    r = await add(client, "C")
    assert r.status_code == 422
    err = r.json()["error"]
    assert err["code"] == "meal_slot_limit_reached" and err["details"] == {"max": 6}


async def test_archived_do_not_count(client, consented):
    first = (await add(client, "A")).json()
    await add(client, "B")
    assert (await client.delete(f"{URL}/{first['id']}")).status_code == 200
    assert (await add(client, "C")).status_code == 201


async def test_duplicate_case_insensitive_refused(client, consented):
    await add(client, "Chai")
    r = await add(client, "  cHAI ")
    assert r.status_code == 422
    assert r.json()["error"] == {
        "code": "meal_slot_label_duplicate",
        "message_key": "error.meal_slot_label_duplicate",
        "details": {},
    }


async def test_duplicate_of_archived_allowed(client, consented, db_session):
    row = (await add(client, "Chai")).json()
    from tests.api.meal_slots.helpers import log_quick

    await log_quick(client, row["id"])
    assert (await client.delete(f"{URL}/{row['id']}")).json() == {"result": "archived"}
    assert (await add(client, "chai")).status_code == 201


async def test_label_31_code_points_refused(client, consented):
    r = await add(client, "a" * 31)
    assert r.status_code == 422
    assert r.json()["error"]["code"] == "validation_error"
    assert r.json()["error"]["details"] == {"fields": ["body.custom_label"]}
    assert (await add(client, "a" * 30)).status_code == 201


async def test_label_30_devanagari_code_points_accepted(client, consented):
    label = "चाय" * 10  # 30 code points, 60 UTF-8 bytes
    assert len(label) == 30
    r = await add(client, label)
    assert r.status_code == 201 and r.json()["custom_label"] == label


@pytest.mark.parametrize("label", ["", "   ", "a\nb", "a\x00b", "tab\there"])
async def test_control_char_refused(client, consented, label):
    r = await add(client, label)
    assert r.status_code == 422 and r.json()["error"]["code"] == "validation_error"


async def test_create_client_id_replay_200(client, consented, db_session):
    cid = "5b0b9e3a-3c7b-4d7a-9a55-0f6a1b7a1c11"
    first = await add(client, "Chai", client_id=cid)
    again = await add(client, "Chai", client_id=cid)
    assert first.status_code == 201 and again.status_code == 200
    assert first.json() == again.json()
    rows = list(await db_session.scalars(select(MealSlot).where(MealSlot.client_id.isnot(None))))
    assert len(rows) == 1


async def test_concurrent_creates_respect_limit(client, consented, db_session):
    """Every create locks the member row first, so two requests at 5 active are serialised:
    the second sees 6 and is refused. (The test session is single-connection, so the
    serialisation is asserted through the lock statement and the outcome.)"""
    statements: list[str] = []

    def _record(conn, cursor, statement, *_a):
        statements.append(statement)

    sync = db_session.sync_session.get_bind()
    event.listen(sync, "before_cursor_execute", _record)
    try:
        await add(client, "A")
        first = await add(client, "B")
        second = await add(client, "C")
    finally:
        event.remove(sync, "before_cursor_execute", _record)
    assert sorted([first.status_code, second.status_code]) == [201, 422]
    assert any("FROM members" in s and "FOR UPDATE" in s for s in statements)
    assert len(await listing(client)) == 6


async def test_foreign_404(client, consented, add_member):
    foreign = await add_member(ACC_B)
    r = await add(client, "Chai", member_id=str(foreign.id))
    assert r.status_code == 404 and r.json()["error"]["code"] == "member_not_found"


async def test_non_primary_422(client, consented, add_member):
    other = await add_member(ACC_A, name="Dad")
    r = await add(client, "Chai", member_id=str(other.id))
    assert r.status_code == 422 and r.json()["error"]["code"] == "diary_member_not_enabled"


async def test_slot_writes_rate_limited(client, app, consented, monkeypatch):
    monkeypatch.setattr(app.state.settings, "rate_limit_diary_writes_per_day", 2)
    assert (await add(client, "A")).status_code == 201
    first = (await listing(client))[0]["id"]
    assert (await client.patch(f"{URL}/{first}", json={"custom_label": "B"})).status_code == 200
    r = await add(client, "C")
    assert r.status_code == 429 and r.json()["error"]["code"] == "rate_limited"
    assert (await client.get(URL)).status_code == 200  # reads are not limited
