"""Frozen daily targets (Plan 11 Task 3; Ruling E5; ADR 0023)."""

from datetime import date

from sqlalchemy import func, select

from app.features.diary import days
from app.features.diary.models import DiaryDay
from app.features.members import service as members_service
from tests.api.diary.conftest import (
    ACC_A,
    G1_SETTINGS,
    G2_SETTINGS,
    TODAY,
    YESTERDAY,
)

URL = "/v1/targets"
S = f"{URL}/settings"


async def _rows(db_session, member) -> dict[str, DiaryDay]:
    rows = await db_session.scalars(
        select(DiaryDay)
        .where(DiaryDay.member_id == member)
        .execution_options(populate_existing=True)
    )
    return {str(r.local_date): r for r in rows}


async def test_today_row_created_on_read(client, g1, db_session):
    await client.put(S, json=G1_SETTINGS)
    await db_session.execute(DiaryDay.__table__.delete())  # drop what the PUT wrote
    assert await _rows(db_session, g1) == {}
    r = await client.get(URL)
    assert r.json()["energy_kcal"] == 2760
    rows = await _rows(db_session, g1)
    assert list(rows) == ["2026-11-07"]
    assert rows["2026-11-07"].status == "ready" and rows["2026-11-07"].energy_kcal == 2760


async def test_settings_change_recomputes_today_not_yesterday(
    client, g2, db_session, seed_day, set_primary
):
    # Yesterday froze with the G1 settings on the G1 body ...
    member = await members_service.get_or_create_primary(db_session, ACC_A)
    await set_primary(birth_year=1997, sex="male", height_cm=175, weight_kg=70, goal="build_muscle")
    await seed_day(member, YESTERDAY, G1_SETTINGS)
    # ... today the user switches to the G2 body and settings.
    await set_primary(
        birth_year=1985, sex="female", height_cm=160, weight_kg=80, goal="weight_loss"
    )
    assert (await client.put(S, json=G2_SETTINGS)).json()["energy_kcal"] == 1540
    rows = await _rows(db_session, g2)
    assert rows[YESTERDAY].energy_kcal == 2760
    assert rows["2026-11-07"].energy_kcal == 1540
    past = (await client.get(URL, params={"date": YESTERDAY})).json()
    assert past["energy_kcal"] == 2760 and past["rate_options"] == []


async def test_weight_change_recomputes_today_only(client, g1, db_session, seed_day, set_primary):
    member = await members_service.get_or_create_primary(db_session, ACC_A)
    await client.put(S, json=G1_SETTINGS)
    await seed_day(member, YESTERDAY, G1_SETTINGS)
    before = (await client.get(URL)).json()["energy_kcal"]
    await set_primary(weight_kg=90)
    after = (await client.get(URL)).json()
    assert after["energy_kcal"] != before and after["explanation"]["weight_kg_used"] == 90.0
    rows = await _rows(db_session, g1)
    assert rows[YESTERDAY].energy_kcal == 2760  # untouched
    assert rows["2026-11-07"].energy_kcal == after["energy_kcal"]


async def test_past_day_without_row_is_none_and_not_written(client, g1, db_session):
    await client.put(S, json=G1_SETTINGS)
    t = (await client.get(URL, params={"date": "2026-11-05"})).json()
    assert t["status"] == "none" and t["energy_kcal"] is None
    assert "2026-11-05" not in await _rows(db_session, g1)


async def test_delete_settings_makes_today_none_keeps_past(client, g1, db_session, seed_day):
    member = await members_service.get_or_create_primary(db_session, ACC_A)
    await client.put(S, json=G1_SETTINGS)
    await seed_day(member, YESTERDAY, G1_SETTINGS)
    assert (await client.delete(S)).status_code == 204
    rows = await _rows(db_session, g1)
    assert rows["2026-11-07"].status == "none" and rows["2026-11-07"].energy_kcal is None
    assert rows[YESTERDAY].status == "ready" and rows[YESTERDAY].energy_kcal == 2760
    assert (await client.get(URL)).json()["status"] == "none"


async def test_future_date_422(client, g1):
    r = await client.get(URL, params={"date": "2026-11-08"})
    assert r.status_code == 422 and r.json()["error"]["code"] == "date_in_future"


async def test_no_row_written_without_health_data(db_session, grant):
    """The service computes a row only while `health_data` is active: without it, a marked
    day is a `none` row with no numbers, even when settings are stored."""
    from app.features.targets.models import DiaryGoalSettings

    await grant(ACC_A, ("terms",))  # no health_data

    member = await members_service.get_or_create_primary(db_session, ACC_A)
    db_session.add(
        DiaryGoalSettings(
            member_id=member.id, account_id=ACC_A, direction="gain", activity_level="moderate"
        )
    )
    await db_session.flush()
    row = await days.set_partial(db_session, member, TODAY, True, today=TODAY)
    assert row.status == "none" and row.energy_kcal is None and row.partial_logged is True


async def test_partial_on_past_day_inserts_none_row(db_session, g1):
    member = await members_service.get_or_create_primary(db_session, ACC_A)
    row = await days.set_partial(db_session, member, date(2026, 11, 3), True, today=TODAY)
    assert row.status == "none" and row.partial_logged is True and row.energy_kcal is None
    again = await days.set_partial(db_session, member, date(2026, 11, 3), False, today=TODAY)
    assert again.partial_logged is False
    n = await db_session.scalar(
        select(func.count()).select_from(DiaryDay).where(DiaryDay.member_id == member.id)
    )
    assert n == 1


async def test_set_partial_future_is_422(db_session, g1):
    import pytest

    from app.core.errors import ApiError

    member = await members_service.get_or_create_primary(db_session, ACC_A)
    with pytest.raises(ApiError) as exc:
        await days.set_partial(db_session, member, date(2026, 11, 8), True, today=TODAY)
    assert exc.value.code == "date_in_future"


async def test_today_follows_account_zone(client, g1, clock):
    await client.put(S, json=G1_SETTINGS)
    assert (
        await client.put("/v1/me/timezone", json={"timezone": "America/New_York"})
    ).status_code == 200
    clock.set("2026-11-08T03:00:00+00:00")  # 22:00 on 7 Nov in New York, 08:30 on 8 Nov in IST
    t = (await client.get(URL)).json()
    assert t["date"] == "2026-11-07" and t["status"] == "ready"
    r = await client.get(URL, params={"date": "2026-11-08"})
    assert r.status_code == 422
