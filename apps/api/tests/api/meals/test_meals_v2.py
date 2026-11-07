"""Meals v2: slot, local date, snapshot (Plan 11 Task 4; Rulings E8, E9, E11, E21, E22)."""

from datetime import UTC, datetime
from uuid import uuid4

import pytest
from sqlalchemy import select

from app.features.diary.models import DiaryDay
from app.features.meal_slots.models import MealSlot
from app.features.meals.models import MealLog
from app.features.members.models import Member
from app.features.targets.models import DiaryGoalSettings
from tests.api.meals.conftest import ACC_A, OFF_BARCODE

pytestmark = pytest.mark.usefixtures("family")


async def _slots(client, **params) -> dict[str, str]:
    """label_key -> id of the primary's slots."""
    items = (await client.get("/v1/meal-slots", params=params)).json()["items"]
    return {i["label_key"]: i["id"] for i in items}


async def _log(client, member=None, product=None, **kw):
    body = dict(kw)
    if member is not None:
        body["member_id"] = str(member)
    if product is not None:
        body["product_id"] = str(product)
    return await client.post("/v1/meals", json=body)


async def test_log_without_slot_picks_from_local_time(client, family, sf_biscuit_product_id, clock):
    clock.set("2026-11-07T16:00:00+00:00")  # 21:30 IST
    slots = await _slots(client)
    morning = await _log(
        client, family.me, sf_biscuit_product_id, grams=30, eaten_at="2026-11-07T03:30:00+00:00"
    )  # 09:00 IST
    evening = await _log(
        client, family.me, sf_biscuit_product_id, grams=30, eaten_at="2026-11-06T15:30:00+00:00"
    )  # 21:00 IST
    assert morning.json()["meal_slot_id"] == slots["diary.slot.breakfast"]
    assert evening.json()["meal_slot_id"] == slots["diary.slot.dinner"]
    assert morning.json()["local_date"] == "2026-11-07"
    assert evening.json()["local_date"] == "2026-11-06"


async def test_log_local_date_uses_account_zone(client, family, sf_biscuit_product_id, clock):
    assert (
        await client.put("/v1/me/timezone", json={"timezone": "America/New_York"})
    ).status_code == 200
    clock.set("2026-11-08T03:00:00+00:00")
    slots = await _slots(client)
    r = await _log(
        client, family.me, sf_biscuit_product_id, grams=30, eaten_at="2026-11-08T02:00:00+00:00"
    )
    assert r.status_code == 201, r.text
    # 02:00Z is 21:00 on 7 Nov in New York (and already 7:30 on 8 Nov in India).
    assert r.json()["local_date"] == "2026-11-07"
    assert r.json()["meal_slot_id"] == slots["diary.slot.dinner"]


async def test_log_with_local_date_past_day(client, family, sf_biscuit_product_id, clock):
    r = await _log(client, family.me, sf_biscuit_product_id, grams=30, local_date="2026-11-06")
    assert r.status_code == 201, r.text
    j = r.json()
    assert j["local_date"] == "2026-11-06"
    assert j["eaten_at"].startswith("2026-11-06T06:30:00")  # yesterday at the current clock time


async def test_log_with_local_date_today_and_future(client, family, sf_biscuit_product_id, clock):
    today = await _log(client, family.me, sf_biscuit_product_id, grams=30, local_date="2026-11-07")
    assert today.status_code == 201 and today.json()["local_date"] == "2026-11-07"
    future = await _log(client, family.me, sf_biscuit_product_id, grams=30, local_date="2026-11-08")
    assert future.status_code == 422 and future.json()["error"]["code"] == "date_in_future"
    old = await _log(client, family.me, sf_biscuit_product_id, grams=30, local_date="2026-09-01")
    assert old.status_code == 422 and old.json()["error"]["code"] == "eaten_at_out_of_range"


async def test_local_date_and_eaten_at_together_422(client, family, sf_biscuit_product_id, clock):
    r = await _log(
        client,
        family.me,
        sf_biscuit_product_id,
        grams=30,
        local_date="2026-11-06",
        eaten_at="2026-11-06T06:30:00+00:00",
    )
    assert r.status_code == 422 and r.json()["error"]["code"] == "validation_error"


async def test_log_into_archived_slot_422(client, family, sf_biscuit_product_id, db_session):
    slots = await _slots(client)
    row = await db_session.get(MealSlot, slots["diary.slot.snack"])
    row.archived_at = datetime.now(UTC)
    await db_session.flush()
    r = await _log(
        client,
        family.me,
        sf_biscuit_product_id,
        grams=30,
        meal_slot_id=slots["diary.slot.snack"],
    )
    assert r.status_code == 422 and r.json()["error"]["code"] == "meal_slot_archived"


async def test_log_into_other_members_slot_404(client, family, sf_biscuit_product_id):
    dad_meal = await _log(client, family.dad, sf_biscuit_product_id, grams=30)
    r = await _log(
        client,
        family.me,
        sf_biscuit_product_id,
        grams=30,
        meal_slot_id=dad_meal.json()["meal_slot_id"],
    )
    assert r.status_code == 404 and r.json()["error"]["code"] == "meal_slot_not_found"
    ghost = await _log(
        client, family.me, sf_biscuit_product_id, grams=30, meal_slot_id=str(uuid4())
    )
    assert ghost.status_code == 404 and ghost.json()["error"]["code"] == "meal_slot_not_found"


async def test_family_member_log_still_works(client, family, sf_biscuit_product_id, db_session):
    r = await _log(client, family.dad, sf_biscuit_product_id, grams=30)
    assert r.status_code == 201 and r.json()["member_id"] == str(family.dad)
    slots = list(await db_session.scalars(select(MealSlot).where(MealSlot.member_id == family.dad)))
    assert len(slots) == 4  # its own hidden default slots (Ruling E9)
    assert r.json()["meal_slot_id"] in {str(s.id) for s in slots}


async def test_member_id_optional_is_primary(client, family, sf_biscuit_product_id):
    r = await _log(client, None, sf_biscuit_product_id, grams=30)
    assert r.status_code == 201 and r.json()["member_id"] == str(family.me)
    listed = (await client.get("/v1/meals")).json()
    assert [m["id"] for m in listed] == [r.json()["id"]]


async def test_snapshot_has_fibre_and_food_snapshot(
    client, family, sf_biscuit_product_id, db_session
):
    r = await _log(client, family.me, sf_biscuit_product_id, servings=2)
    j = r.json()
    assert "fibre_g" in j["nutrients"] and j["source_kind"] == "product"
    row = await db_session.get(MealLog, j["id"])
    snap = row.food_snapshot
    assert snap["name"] == "Sugar Free Biscuit" and snap["basis"] == "g"
    assert set(snap["per_100"]) == {
        "energy_kcal",
        "sugars_g",
        "salt_g",
        "protein_g",
        "fat_g",
        "sat_fat_g",
        "carbs_g",
        "fibre_g",
    }
    # Plan 12: every unit that resolved at log time (grams always, then the serving).
    assert snap["units"] == {"g": 1.0, "serving": 25.0} and snap["attribution"] is None
    assert row.updated_at is not None and row.local_date is not None


async def test_off_product_keeps_attribution(client, family, db_session):
    r = await client.post(
        "/v1/meals", json={"member_id": str(family.me), "barcode": OFF_BARCODE, "grams": 30}
    )
    j = r.json()
    assert j["source_kind"] == "off" and j["attribution"] == "attribution.off"
    row = await db_session.get(MealLog, j["id"])
    assert row.food_snapshot["attribution"] == "attribution.off"
    assert row.food_snapshot["per_100"]["sugars_g"] is None  # never 0
    assert "sugars_g" in j["incomplete"]


async def test_offline_entry_keeps_eaten_at_day(client, family, sf_biscuit_product_id, clock):
    """An entry logged at 23:30 IST that syncs after midnight keeps its day."""
    clock.set("2026-11-06T18:05:00+00:00")  # 23:35 IST on 6 Nov
    body = {
        "member_id": str(family.me),
        "product_id": str(sf_biscuit_product_id),
        "grams": 30,
        "client_id": str(uuid4()),
        "eaten_at": "2026-11-06T18:00:00+00:00",  # 23:30 IST
    }
    first = await client.post("/v1/meals", json=body)
    assert first.status_code == 201 and first.json()["local_date"] == "2026-11-06"
    clock.set("2026-11-06T19:00:00+00:00")  # 00:30 IST on 7 Nov: the retry arrives
    again = await client.post("/v1/meals", json=body)
    assert again.status_code == 200
    assert again.json()["id"] == first.json()["id"] and again.json()["local_date"] == "2026-11-06"
    # A fresh offline entry that syncs after midnight lands on its own eaten_at day too.
    fresh = await client.post("/v1/meals", json={**body, "client_id": str(uuid4())})
    assert fresh.status_code == 201 and fresh.json()["local_date"] == "2026-11-06"


async def test_log_today_creates_day_row_with_health_data(
    client,
    family,
    sf_biscuit_product_id,
    db_session,
    grant,
    clock,
):
    await grant(ACC_A)
    me = await db_session.get(Member, family.me)
    me.birth_year, me.sex, me.height_cm, me.weight_kg = 1997, "male", 175, 70
    me.goal = "build_muscle"
    db_session.add(
        DiaryGoalSettings(
            member_id=me.id, account_id=ACC_A, direction="gain", activity_level="moderate"
        )
    )
    await db_session.flush()
    assert (await _log(client, family.me, sf_biscuit_product_id, grams=30)).status_code == 201
    rows = list(await db_session.scalars(select(DiaryDay).where(DiaryDay.member_id == me.id)))
    assert [(str(r.local_date), r.status) for r in rows] == [("2026-11-07", "ready")]
    # A past-day entry never creates or changes a frozen row.
    await _log(client, family.me, sf_biscuit_product_id, grams=30, local_date="2026-11-05")
    rows = list(
        await db_session.scalars(
            select(DiaryDay)
            .where(DiaryDay.member_id == me.id)
            .execution_options(populate_existing=True)
        )
    )
    assert [str(r.local_date) for r in rows] == ["2026-11-07"]


async def test_log_without_health_data_writes_no_day_row(
    client, family, sf_biscuit_product_id, db_session
):
    assert (await _log(client, family.me, sf_biscuit_product_id, grams=30)).status_code == 201
    assert list(await db_session.scalars(select(DiaryDay))) == []
