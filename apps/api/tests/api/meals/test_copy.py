"""POST /v1/meals/copy (Plan 11 Task 6; Rulings E9, E12, E21)."""

from datetime import UTC, datetime
from uuid import uuid4

import pytest
from sqlalchemy import func, select, text

from app.features.meal_slots.models import MealSlot
from app.features.meals import copy as copy_service
from app.features.meals.models import MealLog
from app.features.targets.models import DiaryGoalSettings
from tests.api.meals.conftest import ACC_A, OFF_BARCODE, FakeOff

pytestmark = pytest.mark.usefixtures("family")

URL = "/v1/meals/copy"
YESTERDAY = "2026-11-06"
TODAY = "2026-11-07"


async def _slots(client, **params) -> dict[str, str]:
    items = (await client.get("/v1/meal-slots", params=params)).json()["items"]
    return {i["label_key"]: i["id"] for i in items}


async def _log(client, slot, *, product=None, day=YESTERDAY, **kw):
    body = {"meal_slot_id": slot, "local_date": day, **kw}
    if product is not None:
        body["product_id"] = str(product)
        body.setdefault("grams", 30)
    r = await client.post("/v1/meals", json=body)
    assert r.status_code == 201, r.text
    return r.json()


def _copy_body(**kw):
    return {"from_date": YESTERDAY, "to_date": TODAY, "client_id": str(uuid4()), **kw}


async def _count(db_session) -> int:
    return await db_session.scalar(select(func.count()).select_from(MealLog))


async def test_copy_meal_to_today(client, clock, sf_biscuit_product_id, db_session):
    slots = await _slots(client)
    src = await _log(client, slots["diary.slot.breakfast"], product=sf_biscuit_product_id, grams=50)
    await _log(client, slots["diary.slot.lunch"], product=sf_biscuit_product_id, grams=20)
    r = await client.post(URL, json=_copy_body(from_slot_id=slots["diary.slot.breakfast"]))
    assert r.status_code == 201, r.text
    [copy] = r.json()["created"]
    assert copy["local_date"] == TODAY and copy["meal_slot_id"] == slots["diary.slot.breakfast"]
    assert copy["nutrients"] == src["nutrients"] and copy["grams"] == 50.0
    assert copy["id"] != src["id"] and copy["product_id"] == src["product_id"]
    assert copy["grade"] == src["grade"] and copy["source_kind"] == "product"
    # The sources are unchanged.
    old = (await client.get("/v1/meals", params={"local_date": YESTERDAY})).json()
    assert src["id"] in {m["id"] for m in old} and len(old) == 2
    assert [m["updated_at"] for m in old if m["id"] == src["id"]] == [src["updated_at"]]


async def test_copy_day_keeps_slots(client, clock, sf_biscuit_product_id):
    slots = await _slots(client)
    await _log(client, slots["diary.slot.breakfast"], product=sf_biscuit_product_id)
    await _log(client, slots["diary.slot.dinner"], product=sf_biscuit_product_id)
    r = await client.post(URL, json=_copy_body())
    assert r.status_code == 201
    assert sorted(c["meal_slot_id"] for c in r.json()["created"]) == sorted(
        [slots["diary.slot.breakfast"], slots["diary.slot.dinner"]]
    )
    assert len((await client.get("/v1/meals", params={"local_date": TODAY})).json()) == 2


async def test_copy_to_other_slot(client, clock, sf_biscuit_product_id):
    slots = await _slots(client)
    await _log(client, slots["diary.slot.breakfast"], product=sf_biscuit_product_id)
    r = await client.post(
        URL,
        json=_copy_body(
            from_slot_id=slots["diary.slot.breakfast"], to_slot_id=slots["diary.slot.snack"]
        ),
    )
    assert r.json()["created"][0]["meal_slot_id"] == slots["diary.slot.snack"]


async def test_copy_retry_returns_same_rows(client, clock, sf_biscuit_product_id, db_session):
    slots = await _slots(client)
    await _log(client, slots["diary.slot.breakfast"], product=sf_biscuit_product_id)
    await _log(client, slots["diary.slot.lunch"], product=sf_biscuit_product_id)
    body = _copy_body()
    first = await client.post(URL, json=body)
    before = await _count(db_session)
    again = await client.post(URL, json=body)
    assert (first.status_code, again.status_code) == (201, 200)
    assert [c["id"] for c in first.json()["created"]] == [c["id"] for c in again.json()["created"]]
    assert await _count(db_session) == before == 4
    # A different client_id is a new copy.
    third = await client.post(URL, json=_copy_body())
    assert third.status_code == 201 and await _count(db_session) == 6


async def test_copy_double_tap_creates_once(
    client, clock, sf_biscuit_product_id, db_session, monkeypatch
):
    """A concurrent request won the race and inserted the first copy between this request's
    existence check and its insert: ON CONFLICT DO NOTHING keeps one set of copies."""
    slots = await _slots(client)
    await _log(client, slots["diary.slot.breakfast"], product=sf_biscuit_product_id)
    await _log(client, slots["diary.slot.lunch"], product=sf_biscuit_product_id)
    body = _copy_body()
    real = copy_service._read_back
    calls = {"n": 0}

    async def racing(session, account_id, ids):
        calls["n"] += 1
        if calls["n"] == 1:
            first = (
                await session.scalars(
                    select(MealLog).where(MealLog.local_date.isnot(None)).order_by(MealLog.eaten_at)
                )
            ).first()
            await session.execute(
                text(
                    "insert into meal_logs (account_id, member_id, source_kind, product_id, grams, "
                    "nutrients, eaten_at, local_date, meal_slot_id, client_id) "
                    "select account_id, member_id, source_kind, product_id, grams, nutrients, "
                    "eaten_at, local_date, meal_slot_id, :c from meal_logs where id = :i"
                ),
                {"c": ids[0], "i": first.id},
            )
            return []  # this request did not see it yet
        return await real(session, account_id, ids)

    monkeypatch.setattr(copy_service, "_read_back", racing)
    r = await client.post(URL, json=body)
    assert r.status_code == 201, r.text
    assert len(r.json()["created"]) == 2
    assert await _count(db_session) == 4  # 2 sources + 2 copies, no duplicate


async def test_copy_future_clock_time_capped_at_now(client, clock, sf_biscuit_product_id):
    clock.set("2026-11-07T03:30:00+00:00")  # 09:00 IST
    slots = await _slots(client)
    r = await client.post(
        "/v1/meals",
        json={
            "product_id": str(sf_biscuit_product_id),
            "grams": 30,
            "meal_slot_id": slots["diary.slot.dinner"],
            "eaten_at": "2026-11-06T14:30:00+00:00",  # yesterday 20:00 IST
        },
    )
    assert r.status_code == 201
    copied = await client.post(URL, json=_copy_body())
    assert copied.status_code == 201, copied.text
    [c] = copied.json()["created"]
    assert datetime.fromisoformat(c["eaten_at"]) == clock.now  # never in the future, never 422
    assert c["local_date"] == TODAY and c["meal_slot_id"] == slots["diary.slot.dinner"]


async def test_copy_keeps_past_clock_time_on_a_past_day(client, clock, sf_biscuit_product_id):
    slots = await _slots(client)
    await client.post(
        "/v1/meals",
        json={
            "product_id": str(sf_biscuit_product_id),
            "grams": 30,
            "meal_slot_id": slots["diary.slot.dinner"],
            "eaten_at": "2026-11-05T14:30:00+00:00",  # 20:00 IST on the 5th
        },
    )
    r = await client.post(
        URL, json={"from_date": "2026-11-05", "to_date": YESTERDAY, "client_id": str(uuid4())}
    )
    [c] = r.json()["created"]
    assert c["eaten_at"].startswith("2026-11-06T14:30:00") and c["local_date"] == YESTERDAY


async def test_copy_uses_source_snapshot_not_product(
    client, clock, sf_biscuit_product_id, db_session
):
    slots = await _slots(client)
    src = await _log(client, slots["diary.slot.lunch"], product=sf_biscuit_product_id, grams=50)
    await db_session.execute(
        text("update products set per_100g = jsonb_set(per_100g, '{energy_kcal}', '999')")
    )
    [c] = (await client.post(URL, json=_copy_body())).json()["created"]
    assert c["nutrients"] == src["nutrients"]

    async def snap(meal_id):
        row = await db_session.execute(
            text("select food_snapshot from meal_logs where id = :i"), {"i": meal_id}
        )
        return row.scalar_one()

    a, b = await snap(src["id"]), await snap(c["id"])
    assert a == b  # the copy carries the source's snapshot


async def test_copy_off_entry_needs_no_product_fetch(client, clock, login, family):
    slots = await _slots(client)
    r = await client.post(
        "/v1/meals",
        json={
            "barcode": OFF_BARCODE,
            "grams": 30,
            "local_date": YESTERDAY,
            "meal_slot_id": slots["diary.slot.lunch"],
        },
    )
    assert r.status_code == 201
    login(off=FakeOff(fail=True))  # Open Food Facts is down: the copy never asks it
    copied = await client.post(URL, json=_copy_body())
    assert copied.status_code == 201, copied.text
    [c] = copied.json()["created"]
    assert c["source_kind"] == "off" and c["barcode"] == OFF_BARCODE
    assert c["attribution"] == "attribution.off" and c["nutrients"] == r.json()["nutrients"]


async def test_copy_quick_add_entry(client, clock):
    slots = await _slots(client)
    q = await client.post(
        "/v1/meals",
        json={
            "quick": {"energy_kcal": 450, "name": "Office lunch"},
            "local_date": YESTERDAY,
            "meal_slot_id": slots["diary.slot.lunch"],
        },
    )
    [c] = (await client.post(URL, json=_copy_body())).json()["created"]
    assert c["source_kind"] == "quick_add" and c["grams"] is None
    assert c["product_name"] == "Office lunch" and c["nutrients"] == q.json()["nutrients"]
    assert "protein_g" in c["incomplete"]


async def test_copy_legacy_source_gets_a_derived_snapshot(
    client, clock, sf_biscuit_product_id, db_session
):
    slots = await _slots(client)
    src = await _log(client, slots["diary.slot.lunch"], product=sf_biscuit_product_id, grams=50)
    await db_session.execute(
        text("update meal_logs set food_snapshot = null where id = :i"), {"i": src["id"]}
    )
    [c] = (await client.post(URL, json=_copy_body())).json()["created"]
    snap = (
        await db_session.execute(
            text("select food_snapshot from meal_logs where id = :i"), {"i": c["id"]}
        )
    ).scalar_one()
    assert snap["basis"] == "g" and snap["per_100"]["energy_kcal"] == pytest.approx(
        src["nutrients"]["energy_kcal"] * 2, abs=0.1
    )


async def test_copy_errors(client, clock, sf_biscuit_product_id, db_session, family):
    slots = await _slots(client)
    one = await _log(client, slots["diary.slot.lunch"], product=sf_biscuit_product_id)
    cases = {
        "empty": ({"from_date": "2026-11-01"}, 422, "copy_source_empty"),
        "future_to": ({"to_date": "2026-11-08"}, 422, "date_in_future"),
        "future_from": ({"from_date": "2026-11-08"}, 422, "date_in_future"),
        "too_old": ({"to_date": "2026-10-07"}, 422, "date_too_old"),
        "foreign_slot": ({"to_slot_id": str(uuid4())}, 404, "meal_slot_not_found"),
        "foreign_from_slot": ({"from_slot_id": str(uuid4())}, 404, "meal_slot_not_found"),
    }
    for name, (patch, status, code) in cases.items():
        r = await client.post(URL, json=_copy_body(**patch))
        assert (r.status_code, r.json()["error"]["code"]) == (status, code), name
    # 30 days back is the oldest allowed target.
    ok = await client.post(URL, json=_copy_body(to_date="2026-10-08"))
    assert ok.status_code == 201
    # Another member's slot is a 404, not a leak.
    dad = await client.post(
        "/v1/meals",
        json={"member_id": str(family.dad), "quick": {"energy_kcal": 100}},
    )
    r = await client.post(URL, json=_copy_body(to_slot_id=dad.json()["meal_slot_id"]))
    assert (r.status_code, r.json()["error"]["code"]) == (404, "meal_slot_not_found")
    # An archived target slot.
    row = await db_session.get(MealSlot, slots["diary.slot.snack"])
    row.archived_at = datetime.now(UTC)
    await db_session.flush()
    r = await client.post(URL, json=_copy_body(to_slot_id=slots["diary.slot.snack"]))
    assert (r.status_code, r.json()["error"]["code"]) == (422, "meal_slot_archived")
    assert one["id"]


async def test_copy_too_many(client, clock, sf_biscuit_product_id, db_session, family):
    slots = await _slots(client)
    base = await _log(client, slots["diary.slot.lunch"], product=sf_biscuit_product_id)
    row = await db_session.get(MealLog, base["id"])
    for _ in range(50):  # 51 entries on the day
        db_session.add(
            MealLog(
                account_id=ACC_A,
                member_id=row.member_id,
                source_kind="quick_add",
                grams=None,
                nutrients=row.nutrients,
                eaten_at=row.eaten_at,
                local_date=row.local_date,
                meal_slot_id=row.meal_slot_id,
            )
        )
    await db_session.flush()
    r = await client.post(URL, json=_copy_body())
    assert (r.status_code, r.json()["error"]["code"]) == (422, "copy_too_many")
    row_count = await _count(db_session)
    assert row_count == 51


async def test_copy_from_archived_slot_needs_target(
    client, clock, sf_biscuit_product_id, db_session
):
    slots = await _slots(client)
    await _log(client, slots["diary.slot.snack"], product=sf_biscuit_product_id)
    row = await db_session.get(MealSlot, slots["diary.slot.snack"])
    row.archived_at = datetime.now(UTC)
    await db_session.flush()
    r = await client.post(URL, json=_copy_body(from_slot_id=slots["diary.slot.snack"]))
    assert (r.status_code, r.json()["error"]["code"]) == (422, "meal_slot_archived")
    ok = await client.post(
        URL,
        json=_copy_body(
            from_slot_id=slots["diary.slot.snack"], to_slot_id=slots["diary.slot.lunch"]
        ),
    )
    assert (
        ok.status_code == 201
        and ok.json()["created"][0]["meal_slot_id"] == slots["diary.slot.lunch"]
    )


async def test_copy_counts_each_entry_against_meal_logs(
    client, app, clock, sf_biscuit_product_id, db_session, monkeypatch
):
    slots = await _slots(client)
    for slot in (
        "diary.slot.breakfast",
        "diary.slot.lunch",
        "diary.slot.snack",
        "diary.slot.dinner",
    ):
        await _log(client, slots[slot], product=sf_biscuit_product_id)
    monkeypatch.setattr(app.state.settings, "rate_limit_meal_logs_per_day", 3)
    before = await _count(db_session)
    r = await client.post(URL, json=_copy_body())  # 4 entries against a limit of 3
    assert r.status_code == 429 and r.json()["error"]["code"] == "rate_limited"
    assert await _count(db_session) == before  # nothing created


async def test_copy_redacted_when_hidden(client, clock, sf_biscuit_product_id, db_session, family):
    slots = await _slots(client)
    await _log(client, slots["diary.slot.lunch"], product=sf_biscuit_product_id, grams=100)
    db_session.add(
        DiaryGoalSettings(
            member_id=family.me,
            account_id=ACC_A,
            direction="maintain",
            activity_level="light",
            numbers_display="hide_all",
        )
    )
    await db_session.flush()
    [c] = (await client.post(URL, json=_copy_body())).json()["created"]
    assert all(v is None for v in c["nutrients"].values()) and c["grams"] == 100.0


async def test_copy_family_member_422(client, clock, family, app, monkeypatch):
    r = await client.post(URL, json=_copy_body(member_id=str(family.dad)))
    assert (r.status_code, r.json()["error"]["code"]) == (422, "diary_member_not_enabled")
    foreign = await client.post(URL, json=_copy_body(member_id=str(uuid4())))
    assert (foreign.status_code, foreign.json()["error"]["code"]) == (404, "member_not_found")
