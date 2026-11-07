"""weights_list and weights_delete (Plan 12 Task 23; G26, G28)."""

from sqlalchemy import func, select

from app.features.weights.models import WeightLog
from tests.api.weights.conftest import ACC_A, URL, body


def _err(r) -> dict:
    return r.json()["error"]


async def test_default_90_days(client, consented, seed_weights):
    await seed_weights(
        [("2026-08-08", 85), ("2026-08-09", 84), ("2026-09-01", 82), ("2026-11-07", 80)]
    )
    r = await client.get(URL)
    assert r.status_code == 200, r.text
    items = r.json()["items"]
    # 90 local days ending 2026-11-07 start on 2026-08-10; oldest first
    assert [i["date"] for i in items] == ["2026-09-01", "2026-11-07"]
    assert [i["weight_kg"] for i in items] == [82.0, 80.0] and r.json()["numbers_hidden"] is False
    assert items[0]["source"] == "manual" and items[0]["numbers_hidden"] is False


async def test_explicit_range(client, consented, seed_weights):
    await seed_weights([("2026-08-08", 85), ("2026-09-01", 82), ("2026-11-07", 80)])
    r = await client.get(URL, params={"from": "2026-08-01", "to": "2026-09-01"})
    assert [i["date"] for i in r.json()["items"]] == ["2026-08-08", "2026-09-01"]


async def test_range_too_long(client, consented):
    r = await client.get(URL, params={"from": "2025-01-01", "to": "2026-11-07"})
    assert r.status_code == 422 and _err(r)["code"] == "date_range_too_long"
    ok = await client.get(URL, params={"from": "2025-10-03", "to": "2026-11-07"})  # 400 days
    assert ok.status_code == 200


async def test_delete_latest_restores_previous_weight(client, consented, db_session):
    from app.features.members import service as members_service

    member = await members_service.get_or_create_primary(db_session, ACC_A)
    for day, kg in (("2026-11-05", 80), ("2026-11-06", 79.5), ("2026-11-07", 79)):
        assert (await client.put(f"{URL}/{day}", json=body(kg))).status_code == 200
    assert member.weight_kg == 79
    assert (await client.delete(f"{URL}/2026-11-07")).status_code == 204
    assert member.weight_kg == 79.5
    assert (await client.delete(f"{URL}/2026-11-05")).status_code == 204  # not the latest
    assert member.weight_kg == 79.5


async def test_delete_last_row_keeps_member_weight(client, consented, db_session):
    from app.features.members import service as members_service

    member = await members_service.get_or_create_primary(db_session, ACC_A)
    assert (await client.put(f"{URL}/2026-11-07", json=body(79))).status_code == 200
    assert (await client.delete(f"{URL}/2026-11-07")).status_code == 204
    assert member.weight_kg == 79  # unchanged: the profile keeps the last known weight
    assert await db_session.scalar(select(func.count()).select_from(WeightLog)) == 0


async def test_delete_404(client, consented):
    r = await client.delete(f"{URL}/2026-11-07")
    assert r.status_code == 404 and _err(r)["code"] == "weight_not_found"
