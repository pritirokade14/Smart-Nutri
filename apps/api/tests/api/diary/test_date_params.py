"""Date query/path params sent as an ISO date-time (the Android client does this).

Midnight date-times ("2026-11-07T00:00:00.000Z", "2026-11-07 00:00:00.000Z") mean the calendar
date in the string, with no zone conversion. A date-time that is not midnight is a 422, so the
clients send a plain YYYY-MM-DD (documented in the api report).
"""

import pytest

from tests.api.diary.conftest import G1_SETTINGS, YESTERDAY

S = "/v1/targets/settings"
FORMS = ["2026-11-06T00:00:00.000Z", "2026-11-06 00:00:00.000Z", "2026-11-06"]


@pytest.mark.parametrize("value", FORMS)
async def test_day_date_param_forms(client, g1, slot_ids, value):
    assert (await client.put(S, json=G1_SETTINGS)).status_code == 200
    r = await client.get("/v1/diary/day", params={"date": value})
    assert r.status_code == 200, r.text
    assert r.json()["date"] == YESTERDAY


@pytest.mark.parametrize("value", FORMS)
async def test_week_end_param_forms(client, g1, slot_ids, value):
    assert (await client.put(S, json=G1_SETTINGS)).status_code == 200
    r = await client.get("/v1/diary/week", params={"end": value})
    assert r.status_code == 200, r.text
    assert r.json()["end"] == YESTERDAY


@pytest.mark.parametrize("value", FORMS)
async def test_meals_local_date_param_forms(client, g1, slot_ids, value):
    quick = {"quick": {"energy_kcal": 200}, "local_date": YESTERDAY}
    assert (await client.post("/v1/meals", json=quick)).status_code == 201
    r = await client.get("/v1/meals", params={"local_date": value})
    assert r.status_code == 200, r.text
    assert len(r.json()) == 1


@pytest.mark.parametrize("value", FORMS[:2])
async def test_summary_date_param_forms(client, g1, slot_ids, value):
    r = await client.get("/v1/meals/summary", params={"member_id": str(g1), "date": value})
    assert r.status_code == 200, r.text


async def test_non_midnight_datetime_is_422(client, g1, slot_ids):
    r = await client.get("/v1/diary/day", params={"date": "2026-11-06T18:30:00.000Z"})
    assert r.status_code == 422
