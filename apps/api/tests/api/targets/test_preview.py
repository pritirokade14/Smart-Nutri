"""POST /v1/targets/preview (Plan 10 Task 4): unsaved settings and body data, hidden numbers."""

import json

import pytest
from sqlalchemy import select

from app.features.members.models import Member
from tests.api.targets.conftest import ACC_A, G1_SETTINGS, G2_SETTINGS, URL

P = f"{URL}/preview"
S = f"{URL}/settings"


def _err(r) -> dict:
    return r.json()["error"]


async def test_preview_matches_put_and_saves_nothing(client, g1):
    r = await client.post(P, json=G1_SETTINGS)
    assert r.status_code == 200, r.text
    assert r.json()["energy_kcal"] == 2760
    assert (await client.get(S)).json() is None


async def test_preview_unsaved_body_fat_moves_basis(client, g1, db_session):
    r = await client.post(P, json={**G1_SETTINGS, "body": {"body_fat_pct": 15}})
    t = r.json()
    assert t["explanation"]["protein_basis"] == "lean_mass" and t["protein_g"] == 119
    row = await db_session.scalar(
        select(Member)
        .where(Member.account_id == ACC_A, Member.is_primary.is_(True))
        .execution_options(populate_existing=True)
    )
    assert row.body_fat_pct is None  # the member row is unchanged


async def test_preview_body_fat_out_of_range(client, g1):
    r = await client.post(P, json={**G1_SETTINGS, "body": {"body_fat_pct": 2.9}})
    assert r.status_code == 422 and _err(r)["code"] == "body_fat_out_of_range"
    assert _err(r)["details"] == {"min": 3, "max": 70}


async def test_preview_sent_null_overrides_stored(client, g1, set_primary):
    await set_primary(body_fat_pct=15)
    kept = (await client.post(P, json=G1_SETTINGS)).json()
    assert kept["explanation"]["protein_basis"] == "lean_mass"
    cleared = (await client.post(P, json={**G1_SETTINGS, "body": {"body_fat_pct": None}})).json()
    assert cleared["explanation"]["protein_basis"] == "actual_weight"


async def test_preview_needs_body_data_is_200(client, g1):
    r = await client.post(P, json={**G1_SETTINGS, "body": {"height_cm": None}})
    assert r.status_code == 200
    t = r.json()
    assert t["status"] == "needs_body_data" and t["missing_fields"] == ["height_cm"]
    assert t["energy_kcal"] is None


async def test_preview_body_overrides_birth_year_and_weight(client, g1):
    t = (await client.post(P, json={**G1_SETTINGS, "body": {"weight_kg": 80}})).json()
    assert t["explanation"]["weight_kg_used"] == 80.0
    t = (await client.post(P, json={**G1_SETTINGS, "body": {"birth_year": 2011}})).json()
    assert _err_or_status(t) == "goal_not_allowed_minor"


def _err_or_status(t) -> str:
    return t["error"]["code"] if "error" in t else t["status"]


async def test_preview_minor_with_a_gain_goal_is_refused(client, g1):
    r = await client.post(P, json={**G1_SETTINGS, "body": {"birth_year": 2011}})
    assert r.status_code == 422 and _err(r)["code"] == "goal_not_allowed_minor"
    ok = await client.post(
        P,
        json={
            "direction": "maintain",
            "activity_level": "light",
            "pregnant_or_breastfeeding": False,
            "body": {"birth_year": 2011},
        },
    )
    assert ok.json()["status"] == "not_available_minor"


async def test_preview_unusual_height(client, g1):
    t = (await client.post(P, json={**G1_SETTINGS, "body": {"height_cm": 115}})).json()
    assert t["unusual_fields"] == ["height_cm"]


async def test_preview_rate_options_g2(client, g2):
    t = (await client.post(P, json=G2_SETTINGS)).json()
    assert [o["kg_per_week"] for o in t["rate_options"]] == [0.2, 0.4, 0.6, 0.8]
    assert [o["pct_bw_per_week"] for o in t["rate_options"]] == [0.25, 0.5, 0.75, 1.0]


async def test_preview_validates_settings_like_put(client, g2):
    r = await client.post(P, json={**G2_SETTINGS, "rate_pct_bw_per_week": 0.6})
    assert r.status_code == 422 and _err(r)["code"] == "rate_not_allowed"
    r = await client.post(P, json={**G2_SETTINGS, "energy_mode": "adaptive"})
    assert r.status_code == 422 and _err(r)["code"] == "adaptive_not_enabled"


async def test_preview_rate_limited(client, g1, app):
    app.state.settings.rate_limit_targets_preview_per_hour = 3
    for _ in range(3):
        assert (await client.post(P, json=G1_SETTINGS)).status_code == 200
    r = await client.post(P, json=G1_SETTINGS)
    assert r.status_code == 429 and _err(r)["code"] == "rate_limited"


def _walk(node, path=""):
    if isinstance(node, dict):
        for k, v in node.items():
            yield from _walk(v, f"{path}.{k}" if path else k)
    elif isinstance(node, list):
        for i, v in enumerate(node):
            yield from _walk(v, f"{path}[{i}]")
    else:
        yield path, node


@pytest.mark.parametrize("fixture", ["g1", "g4"])
async def test_hidden_numbers_redact_every_number(client, consented, set_primary, fixture):
    if fixture == "g4":  # the floor case: the flag copy would carry the floor number
        await set_primary(
            birth_year=1970, sex="female", height_cm=150, weight_kg=52, goal="weight_loss"
        )
        body = {
            "direction": "lose",
            "activity_level": "sedentary",
            "rate_pct_bw_per_week": 1.0,
            "pregnant_or_breastfeeding": False,
        }
    else:
        await set_primary(
            birth_year=1997, sex="male", height_cm=175, weight_kg=70, goal="build_muscle"
        )
        body = G1_SETTINGS
    shown = (await client.post(P, json={**body, "numbers_display": "show"})).json()
    assert shown["energy_kcal"] is not None and shown["numbers_hidden"] == {
        "energy": False,
        "macros": False,
    }

    energy = (await client.post(P, json={**body, "numbers_display": "hide_energy"})).json()
    flat = dict(_walk(energy))
    assert energy["numbers_hidden"] == {"energy": True, "macros": False}
    for key, value in flat.items():
        if "kcal" in key:
            assert value is None, key
    assert energy["protein_g"] == shown["protein_g"] and energy["carbs_g"] == shown["carbs_g"]
    assert energy["explanation"]["protein_g_per_kg"] == shown["explanation"]["protein_g_per_kg"]

    hidden = (await client.post(P, json={**body, "numbers_display": "hide_all"})).json()
    assert hidden["numbers_hidden"] == {"energy": True, "macros": True}
    for key in ("energy_kcal", "protein_g", "fat_g", "carbs_g"):
        assert hidden[key] is None, key
    for key, value in hidden["explanation"].items():
        if key != "protein_basis":
            assert value is None, key
    assert hidden["explanation"]["protein_basis"] == shown["explanation"]["protein_basis"]
    # the pace stays, as a percent only: kg/week would let anyone work out the body weight
    assert hidden["rate"] == {**shown["rate"], "kg_per_week": None}
    assert hidden["rate_options"] == [{**o, "kg_per_week": None} for o in shown["rate_options"]]
    assert all(o["pct_bw_per_week"] for o in hidden["rate_options"])
    # hide_energy still shows the kg pace
    assert energy["rate"] == shown["rate"]
    assert hidden["flags"] == shown["flags"] and hidden["status"] == "ready"
    # no number of the target can be read from the whole response
    text = json.dumps(hidden)
    for number in (str(shown["energy_kcal"]), str(shown["explanation"]["bmr_kcal"])):
        assert f": {number}" not in text
