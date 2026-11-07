"""GET /v1/diary/week (Plan 11 Task 7; Ruling E16)."""

from tests.api.diary.conftest import (
    ACC_A,
    G1_BODY,
    G1_SETTINGS,
    G2_BODY,
    G2_SETTINGS,
)
from tests.api.diary.seeding import load_expected, load_input, normalise, seed_entries

URL = "/v1/diary/week"
S = "/v1/targets/settings"


async def _seed_week(client, db_session, set_primary, seed_day, g1, slot_ids, product_id, stem):
    """Rebuild a week fixture in the database: frozen rows per day (G1 days with the G1 body,
    G2 days with the G2 body), the partial mark, and the entries."""
    from app.features.members import service as members_service

    case = load_input(stem)
    member = await members_service.get_or_create_primary(db_session, ACC_A)
    by_case = {
        "g1_build_muscle": (G1_BODY, G1_SETTINGS),
        "g2_lose_adjusted": (G2_BODY, G2_SETTINGS),
    }
    today = case["as_of"]
    for want in ("g1_build_muscle", "g2_lose_adjusted"):
        body, settings = by_case[want]
        await set_primary(**body)
        for d in case["days"]:
            if d["targets_case"] == want and d["date"] != today:
                await seed_day(member, d["date"], settings, partial_logged=d["partial_logged"])
    # today's row is live: it follows the settings saved last
    last = next(d["targets_case"] for d in case["days"] if d["date"] == today)
    body, settings = by_case[last]
    await set_primary(**body)
    assert (await client.put(S, json=settings)).status_code == 200
    for d in case["days"]:
        seed_entries(
            db_session,
            ACC_A,
            member.id,
            slot_ids,
            d["date"],
            d["entries"],
            case["timezone"],
            product_id,
        )
    await db_session.flush()


async def test_week_matches_golden_week_mixed(
    client, g1, db_session, set_primary, seed_day, slot_ids, product_id, clock
):
    await _seed_week(
        client, db_session, set_primary, seed_day, g1, slot_ids, product_id, "week_mixed"
    )
    r = await client.get(URL)
    assert r.status_code == 200, r.text
    assert normalise(r.json()) == normalise(load_expected("week_mixed"))


async def test_week_frozen_targets_per_day(
    client, g1, db_session, set_primary, seed_day, slot_ids, product_id, clock
):
    await _seed_week(
        client, db_session, set_primary, seed_day, g1, slot_ids, product_id, "week_mixed"
    )
    days = {t["date"]: t for t in (await client.get(URL)).json()["days"]}
    assert days["2026-11-01"]["targets"] == {"energy_kcal": 2760, "protein_g": 112}
    assert days["2026-11-02"]["targets"] == {"energy_kcal": 1540, "protein_g": 71}
    assert days["2026-11-06"]["targets"] is None  # no frozen row: never back-filled


async def test_week_end_default_today(client, g1, clock):
    j = (await client.get(URL)).json()
    assert (j["end"], j["start"], j["today"]) == ("2026-11-07", "2026-11-01", "2026-11-07")
    assert [t["date"] for t in j["days"]] == [f"2026-11-0{i}" for i in range(1, 8)]
    earlier = (await client.get(URL, params={"end": "2026-11-03"})).json()
    assert (earlier["start"], earlier["end"]) == ("2026-10-28", "2026-11-03")
    future = await client.get(URL, params={"end": "2026-11-08"})
    assert future.status_code == 422 and future.json()["error"]["code"] == "date_in_future"
    assert j["averages"] == {"energy_kcal": None, "protein_g": None, "fat_g": None, "carbs_g": None}
    assert j["averaged_days"] == 0 and j["protein_met_days"] == 0
