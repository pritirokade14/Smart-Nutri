"""PUT/GET /v1/targets/settings, DELETE (Plan 10 Task 4)."""

import pytest

from tests.api.targets.conftest import (
    ACC_A,
    ACC_C,
    G1_SETTINGS,
    G2_SETTINGS,
    URL,
)

S = f"{URL}/settings"


def _err(r) -> dict:
    return r.json()["error"]


async def test_put_then_get_roundtrip(client, g1):
    r = await client.put(S, json=G1_SETTINGS)
    assert r.status_code == 200, r.text
    t = r.json()
    assert t["status"] == "ready" and t["date"] == "2026-11-07"
    assert (t["energy_kcal"], t["protein_g"], t["fat_g"], t["carbs_g"]) == (2760, 112, 77, 405)
    e = t["explanation"]
    assert (e["bmr_kcal"], e["maintenance_kcal"], e["adjustment_kcal"]) == (1659, 2571, 193)
    assert e["protein_basis"] == "actual_weight"
    assert t["basis"] == "formula" and t["direction"] == "gain"
    assert t["rate"] == {"pct_bw_per_week": 0.25, "kg_per_week": 0.18}
    assert t["pending_clinician_review"] is True
    assert t["numbers_hidden"] == {"energy": False, "macros": False}
    assert "mifflin_1990" in t["sources"]
    got = (await client.get(S)).json()
    assert got["member_id"] == str(g1)
    for key, value in G1_SETTINGS.items():
        assert got[key] == value
    assert got["numbers_display"] == "show" and got["summary_view"] == "remaining"
    assert got["energy_mode"] == "formula" and got["updated_at"]


async def test_put_replaces_the_row(client, g1):
    await client.put(S, json=G1_SETTINGS)
    r = await client.put(S, json={**G2_SETTINGS, "target_weight_kg": 60})
    assert r.status_code == 200
    got = (await client.get(S)).json()
    assert got["direction"] == "lose" and got["target_weight_kg"] == 60


async def test_omitted_rate_is_stored_as_the_yaml_default(client, g1):
    body = {k: v for k, v in G1_SETTINGS.items() if k != "rate_pct_bw_per_week"}
    assert (await client.put(S, json=body)).status_code == 200
    assert (await client.get(S)).json()["rate_pct_bw_per_week"] == 0.25
    maintain = {
        "direction": "maintain",
        "activity_level": "light",
        "pregnant_or_breastfeeding": False,
    }
    assert (await client.put(S, json=maintain)).status_code == 200
    assert (await client.get(S)).json()["rate_pct_bw_per_week"] is None


async def test_get_without_settings_is_null(client, g1):
    r = await client.get(S)
    assert r.status_code == 200 and r.json() is None


@pytest.mark.parametrize(
    ("member", "body", "code"),
    [
        ({"birth_year": 2011}, G2_SETTINGS, "goal_not_allowed_minor"),
        ({"height_cm": 168, "weight_kg": 50}, G2_SETTINGS, "goal_not_allowed_underweight"),
        ({"height_cm": 160}, {**G1_SETTINGS, "target_weight_kg": 40}, "target_weight_too_low"),
        ({}, {**G2_SETTINGS, "rate_pct_bw_per_week": 0.6}, "rate_not_allowed"),
        ({}, {**G1_SETTINGS, "fat_pct_energy": 31}, "fat_pct_out_of_range"),
        ({}, {**G1_SETTINGS, "energy_mode": "adaptive"}, "adaptive_not_enabled"),
    ],
)
async def test_put_error_codes(client, g1, set_primary, member, body, code):
    await set_primary(**member)
    r = await client.put(S, json=body)
    assert r.status_code == 422, r.text
    assert _err(r)["code"] == code
    assert _err(r)["message_key"] == f"error.{code}"
    assert (await client.get(S)).json() is None  # nothing was stored


async def test_error_details(client, g1, set_primary):
    await set_primary(height_cm=160)
    r = await client.put(S, json={**G1_SETTINGS, "target_weight_kg": 47})
    assert _err(r)["details"] == {"min_kg": 47.4}
    r = await client.put(S, json={**G2_SETTINGS, "rate_pct_bw_per_week": 0.6})
    assert _err(r)["details"] == {"options": [0.25, 0.5, 0.75, 1.0]}
    r = await client.put(S, json={**G1_SETTINGS, "fat_pct_energy": 31})
    assert _err(r)["details"] == {"min": 20, "max": 30}


async def test_target_weight_bounds_are_a_validation_error(client, g1):
    r = await client.put(S, json={**G1_SETTINGS, "target_weight_kg": 1})
    assert r.status_code == 422 and _err(r)["code"] == "validation_error"


async def test_put_with_missing_body_data_is_ready_to_save(client, g1, set_primary):
    # Missing height: the settings are saved, the targets report what is needed (not an error).
    await set_primary(height_cm=None)
    r = await client.put(S, json=G1_SETTINGS)
    assert r.status_code == 200
    assert r.json()["status"] == "needs_body_data" and r.json()["missing_fields"] == ["height_cm"]
    assert (await client.get(S)).json()["direction"] == "gain"


async def test_foreign_member_404(client, g1, add_member):
    other = await add_member(ACC_C, name="Other")
    for method, kwargs in (
        ("put", {"json": {**G1_SETTINGS, "member_id": str(other.id)}}),
        ("get", {"params": {"member_id": str(other.id)}}),
        ("delete", {"params": {"member_id": str(other.id)}}),
    ):
        r = await getattr(client, method)(S, **kwargs)
        assert r.status_code == 404, (method, r.text)
        assert _err(r)["code"] == "member_not_found"


async def test_non_primary_422_until_flag_on(client, app, g1, add_member, monkeypatch):
    member = await add_member(ACC_A, name="Papa", relation="parent")
    body = {**G1_SETTINGS, "member_id": str(member.id)}
    r = await client.put(S, json=body)
    assert r.status_code == 422 and _err(r)["code"] == "diary_member_not_enabled"
    assert (await client.get(S, params={"member_id": str(member.id)})).status_code == 422
    monkeypatch.setattr(app.state.settings, "diary_family_enabled", True)
    assert (await client.put(S, json=body)).status_code == 200


async def test_primary_member_id_is_accepted(client, g1):
    r = await client.put(S, json={**G1_SETTINGS, "member_id": str(g1)})
    assert r.status_code == 200 and r.json()["member_id"] == str(g1)


async def test_delete_then_get_is_none(client, g1):
    await client.put(S, json=G1_SETTINGS)
    r = await client.delete(S)
    assert r.status_code == 204 and r.content == b""
    assert (await client.get(S)).json() is None
    assert (await client.get(URL)).json()["status"] == "none"
    assert (await client.delete(S)).status_code == 204  # idempotent


async def test_settings_put_rate_limited(client, g1, app):
    for _ in range(30):
        assert (await client.put(S, json=G1_SETTINGS)).status_code == 200
    r = await client.put(S, json=G1_SETTINGS)
    assert r.status_code == 429 and _err(r)["code"] == "rate_limited"


def test_default_limits():
    from app.core.config import Settings

    s = Settings(_env_file=None)
    assert s.rate_limit_diary_settings_per_day == 30
    assert s.rate_limit_targets_preview_per_hour == 120
    assert s.diary_family_enabled is False and s.adaptive_tdee_enabled is False


async def test_every_settings_error_code_has_copy():
    import json

    from app.core.consent import REQUIRED  # noqa: F401
    from tests.unit.test_error_codes_i18n import MESSAGES

    for locale in ("en", "hi", "mr"):
        messages = json.loads((MESSAGES / f"{locale}.json").read_text())["error"]
        for code in (
            "goal_not_allowed_minor",
            "goal_not_allowed_underweight",
            "target_weight_too_low",
            "rate_not_allowed",
            "fat_pct_out_of_range",
            "adaptive_not_enabled",
            "body_fat_out_of_range",
            "diary_member_not_enabled",
            "date_in_future",
            "goal_settings_not_found",
        ):
            assert messages.get(code), (locale, code)
