"""GET /v1/diary/recents (Plan 11 Task 7; Ruling E18)."""

from datetime import date, datetime, timedelta, timezone
from uuid import uuid4

from app.features.meals.models import MealLog
from app.features.members import service as members_service
from tests.api.diary.conftest import ACC_A

URL = "/v1/diary/recents"
IST = timezone(timedelta(hours=5, minutes=30))


def _off(member, slot, barcode, at, *, name="OFF thing", grams=30.0, day=None):
    return MealLog(
        id=uuid4(),
        account_id=ACC_A,
        member_id=member.id,
        meal_slot_id=slot,
        source_kind="off",
        off_barcode=barcode,
        product_name=name,
        grams=grams,
        nutrients={},
        eaten_at=at,
        local_date=day or at.astimezone(IST).date(),
    )


async def test_recents_dedupe_and_order(client, g1, db_session, slot_ids, product_id, clock):
    member = await members_service.get_or_create_primary(db_session, ACC_A)
    lunch = slot_ids["lunch"]
    # The same product three times (newest wins), then another, then an OFF barcode.
    await client.post(
        "/v1/meals",
        json={
            "product_id": str(product_id),
            "grams": 10,
            "local_date": "2026-11-04",
            "meal_slot_id": lunch,
        },
    )
    newest = await client.post(
        "/v1/meals",
        json={
            "product_id": str(product_id),
            "grams": 40,
            "local_date": "2026-11-06",
            "meal_slot_id": lunch,
        },
    )
    db_session.add(
        _off(member, lunch, "8901", datetime(2026, 11, 5, 8, 0, tzinfo=IST), name="Namkeen")
    )
    db_session.add(
        _off(member, lunch, "8901", datetime(2026, 11, 3, 8, 0, tzinfo=IST), name="Namkeen")
    )
    await db_session.flush()
    items = (await client.get(URL)).json()["items"]
    assert [(i["source_kind"], i["product_id"] or i["barcode"]) for i in items] == [
        ("product", str(product_id)),
        ("off", "8901"),
    ]
    assert items[0]["grams"] == 40.0 and items[0]["last_eaten_at"] == newest.json()["eaten_at"]
    assert items[1]["grams"] == 30.0 and items[1]["name"] == "Namkeen"


async def test_recents_slot_first(client, g1, db_session, slot_ids, clock):
    member = await members_service.get_or_create_primary(db_session, ACC_A)
    newer_in_lunch = _off(
        member, slot_ids["lunch"], "8001", datetime(2026, 11, 6, 13, 0, tzinfo=IST)
    )
    older_in_dinner = _off(
        member, slot_ids["dinner"], "8002", datetime(2026, 11, 5, 20, 0, tzinfo=IST)
    )
    db_session.add_all([newer_in_lunch, older_in_dinner])
    await db_session.flush()
    plain = [i["barcode"] for i in (await client.get(URL)).json()["items"]]
    assert plain == ["8001", "8002"]
    first_dinner = (await client.get(URL, params={"slot_id": slot_ids["dinner"]})).json()["items"]
    assert [i["barcode"] for i in first_dinner] == ["8002", "8001"]
    ghost = await client.get(URL, params={"slot_id": str(uuid4())})
    assert ghost.status_code == 404 and ghost.json()["error"]["code"] == "meal_slot_not_found"


async def test_recents_exclude_quick_add(client, g1, slot_ids, clock):
    await client.post("/v1/meals", json={"quick": {"energy_kcal": 300, "name": "Chai"}})
    assert (await client.get(URL)).json() == {"items": []}


async def test_recents_max_30(client, g1, db_session, slot_ids, clock):
    member = await members_service.get_or_create_primary(db_session, ACC_A)
    for i in range(35):
        at = datetime(2026, 11, 6, 0, 0, tzinfo=IST) + timedelta(minutes=i)
        db_session.add(_off(member, slot_ids["lunch"], f"89{i:04d}", at))
    await db_session.flush()
    items = (await client.get(URL)).json()["items"]
    assert len(items) == 30
    assert items[0]["barcode"] == "890034"  # newest first
    assert len((await client.get(URL, params={"limit": 5})).json()["items"]) == 5
    assert (await client.get(URL, params={"limit": 31})).status_code == 422
    assert (await client.get(URL, params={"limit": 0})).status_code == 422


async def test_recents_last_90_days_only(client, g1, db_session, slot_ids, clock):
    member = await members_service.get_or_create_primary(db_session, ACC_A)
    today = date(2026, 11, 7)
    db_session.add(
        _off(
            member,
            slot_ids["lunch"],
            "7001",
            datetime(2026, 8, 10, 12, 0, tzinfo=IST),
            day=today - timedelta(days=89),
        )  # in
    )
    db_session.add(
        _off(
            member,
            slot_ids["lunch"],
            "7002",
            datetime(2026, 8, 9, 12, 0, tzinfo=IST),
            day=today - timedelta(days=90),
        )  # out
    )
    await db_session.flush()
    assert [i["barcode"] for i in (await client.get(URL)).json()["items"]] == ["7001"]


async def test_recents_off_attribution(client, g1, db_session, slot_ids, product_id, clock):
    member = await members_service.get_or_create_primary(db_session, ACC_A)
    db_session.add(
        _off(member, slot_ids["lunch"], "8003", datetime(2026, 11, 6, 13, 0, tzinfo=IST))
    )
    await client.post(
        "/v1/meals",
        json={"product_id": str(product_id), "grams": 20, "local_date": "2026-11-05"},
    )
    await db_session.flush()
    by_kind = {i["source_kind"]: i for i in (await client.get(URL)).json()["items"]}
    assert by_kind["off"]["attribution"] == "attribution.off"
    assert by_kind["product"]["attribution"] is None
