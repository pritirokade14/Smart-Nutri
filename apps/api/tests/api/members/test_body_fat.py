"""Plan 10 Task 3: `members.body_fat_pct` (Q10, Ruling D3).

Optional, 3-70, health data. `null` on PATCH means "unchanged" (the generated Dart client sends
every unset field as null); `clear_body_fat_pct: true` clears it, and clearing is never gated.
"""

import pytest
from sqlalchemy import select

from app.features.members.models import Member
from tests.api.members.conftest import ACC_B

URL = "/v1/members"
ADULT = {"name": "Dev", "relation": "other", "birth_year": 1990}


def _err(r) -> dict:
    return r.json()["error"]


async def _row(db_session, member_id) -> Member:
    return await db_session.scalar(
        select(Member).where(Member.id == member_id).execution_options(populate_existing=True)
    )


@pytest.mark.parametrize("value", [3, 70, 15.5])
async def test_body_fat_accepts_bounds(client, consented, value):
    r = await client.post(URL, json={**ADULT, "body_fat_pct": value})
    assert r.status_code == 201, r.json()
    assert r.json()["body_fat_pct"] == value
    listed = {m["id"]: m for m in (await client.get(URL)).json()}
    assert listed[r.json()["id"]]["body_fat_pct"] == value


@pytest.mark.parametrize("value", [2.9, 70.1, 0, -1, 100])
async def test_body_fat_refuses_out_of_range(client, consented, value):
    r = await client.post(URL, json={**ADULT, "body_fat_pct": value})
    assert r.status_code == 422
    assert _err(r)["code"] == "body_fat_out_of_range"
    assert _err(r)["message_key"] == "error.body_fat_out_of_range"
    assert _err(r)["details"] == {"min": 3, "max": 70}
    created = (await client.post(URL, json=ADULT)).json()
    r = await client.patch(f"{URL}/{created['id']}", json={"body_fat_pct": value})
    assert r.status_code == 422 and _err(r)["code"] == "body_fat_out_of_range"


async def test_body_fat_on_create(client, consented, db_session):
    r = await client.post(URL, json={**ADULT, "body_fat_pct": 22})
    assert r.status_code == 201
    row = await _row(db_session, r.json()["id"])
    assert float(row.body_fat_pct) == 22.0
    r = await client.post(URL, json={**ADULT, "name": "NoBF"})
    assert r.json()["body_fat_pct"] is None  # blank is unknown, never 0


async def test_null_body_fat_on_patch_leaves_value(client, consented, db_session):
    created = (await client.post(URL, json={**ADULT, "body_fat_pct": 15})).json()
    r = await client.patch(f"{URL}/{created['id']}", json={"name": "A", "body_fat_pct": None})
    assert r.status_code == 200
    assert r.json()["body_fat_pct"] == 15
    assert float((await _row(db_session, created["id"])).body_fat_pct) == 15.0


async def test_clear_body_fat_pct_clears_without_health_data(client, login, add_member, db_session):
    member = await add_member(ACC_B, body_fat_pct=18)  # no consent granted at all
    login(ACC_B)
    r = await client.patch(f"{URL}/{member.id}", json={"clear_body_fat_pct": True})
    assert r.status_code == 200, r.json()
    assert r.json()["body_fat_pct"] is None
    assert (await _row(db_session, member.id)).body_fat_pct is None


async def test_clear_flag_false_changes_nothing(client, consented):
    created = (await client.post(URL, json={**ADULT, "body_fat_pct": 15})).json()
    r = await client.patch(f"{URL}/{created['id']}", json={"clear_body_fat_pct": False})
    assert r.status_code == 200 and r.json()["body_fat_pct"] == 15


async def test_body_fat_write_needs_health_data(client, login, add_member):
    member = await add_member(ACC_B)
    login(ACC_B)
    r = await client.patch(f"{URL}/{member.id}", json={"body_fat_pct": 20})
    assert r.status_code == 403
    assert _err(r)["code"] == "consent_required"
    assert _err(r)["details"]["purpose"] == "health_data"
    r = await client.post(URL, json={**ADULT, "body_fat_pct": 20})
    assert r.status_code == 403 and _err(r)["code"] == "consent_required"


async def test_resending_the_stored_body_fat_needs_no_consent(client, login, add_member):
    member = await add_member(ACC_B, body_fat_pct=20)
    login(ACC_B)
    r = await client.patch(f"{URL}/{member.id}", json={"name": "Renamed", "body_fat_pct": 20})
    assert r.status_code == 200 and r.json()["body_fat_pct"] == 20


async def test_value_and_clear_together_is_422(client, consented):
    created = (await client.post(URL, json={**ADULT, "body_fat_pct": 15})).json()
    r = await client.patch(
        f"{URL}/{created['id']}", json={"body_fat_pct": 20, "clear_body_fat_pct": True}
    )
    assert r.status_code == 422
    assert _err(r)["code"] == "validation_error"
    assert _err(r)["details"]["fields"] == ["body.clear_body_fat_pct"]
    assert (await client.get(URL)).json()[-1]["body_fat_pct"] == 15


async def test_body_fat_range_is_checked_before_consent(client, login, add_member):
    # A bad value is a 422 whether or not consent is held (the range check runs first).
    member = await add_member(ACC_B)
    login(ACC_B)
    r = await client.patch(f"{URL}/{member.id}", json={"body_fat_pct": 2.9})
    assert r.status_code == 422 and _err(r)["code"] == "body_fat_out_of_range"
