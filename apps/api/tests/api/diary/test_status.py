"""PUT /v1/diary/days/{date}/status (Plan 11 Task 7)."""

from sqlalchemy import select

from app.features.diary.models import DiaryDay


def _url(day: str) -> str:
    return f"/v1/diary/days/{day}/status"


async def test_mark_partial_today(client, g1, db_session):
    r = await client.put(_url("2026-11-07"), json={"partial_logged": True})
    assert r.status_code == 200 and r.json() == {"date": "2026-11-07", "partial_logged": True}
    day = (await client.get("/v1/diary/day")).json()
    assert day["partial_logged"] is True
    week = (await client.get("/v1/diary/week")).json()
    assert week["days"][-1]["partial_logged"] is True
    cleared = await client.put(_url("2026-11-07"), json={"partial_logged": False})
    assert cleared.json()["partial_logged"] is False
    assert (await client.get("/v1/diary/day")).json()["partial_logged"] is False


async def test_mark_partial_past_without_row(client, g1, db_session):
    r = await client.put(_url("2026-11-03"), json={"partial_logged": True})
    assert r.status_code == 200 and r.json()["partial_logged"] is True
    row = (
        await db_session.scalars(
            select(DiaryDay)
            .where(DiaryDay.member_id == g1)
            .execution_options(populate_existing=True)
        )
    ).one()
    assert (str(row.local_date), row.status, row.energy_kcal) == ("2026-11-03", "none", None)
    day = (await client.get("/v1/diary/day", params={"date": "2026-11-03"})).json()
    assert day["partial_logged"] is True and day["targets_status"] == "none"


async def test_status_future_422(client, g1):
    r = await client.put(_url("2026-11-08"), json={"partial_logged": True})
    assert r.status_code == 422 and r.json()["error"]["code"] == "date_in_future"


async def test_status_rate_limited(client, g1, app, monkeypatch):
    monkeypatch.setattr(app.state.settings, "rate_limit_diary_settings_per_day", 2)
    for _ in range(2):
        assert (
            await client.put(_url("2026-11-07"), json={"partial_logged": True})
        ).status_code == 200
    r = await client.put(_url("2026-11-07"), json={"partial_logged": True})
    assert r.status_code == 429 and r.json()["error"]["code"] == "rate_limited"


async def test_status_foreign_member_404(client, g1, add_member):
    from tests.api.diary.conftest import ACC_B

    foreign = await add_member(ACC_B)
    r = await client.put(
        _url("2026-11-07"), json={"member_id": str(foreign.id), "partial_logged": True}
    )
    assert r.status_code == 404 and r.json()["error"]["code"] == "member_not_found"
