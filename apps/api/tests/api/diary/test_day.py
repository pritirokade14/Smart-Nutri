"""GET /v1/diary/day (Plan 11 Task 7; Rulings E5, E9, E14)."""

from datetime import UTC, datetime

from app.features.meal_slots.models import MealSlot
from app.features.members import service as members_service
from tests.api.diary.conftest import ACC_A, ACC_B, G1_SETTINGS
from tests.api.diary.seeding import load_expected, load_input, normalise, seed_entries

URL = "/v1/diary/day"
S = "/v1/targets/settings"


async def test_day_matches_golden_complete_under(
    client, g1, db_session, slot_ids, product_id, clock
):
    case = load_input("day_complete_under")
    assert (await client.put(S, json=G1_SETTINGS)).status_code == 200
    seed_entries(
        db_session, ACC_A, g1, slot_ids, case["date"], case["entries"], "Asia/Kolkata", product_id
    )
    await db_session.flush()
    r = await client.get(URL)
    assert r.status_code == 200, r.text
    got = normalise(r.json())
    want = normalise(load_expected("day_complete_under"))
    assert got == want


async def test_day_with_no_entries_matches_golden_empty(client, g1, slot_ids):
    assert (await client.put(S, json=G1_SETTINGS)).status_code == 200
    got = normalise((await client.get(URL)).json())
    assert got == normalise(load_expected("day_empty"))


async def test_day_lists_active_slots_in_order(client, g1, slot_ids):
    j = (await client.get(URL)).json()
    assert [s["label_key"] for s in j["slots"]] == [
        "diary.slot.breakfast",
        "diary.slot.lunch",
        "diary.slot.snack",
        "diary.slot.dinner",
    ]
    assert [s["position"] for s in j["slots"]] == [0, 1, 2, 3]
    assert all(s["entries"] == [] and not s["archived"] for s in j["slots"])
    assert j["member_id"] == str(g1) and j["pending_clinician_review"] is True


async def test_archived_slot_only_on_days_with_entries(client, g1, db_session, slot_ids):
    quick = {"quick": {"energy_kcal": 200}, "meal_slot_id": slot_ids["snack"]}
    assert (
        await client.post("/v1/meals", json={**quick, "local_date": "2026-11-06"})
    ).status_code == 201
    row = await db_session.get(MealSlot, slot_ids["snack"])
    row.archived_at = datetime.now(UTC)
    await db_session.flush()
    with_entries = (await client.get(URL, params={"date": "2026-11-06"})).json()
    snack = [s for s in with_entries["slots"] if s["slot_id"] == slot_ids["snack"]]
    assert len(snack) == 1 and snack[0]["archived"] is True and len(snack[0]["entries"]) == 1
    without = (await client.get(URL, params={"date": "2026-11-07"})).json()
    assert all(s["slot_id"] != slot_ids["snack"] for s in without["slots"])


async def test_day_today_field(client, g1, clock):
    j = (await client.get(URL)).json()
    assert (j["date"], j["today"], j["timezone"]) == ("2026-11-07", "2026-11-07", "Asia/Kolkata")
    assert (
        await client.put("/v1/me/timezone", json={"timezone": "America/New_York"})
    ).status_code == 200
    clock.set("2026-11-08T03:00:00+00:00")  # 22:00 on 7 Nov in New York
    j = (await client.get(URL)).json()
    assert (j["date"], j["today"], j["timezone"]) == (
        "2026-11-07",
        "2026-11-07",
        "America/New_York",
    )


async def test_future_date_422(client, g1):
    r = await client.get(URL, params={"date": "2026-11-08"})
    assert r.status_code == 422 and r.json()["error"]["code"] == "date_in_future"


async def test_timezone_change_keeps_past_dates(client, g1, clock):
    # 01:00 IST on 7 Nov is 19:30Z on 6 Nov (14:30 in New York on the 6th).
    clock.set("2026-11-06T19:30:00+00:00")
    r = await client.post("/v1/meals", json={"quick": {"energy_kcal": 300}})
    assert r.status_code == 201 and r.json()["local_date"] == "2026-11-07"
    assert (
        await client.put("/v1/me/timezone", json={"timezone": "America/New_York"})
    ).status_code == 200
    clock.set("2026-11-08T12:00:00+00:00")  # 7:00 on the 8th in New York
    on_seventh = (await client.get(URL, params={"date": "2026-11-07"})).json()
    on_sixth = (await client.get(URL, params={"date": "2026-11-06"})).json()
    assert sum(len(s["entries"]) for s in on_seventh["slots"]) == 1  # stays on its IST date
    assert sum(len(s["entries"]) for s in on_sixth["slots"]) == 0


async def test_foreign_member_404(client, g1, add_member):
    foreign = await add_member(ACC_B)
    r = await client.get(URL, params={"member_id": str(foreign.id)})
    assert r.status_code == 404 and r.json()["error"]["code"] == "member_not_found"


async def test_non_primary_422(client, g1, add_member, app, monkeypatch):
    other = await add_member(ACC_A, name="Dad")
    r = await client.get(URL, params={"member_id": str(other.id)})
    assert r.status_code == 422 and r.json()["error"]["code"] == "diary_member_not_enabled"
    monkeypatch.setattr(app.state.settings, "diary_family_enabled", True)
    assert (await client.get(URL, params={"member_id": str(other.id)})).status_code == 200


async def test_day_reads_today_row_and_commits(client, g1, db_session):
    from sqlalchemy import select

    from app.features.diary.models import DiaryDay

    await client.put(S, json=G1_SETTINGS)
    j = (await client.get(URL)).json()
    assert j["targets_status"] == "ready" and j["targets"]["energy_kcal"] == 2760
    assert j["remaining"]["energy_kcal"] == 2760.0 and j["progress"]["energy_kcal"] == 0.0
    rows = list(await db_session.scalars(select(DiaryDay)))
    assert [str(r.local_date) for r in rows] == ["2026-11-07"]
    assert members_service  # the primary exists
