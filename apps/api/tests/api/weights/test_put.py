"""weights_put (Plan 12 Task 23; G26, G28)."""

from datetime import date
from decimal import Decimal
from uuid import uuid4

from sqlalchemy import func, select

from app.features.diary.models import DiaryDay
from app.features.members import service as members_service
from app.features.weights import store
from app.features.weights.models import WeightLog
from tests.api.weights.conftest import ACC_A, ACC_B, G5_SETTINGS, URL, body

DAY = "2026-11-07"


def _err(r) -> dict:
    return r.json()["error"]


async def test_put_creates_then_replaces_200(client, consented, db_session):
    first = await client.put(f"{URL}/{DAY}", json=body(80.4))
    assert first.status_code == 200, first.text
    j = first.json()
    assert j["date"] == DAY and j["weight_kg"] == 80.4 and j["source"] == "manual"
    assert j["numbers_hidden"] is False and j["client_id"] is None
    second = await client.put(f"{URL}/{DAY}", json=body(80.1))
    assert second.status_code == 200 and second.json()["weight_kg"] == 80.1
    n = await db_session.scalar(select(func.count()).select_from(WeightLog))
    assert n == 1


async def test_two_decimal_places_half_up(client, consented):
    r = await client.put(f"{URL}/{DAY}", json=body(80.125))
    assert r.json()["weight_kg"] == 80.13


async def test_sets_member_weight_when_latest(client, consented, db_session):
    member = await members_service.get_or_create_primary(db_session, ACC_A)
    assert (await client.put(f"{URL}/2026-11-05", json=body(80))).status_code == 200
    assert member.weight_kg == 80
    assert (await client.put(f"{URL}/{DAY}", json=body(79.2))).status_code == 200
    assert member.weight_kg == 79.2


async def test_older_date_keeps_member_weight(client, consented, db_session):
    member = await members_service.get_or_create_primary(db_session, ACC_A)
    assert (await client.put(f"{URL}/{DAY}", json=body(79.2))).status_code == 200
    assert (await client.put(f"{URL}/2026-11-05", json=body(80))).status_code == 200
    assert member.weight_kg == 79.2


async def test_out_of_range_422(client, consented):
    for kg in (1.99, 0, -3, 300.01, 1000):
        r = await client.put(f"{URL}/{DAY}", json=body(kg))
        assert r.status_code == 422 and _err(r)["code"] == "weight_out_of_range", kg
    for kg in (2, 300):
        ok = await client.put(f"{URL}/{DAY}", json=body(kg, confirm_unusual=True))
        assert ok.status_code == 200, kg


async def test_needs_confirm_plausible_and_daily_change(client, consented):
    low = await client.put(f"{URL}/{DAY}", json=body(25))
    assert low.status_code == 422 and _err(low)["code"] == "weight_needs_confirm"
    assert _err(low)["details"] == {"previous": None, "previous_date": None}
    assert (await client.put(f"{URL}/2026-11-05", json=body(78))).status_code == 200
    jump = await client.put(f"{URL}/2026-11-06", json=body(82))  # 4 kg in one day
    assert jump.status_code == 422 and _err(jump)["code"] == "weight_needs_confirm"
    assert _err(jump)["details"] == {"previous": 78.0, "previous_date": "2026-11-05"}
    # 2 kg a day over two days is allowed (4 kg <= 2.0 x 2)
    assert (await client.put(f"{URL}/{DAY}", json=body(82))).status_code == 200


async def test_confirm_unusual_saves(client, consented):
    assert (await client.put(f"{URL}/2026-11-05", json=body(78))).status_code == 200
    r = await client.put(f"{URL}/2026-11-06", json=body(82, confirm_unusual=True))
    assert r.status_code == 200 and r.json()["weight_kg"] == 82


async def test_needs_confirm_hides_previous(client, g5, put_settings_row, db_session):
    await put_settings_row(g5, numbers_display="hide_all")
    assert (await client.put(f"{URL}/2026-11-05", json=body(78))).status_code == 200
    r = await client.put(f"{URL}/2026-11-06", json=body(90))
    assert r.status_code == 422 and _err(r)["code"] == "weight_needs_confirm"
    assert _err(r)["details"]["previous"] is None
    assert _err(r)["details"]["previous_date"] == "2026-11-05"
    assert "78" not in r.text


async def test_future_and_too_old(client, consented):
    r = await client.put(f"{URL}/2026-11-08", json=body(80))
    assert r.status_code == 422 and _err(r)["code"] == "date_in_future"
    old = await client.put(f"{URL}/2025-09-01", json=body(80))  # 432 days back
    assert old.status_code == 422 and _err(old)["code"] == "date_too_old"
    edge = await client.put(f"{URL}/2025-10-03", json=body(80))  # exactly 400 days back
    assert edge.status_code == 200


async def test_client_id_retry(client, consented, db_session):
    cid = str(uuid4())
    first = await client.put(f"{URL}/{DAY}", json=body(80, client_id=cid))
    assert first.status_code == 200
    retry = await client.put(f"{URL}/{DAY}", json=body(75, client_id=cid))
    assert retry.status_code == 200 and retry.json()["weight_kg"] == 80  # the stored row
    n = await db_session.scalar(select(func.count()).select_from(WeightLog))
    assert n == 1


async def test_client_id_race_returns_the_winner(client, consented, db_session, monkeypatch):
    """A concurrent put with the same client_id inserted between the existence check and the
    insert: the unique key stops the second row and the stored one is returned."""
    cid = uuid4()
    member = await members_service.get_or_create_primary(db_session, ACC_A)
    from app.core import time as core_time
    from app.features.weights import service

    real = service._by_client_id
    calls = {"n": 0}

    async def racing(session, account_id, client_id):
        calls["n"] += 1
        if calls["n"] == 1:
            await store.upsert_weigh_in(
                session, member, date(2026, 11, 6), 79, core_time.now_utc(), cid
            )
            return None  # this request did not see it yet
        return await real(session, account_id, client_id)

    monkeypatch.setattr(service, "_by_client_id", racing)
    r = await client.put(f"{URL}/{DAY}", json=body(80, client_id=str(cid)))
    assert r.status_code == 200, r.text
    assert r.json()["date"] == "2026-11-06" and r.json()["weight_kg"] == 79
    n = await db_session.scalar(select(func.count()).select_from(WeightLog))
    assert n == 1


async def test_recomputes_today_targets(client, g5, db_session):
    assert (await client.put("/v1/targets/settings", json=G5_SETTINGS)).status_code == 200
    before = (await db_session.scalars(select(DiaryDay))).one()
    assert Decimal(before.inputs["weight_kg_used"]) == 80
    assert (await client.put(f"{URL}/{DAY}", json=body(78.5))).status_code == 200
    after = (
        await db_session.scalars(select(DiaryDay).execution_options(populate_existing=True))
    ).one()
    assert (
        Decimal(after.inputs["weight_kg_used"]) == Decimal("78.5")
        and after.inputs["weight_source"] == "latest"
    )


async def test_rate_limited(client, app, consented, monkeypatch):
    monkeypatch.setattr(app.state.settings, "rate_limit_weights_per_day", 2)
    for d in ("2026-11-05", "2026-11-06"):
        assert (await client.put(f"{URL}/{d}", json=body(80))).status_code == 200
    r = await client.put(f"{URL}/{DAY}", json=body(80))
    assert r.status_code == 429 and _err(r)["code"] == "rate_limited"
    assert (await client.get(URL)).status_code == 200  # reads are not limited


async def test_another_accounts_member_is_404(client, consented, grant, add_member):
    await grant(ACC_B)
    other = await add_member(ACC_B, name="X")
    r = await client.put(f"{URL}/{DAY}", json=body(80, member_id=str(other.id)))
    assert r.status_code == 404 and _err(r)["code"] == "member_not_found"


async def test_non_primary_member_needs_family(client, consented, add_member):
    other = await add_member(ACC_A, name="Dad")
    r = await client.put(f"{URL}/{DAY}", json=body(80, member_id=str(other.id)))
    assert r.status_code == 422 and _err(r)["code"] == "diary_member_not_enabled"


async def test_edit_keeps_client_id_so_a_late_retry_is_ignored(client, consented, db_session):
    cid = str(uuid4())
    assert (await client.put(f"{URL}/{DAY}", json=body(80, client_id=cid))).status_code == 200
    # a later edit of the same day without a client_id (online edit, or a member update)
    edit = await client.put(f"{URL}/{DAY}", json=body(79.0))
    assert edit.status_code == 200 and edit.json()["client_id"] == cid
    # the first put is retried late by the offline queue: the stored (edited) value stays
    retry = await client.put(f"{URL}/{DAY}", json=body(80, client_id=cid))
    assert retry.status_code == 200 and retry.json()["weight_kg"] == 79.0
    stored = await db_session.scalar(select(WeightLog))
    assert float(stored.weight_kg) == 79.0


async def test_member_update_keeps_client_id(client, consented, db_session):
    cid = uuid4()
    member = await members_service.get_or_create_primary(db_session, ACC_A)
    assert (await client.put(f"{URL}/{DAY}", json=body(80, client_id=str(cid)))).status_code == 200
    r = await client.patch(f"/v1/members/{member.id}", json={"weight_kg": 78.5})
    assert r.status_code == 200, r.text
    row = await db_session.scalar(select(WeightLog).execution_options(populate_existing=True))
    assert row.client_id == cid and float(row.weight_kg) == 78.5
