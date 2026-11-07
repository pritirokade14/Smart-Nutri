"""The trend weight in the daily guides (Plan 12 Task 23; G25, G26)."""

from sqlalchemy import func, select

from app.features.members import service as members_service
from app.features.weights.models import WeightLog
from tests.api.weights.conftest import ACC_A, G5_SETTINGS, URL, body

TARGETS = "/v1/targets"
S = f"{TARGETS}/settings"


def _t(r) -> dict:
    assert r.status_code == 200, r.text
    return r.json()


async def test_targets_use_trend_weight_after_three(client, g5, seed_weights):
    # Member weight 80 kg; three weigh-ins of 76.2 give the g5_taper fixture's numbers (1940).
    assert (await client.put(S, json=G5_SETTINGS)).status_code == 200
    await seed_weights([("2026-11-05", 76.2), ("2026-11-06", 76.2), ("2026-11-07", 76.2)])
    t = _t(await client.get(TARGETS))
    assert t["energy_kcal"] == 1940 and "taper_active" in t["flags"]
    assert t["explanation"]["weight_source"] == "trend"
    assert t["explanation"]["weight_kg_used"] == 76.2


async def test_two_weigh_ins_use_latest(client, g5, seed_weights):
    assert (await client.put(S, json=G5_SETTINGS)).status_code == 200
    await seed_weights([("2026-11-06", 76.2), ("2026-11-07", 76.2)])
    t = _t(await client.get(TARGETS))
    assert t["explanation"]["weight_source"] == "latest"
    assert t["explanation"]["weight_kg_used"] == 80.0  # members.weight_kg
    assert t["energy_kcal"] != 1940


async def test_no_weight_log_uses_the_profile_weight(client, g5):
    assert (await client.put(S, json=G5_SETTINGS)).status_code == 200
    t = _t(await client.get(TARGETS))
    assert t["explanation"]["weight_source"] == "latest"


async def test_targets_ignore_outlier(client, g5, seed_weights):
    assert (await client.put(S, json=G5_SETTINGS)).status_code == 200
    # 90 kg is more than 3 % from the 76.2 trend: left out of it
    await seed_weights(
        [("2026-11-04", 76.2), ("2026-11-05", 76.2), ("2026-11-06", 76.2), ("2026-11-07", 90)]
    )
    t = _t(await client.get(TARGETS))
    assert t["explanation"]["weight_source"] == "trend"
    assert t["explanation"]["weight_kg_used"] == 76.2 and t["energy_kcal"] == 1940


async def test_weight_source_is_hidden_with_the_numbers(client, g5, seed_weights):
    assert (await client.put(S, json=G5_SETTINGS)).status_code == 200
    await seed_weights([("2026-11-05", 76.2), ("2026-11-06", 76.2), ("2026-11-07", 76.2)])
    assert (
        await client.put(f"{TARGETS}/display", json={"numbers_display": "hide_all"})
    ).status_code == 200
    t = _t(await client.get(TARGETS))
    assert t["explanation"]["weight_kg_used"] is None and t["explanation"]["weight_source"] is None


async def test_preview_keeps_the_typed_overrides(client, g5, seed_weights):
    await seed_weights([("2026-11-05", 76.2), ("2026-11-06", 76.2), ("2026-11-07", 76.2)])
    r = await client.post(f"{TARGETS}/preview", json=G5_SETTINGS | {"body": {"weight_kg": 90}})
    t = _t(r)
    assert t["explanation"]["weight_kg_used"] == 90.0 and t["explanation"]["weight_source"] is None


async def test_member_update_upserts_weigh_in(client, consented, db_session):
    member = await members_service.get_or_create_primary(db_session, ACC_A)
    r = await client.patch(f"/v1/members/{member.id}", json={"weight_kg": 77.5})
    assert r.status_code == 200, r.text
    rows = list(await db_session.scalars(select(WeightLog)))
    assert [(str(x.local_date), float(x.weight_kg), x.source) for x in rows] == [
        ("2026-11-07", 77.5, "manual")
    ]
    # the same value again, and an unrelated edit, add nothing
    await client.patch(f"/v1/members/{member.id}", json={"weight_kg": 77.5})
    await client.patch(f"/v1/members/{member.id}", json={"name": "Asha"})
    assert await db_session.scalar(select(func.count()).select_from(WeightLog)) == 1
    # a new value replaces today's row (one per day)
    await client.patch(f"/v1/members/{member.id}", json={"weight_kg": 77.0})
    rows = list(
        await db_session.scalars(select(WeightLog).execution_options(populate_existing=True))
    )
    assert [float(x.weight_kg) for x in rows] == [77.0]
    # clearing the weight keeps the log
    await client.patch(f"/v1/members/{member.id}", json={"weight_kg": None})
    assert await db_session.scalar(select(func.count()).select_from(WeightLog)) == 1


async def test_non_primary_member_update_logs_nothing(client, consented, add_member, db_session):
    other = await add_member(ACC_A, name="Dad")
    r = await client.patch(f"/v1/members/{other.id}", json={"weight_kg": 70})
    assert r.status_code == 200, r.text
    assert await db_session.scalar(select(func.count()).select_from(WeightLog)) == 0


async def test_frozen_past_day_unchanged_by_new_weigh_in(client, g5, clock):
    assert (await client.put(S, json=G5_SETTINGS)).status_code == 200
    before = _t(await client.get(TARGETS))  # freezes 2026-11-07 with the 80 kg profile weight
    clock.set("2026-11-08T06:30:00+00:00")
    for day in ("2026-11-06", "2026-11-07", "2026-11-08"):
        assert (await client.put(f"{URL}/{day}", json=body(70))).status_code == 200
    past = _t(await client.get(TARGETS, params={"date": "2026-11-07"}))
    assert past["energy_kcal"] == before["energy_kcal"]
    assert past["explanation"]["weight_kg_used"] == 80.0
    assert past["explanation"]["weight_source"] == "latest"
