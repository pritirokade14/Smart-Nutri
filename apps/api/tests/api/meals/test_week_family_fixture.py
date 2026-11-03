"""The shared week_family fixture through the real endpoint (Plan 6 T7).

Inserts the rows of packages/test-fixtures/meals/week_family.json (built by
scripts/export_meal_fixtures.py, exactly as the API stores them) and checks that
GET /v1/meals/summary returns meals/expected/week_family.dad_diabetic.json byte for byte.
"""

import json

from app.core.security import AccountContext
from app.features.me.service import ensure_account
from scripts.export_meal_fixtures import (
    MEALS,
    SHARE,
    WEEK_FAMILY_ACCOUNT,
    load_week_family,
)


async def _seed(db_session):
    family = load_week_family()
    await ensure_account(db_session, AccountContext(WEEK_FAMILY_ACCOUNT, None))
    db_session.add_all(list(family.members.values()))
    db_session.add_all(family.products)
    await db_session.flush()
    db_session.add_all(family.meals)
    await db_session.flush()
    return family


async def test_week_family_summary_matches_expected(client, db_session, login):
    family = await _seed(db_session)
    login(WEEK_FAMILY_ACCOUNT)
    dad = family.members["dad"]
    r = await client.get(
        "/v1/meals/summary",
        params={"member_id": str(dad.id), "period": "week", "date": str(family.end_date)},
    )
    assert r.status_code == 200
    expected = json.loads(
        (MEALS / "expected" / "week_family.dad_diabetic.json").read_text(encoding="utf-8")
    )
    assert r.json() == expected
    # The fixture covers what the clients must render.
    days = {d["date"]: d for d in expected["days"]}
    assert days["2026-10-31"]["bands"]["sugar_g"] == "over"
    assert days["2026-11-01"]["incomplete"]["sugars_g"] is True
    assert expected["incomplete"]["sugars_g"] is True and expected["bands"]["sugar_g"] == "unknown"
    assert days["2026-11-03"]["items"] == 2  # 23:30 IST counts on 3 Nov


async def test_week_family_logged_count_matches_share_fixture(client, db_session, login):
    family = await _seed(db_session)
    login(WEEK_FAMILY_ACCOUNT)
    r = await client.get("/v1/meals/week_counts", params={"date": str(family.end_date)})
    share = json.loads((SHARE / "share_weekly.week_family.json").read_text(encoding="utf-8"))
    assert r.json()["logged"] == share["input"]["logged"]
