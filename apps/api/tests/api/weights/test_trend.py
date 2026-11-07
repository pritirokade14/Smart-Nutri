"""weights_trend_get (Plan 12 Task 23; G24, G27): the shared fixtures and the hide_all rule."""

import json

import pytest

from tests.api.weights.conftest import ACC_A, ACC_B, TREND, URL, body
from tests.fixtures.loader import FIXTURES

WEIGHTS = FIXTURES / "weights"
STEMS = sorted(p.stem for p in (WEIGHTS / "inputs").glob("*.json"))
ENVELOPE = ("member_id", "days", "from", "to")


def test_fixture_set_is_present():
    assert len(STEMS) >= 16


@pytest.mark.parametrize("stem", STEMS)
async def test_matches_weight_fixtures(
    stem, client, consented, seed_weights, put_settings_row, clock
):
    case = json.loads((WEIGHTS / "inputs" / f"{stem}.json").read_text(encoding="utf-8"))
    want = json.loads((WEIGHTS / "expected" / f"{stem}.json").read_text(encoding="utf-8"))
    last = case["weigh_ins"][-1]["date"]
    clock.set(f"{last}T06:30:00+00:00")  # today is the last weigh-in: the 365-day window has all
    member = await seed_weights([(w["date"], w["weight_kg"]) for w in case["weigh_ins"]])
    cols = {"numbers_display": case.get("numbers_display", "show")}
    if case.get("target_kg") is not None:
        cols["target_weight_kg"] = case["target_kg"]
    await put_settings_row(member, **cols)
    r = await client.get(TREND, params={"days": 365})
    assert r.status_code == 200, r.text
    got = r.json()
    assert got["member_id"] == str(member.id) and got["days"] == 365
    assert got["to"] == last
    for key in ENVELOPE:
        got.pop(key)
    assert got == want


async def test_window_slices_but_keeps_the_full_history(client, consented, seed_weights):
    rows = [(f"2026-10-{d:02d}", 80 - d * 0.1) for d in range(1, 29)]
    await seed_weights(rows)
    full = (await client.get(TREND, params={"days": 90})).json()
    short = (await client.get(TREND, params={"days": 30})).json()
    assert (
        len(full["points"]) == 28 and short["from"] == "2026-10-09" and short["to"] == "2026-11-07"
    )
    assert next(p["date"] for p in short["points"]) == "2026-10-09"
    assert short["trend"][-1]["trend_kg"] == full["trend"][-1]["trend_kg"]  # same history
    assert short["weekly_rate"] == full["weekly_rate"]


async def test_days_must_be_30_90_or_365(client, consented):
    assert (await client.get(TREND, params={"days": 60})).status_code == 422
    assert (await client.get(TREND)).json()["days"] == 90


async def test_empty_history(client, consented):
    j = (await client.get(TREND)).json()
    assert j["points"] == [] and j["trend"] == [] and j["weekly_rate"] is None
    assert j["projection"] is None and j["projection_reason"] == "no_target"
    assert j["pending_clinician_review"] is True


async def test_target_comes_from_goal_settings_not_maintain(
    client, consented, seed_weights, put_settings_row
):
    member = await seed_weights([(f"2026-10-{d:02d}", 80 - d * 0.1) for d in range(1, 21)])
    await put_settings_row(member, direction="maintain", target_weight_kg=70)
    assert (await client.get(TREND)).json()["projection_reason"] == "no_target"


async def test_weights_hidden_every_surface(client, g5, put_settings_row, seed_weights):
    """`hide_all`: list, put, trend and the error details carry no kg; `y` is kept."""
    await put_settings_row(g5, numbers_display="hide_all", target_weight_kg=75)
    for d in range(1, 21):
        assert (
            await client.put(f"{URL}/2026-10-{d:02d}", json=body(80 - d * 0.1))
        ).status_code in (
            200,
            422,
        )
    put = await client.put(f"{URL}/2026-11-07", json=body(77.77))
    assert put.status_code == 200 and put.json()["weight_kg"] is None
    assert put.json()["numbers_hidden"] is True
    listing = (await client.get(URL)).json()
    assert listing["numbers_hidden"] is True
    assert all(i["weight_kg"] is None and i["numbers_hidden"] for i in listing["items"])
    trend = (await client.get(TREND)).json()
    assert trend["numbers_hidden"] is True and trend["weekly_rate"] is None
    assert trend["rapid_loss_pct"] is None  # a policy threshold, never shown when hidden
    assert all(p["weight_kg"] is None and p["y"] is not None for p in trend["points"])
    assert all(t["trend_kg"] is None and t["y"] is not None for t in trend["trend"])
    if trend["projection"] is not None:
        assert trend["projection"] == {"target_kg": None, "date": None}
    err = await client.put(f"{URL}/2026-11-07", json=body(250))
    assert err.status_code == 422 and err.json()["error"]["details"]["previous"] is None
    assert "77" not in err.text


async def test_hide_energy_changes_nothing_here(client, g5, put_settings_row, seed_weights):
    await put_settings_row(g5, numbers_display="hide_energy")
    await seed_weights([("2026-11-05", 80), ("2026-11-06", 79.9), ("2026-11-07", 79.8)])
    j = (await client.get(TREND)).json()
    assert j["numbers_hidden"] is False and j["points"][0]["weight_kg"] == 80.0


async def test_account_isolation(client, consented, grant, seed_weights):
    await grant(ACC_B)
    await seed_weights([("2026-11-07", 80)], account=ACC_A)
    await seed_weights([("2026-11-07", 99)], account=ACC_B)
    items = (await client.get(URL)).json()["items"]
    assert [i["weight_kg"] for i in items] == [80.0]
