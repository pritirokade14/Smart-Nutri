"""favourites_log (Plan 12 Task 17; G21, G23): re-log from the snapshots, as a copy does."""

from uuid import uuid4

from sqlalchemy import select, text

from app.features.meals.models import MealLog
from tests.api.favourites.conftest import log_custom, make_custom, save_meal

URL = "/v1/favourites"


async def _saved(client, slot_ids, clock, *, items=2):
    cf = await make_custom(client)
    for i in range(items):
        clock.set(f"2026-11-07T06:{30 + i}:00+00:00")  # distinct times: a stable saved order
        await log_custom(client, cf, slot_ids["breakfast"], grams=50 + i)
    fav = (await save_meal(client, slot_ids["breakfast"])).json()
    return cf, fav


async def test_log_meal_creates_entries_from_snapshots(client, g1, slot_ids, clock, db_session):
    cf, fav = await _saved(client, slot_ids, clock)
    clock.set("2026-11-08T06:30:00+00:00")  # the next day
    cid = str(uuid4())
    r = await client.post(
        f"{URL}/{fav['id']}/log", json={"client_id": cid, "meal_slot_id": slot_ids["dinner"]}
    )
    assert r.status_code == 201, r.text
    created = r.json()["created"]
    assert [(e["grams"], e["local_date"], e["meal_slot_id"]) for e in created] == [
        (50.0, "2026-11-08", slot_ids["dinner"]),
        (51.0, "2026-11-08", slot_ids["dinner"]),
    ]
    assert all(e["custom_food_id"] == cf and e["product_name"] == "Protein bar" for e in created)
    assert created[0]["nutrients"]["protein_g"] == 15.0  # the saved values, not re-read
    day = (await client.get("/v1/diary/day", params={"date": "2026-11-08"})).json()
    assert sum(len(s["entries"]) for s in day["slots"]) == 2


async def test_log_on_a_past_day_and_range(client, g1, slot_ids, clock):
    _, fav = await _saved(client, slot_ids, clock, items=1)
    ok = await client.post(
        f"{URL}/{fav['id']}/log", json={"client_id": str(uuid4()), "local_date": "2026-11-05"}
    )
    assert ok.status_code == 201 and ok.json()["created"][0]["local_date"] == "2026-11-05"
    future = await client.post(
        f"{URL}/{fav['id']}/log", json={"client_id": str(uuid4()), "local_date": "2026-11-08"}
    )
    assert future.status_code == 422 and future.json()["error"]["code"] == "date_in_future"
    old = await client.post(
        f"{URL}/{fav['id']}/log", json={"client_id": str(uuid4()), "local_date": "2026-09-01"}
    )
    assert old.status_code == 422 and old.json()["error"]["code"] == "date_too_old"
    nocid = await client.post(f"{URL}/{fav['id']}/log", json={})
    assert nocid.status_code == 422


async def test_slot_rules(client, g1, slot_ids, clock):
    _, fav = await _saved(client, slot_ids, clock, items=1)
    r = await client.post(
        f"{URL}/{fav['id']}/log", json={"client_id": str(uuid4()), "meal_slot_id": str(uuid4())}
    )
    assert r.status_code == 404 and r.json()["error"]["code"] == "meal_slot_not_found"


async def test_retry_returns_same_rows_200(client, g1, slot_ids, clock, db_session):
    _, fav = await _saved(client, slot_ids, clock)
    cid = str(uuid4())
    first = await client.post(f"{URL}/{fav['id']}/log", json={"client_id": cid})
    again = await client.post(f"{URL}/{fav['id']}/log", json={"client_id": cid})
    assert first.status_code == 201 and again.status_code == 200
    assert [e["id"] for e in again.json()["created"]] == [e["id"] for e in first.json()["created"]]
    n = await db_session.scalar(text("select count(*) from meal_logs"))
    assert n == 4  # 2 originals + 2 logged once
    other = await client.post(f"{URL}/{fav['id']}/log", json={"client_id": str(uuid4())})
    assert other.status_code == 201  # a new action logs again


async def test_deleted_custom_food_item_logs_with_null_ref(client, g1, slot_ids, clock, db_session):
    cf, fav = await _saved(client, slot_ids, clock, items=1)
    await client.delete(f"/v1/custom-foods/{cf}")
    r = await client.post(f"{URL}/{fav['id']}/log", json={"client_id": str(uuid4())})
    assert r.status_code == 201, r.text
    entry = r.json()["created"][0]
    assert entry["custom_food_id"] is None and entry["product_name"] == "Protein bar"
    assert entry["grams"] == 50.0 and entry["source_kind"] == "custom_food"
    row = await db_session.scalar(select(MealLog).where(MealLog.id == entry["id"]))
    assert row.custom_food_id is None


async def test_retired_dish_is_refused_and_nothing_counts(
    client, g1, slot_ids, clock, dal, db_session
):
    r = await client.post(
        "/v1/meals",
        json={
            "food_id": str(dal.id),
            "quantity": 1,
            "unit": "katori",
            "meal_slot_id": slot_ids["lunch"],
        },
    )
    assert r.status_code == 201, r.text
    fav = (await save_meal(client, slot_ids["lunch"])).json()
    dal.review_status = "retired"
    await db_session.flush()
    out = await client.post(f"{URL}/{fav['id']}/log", json={"client_id": str(uuid4())})
    assert out.status_code == 422 and out.json()["error"]["code"] == "food_retired"
    assert await db_session.scalar(text("select count(*) from meal_logs")) == 1
    assert (await client.get(URL)).json()["items"][0]["items"][0][
        "name"
    ] == "Lentils, cooked"  # readable


async def test_counts_against_meal_logs(client, g1, slot_ids, clock, app, monkeypatch, db_session):
    _, fav = await _saved(client, slot_ids, clock, items=2)
    # 2 logs so far + the 2 entries of one re-log: a limit of 4 allows one, not two.
    monkeypatch.setattr(app.state.settings, "rate_limit_meal_logs_per_day", 4)
    one = await client.post(f"{URL}/{fav['id']}/log", json={"client_id": str(uuid4())})
    assert one.status_code == 201, one.text
    over = await client.post(f"{URL}/{fav['id']}/log", json={"client_id": str(uuid4())})
    assert over.status_code == 429 and over.json()["error"]["code"] == "rate_limited"
    assert await db_session.scalar(text("select count(*) from meal_logs")) == 4  # nothing created


async def test_food_favourite_log_422(client, g1, clock):
    cf = await make_custom(client)
    fav = (await client.post(URL, json={"custom_food_id": cf})).json()
    r = await client.post(f"{URL}/{fav['id']}/log", json={"client_id": str(uuid4())})
    assert r.status_code == 422 and r.json()["error"]["code"] == "validation_error"


async def test_log_redacted_under_hide_all(client, g1, slot_ids, clock):
    from tests.api.diary.conftest import G1_SETTINGS

    _, fav = await _saved(client, slot_ids, clock, items=1)
    assert (
        await client.put(
            "/v1/targets/settings", json={**G1_SETTINGS, "numbers_display": "hide_all"}
        )
    ).status_code == 200
    r = await client.post(f"{URL}/{fav['id']}/log", json={"client_id": str(uuid4())})
    assert r.status_code == 201
    entry = r.json()["created"][0]
    assert all(v is None for v in entry["nutrients"].values())
    assert entry["grams"] == 50.0  # the portion stays
    listing = (await client.get(URL)).json()
    assert "protein_g" not in str(listing) and "energy_kcal" not in str(listing)
