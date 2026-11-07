"""The diary needs only `terms`; the targets part needs `health_data` (Plan 11 Task 7;
Rulings E5 and E14; spec 6.6). The real consent gate runs in this folder."""

from datetime import date
from uuid import uuid4

from sqlalchemy import func, select, text

from app.features.diary.models import DiaryDay
from tests.api.diary.conftest import ACC_A, ACC_B, TODAY

DAY = "/v1/diary/day"
WEEK = "/v1/diary/week"


async def _terms_only(grant, login):
    await grant(ACC_A, ("terms",))
    login(ACC_A)


async def test_day_without_health_data_has_entries_and_consent_required(
    client, grant, login, db_session
):
    await _terms_only(grant, login)
    assert (await client.post("/v1/meals", json={"quick": {"energy_kcal": 250}})).status_code == 201
    r = await client.get(DAY)
    assert r.status_code == 200, r.text
    j = r.json()
    assert j["targets"] is None and j["targets_status"] == "consent_required"
    assert j["remaining"] is None and j["progress"] is None
    assert j["totals"]["energy_kcal"] == 250.0
    assert sum(len(s["entries"]) for s in j["slots"]) == 1
    # No frozen row is computed or written without health_data.
    n = await db_session.scalar(select(func.count()).select_from(DiaryDay))
    assert n == 0


async def test_week_without_health_data(client, grant, login, db_session):
    await _terms_only(grant, login)
    await client.post("/v1/meals", json={"quick": {"energy_kcal": 250}})
    r = await client.get(WEEK)
    assert r.status_code == 200, r.text
    j = r.json()
    assert len(j["days"]) == 7 and all(t["targets"] is None for t in j["days"])
    assert all(t["progress"] is None for t in j["days"])
    assert j["days"][-1]["items"] == 1 and j["averaged_days"] == 1
    assert await db_session.scalar(select(func.count()).select_from(DiaryDay)) == 0


async def test_diary_routes_need_terms(client, grant, login):
    await grant(ACC_B, ("health_data", "ai_processing"))  # everything but terms
    login(ACC_B)
    member = uuid4()
    for method, url, body in (
        ("GET", DAY, None),
        ("GET", WEEK, None),
        ("GET", "/v1/diary/recents", None),
        ("PUT", f"/v1/diary/days/{TODAY}/status", {"partial_logged": True}),
        ("GET", "/v1/meal-slots", None),
        ("POST", "/v1/meals/copy", None),
    ):
        r = await client.request(
            method, url, json=body, params={"member_id": str(member)} if method == "GET" else None
        )
        assert r.status_code == 403, (method, url)
        assert r.json()["error"]["details"]["purposes"] == ["terms"], url


async def test_gate_before_rate_limit(client, grant, login, db_session, app, monkeypatch):
    monkeypatch.setattr(app.state.settings, "rate_limit_diary_settings_per_day", 1)
    await grant(ACC_B, ("health_data",))
    login(ACC_B)
    for _ in range(3):
        r = await client.put(f"/v1/diary/days/{TODAY}/status", json={"partial_logged": True})
        assert r.status_code == 403  # a refused call never turns into a 429
    used = await db_session.scalar(
        text("select count(*) from rate_limit_counters where key = :k"), {"k": f"acct:{ACC_B}"}
    )
    assert used == 0


async def test_copy_needs_only_terms(client, grant, login):
    await _terms_only(grant, login)
    await client.post("/v1/meals", json={"quick": {"energy_kcal": 250}, "local_date": "2026-11-06"})
    r = await client.post(
        "/v1/meals/copy",
        json={"from_date": "2026-11-06", "to_date": "2026-11-07", "client_id": str(uuid4())},
    )
    assert r.status_code == 201, r.text
    assert date.fromisoformat(r.json()["created"][0]["local_date"]) == date(2026, 11, 7)
