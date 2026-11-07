"""GET /v1/targets (Plan 10 Task 4; Plan 11 Ruling E5: a past day is its frozen row, else `none`;
future is 422)."""

from tests.api.targets.conftest import G1_SETTINGS, G2_SETTINGS, URL

S = f"{URL}/settings"


def _err(r) -> dict:
    return r.json()["error"]


async def test_no_settings_is_none(client, g1):
    r = await client.get(URL)
    assert r.status_code == 200
    t = r.json()
    assert t["status"] == "none" and t["date"] == "2026-11-07"
    assert t["energy_kcal"] is None and t["explanation"] is None
    assert t["flags"] == [] and t["rate_options"] == [] and t["missing_fields"] == []
    assert t["numbers_hidden"] == {"energy": False, "macros": False}
    assert t["pending_clinician_review"] is True and t["basis"] is None


async def test_today_with_settings_is_ready(client, g1):
    await client.put(S, json=G1_SETTINGS)
    t = (await client.get(URL)).json()
    assert t["status"] == "ready" and t["energy_kcal"] == 2760
    t = (await client.get(URL, params={"date": "2026-11-07"})).json()
    assert t["status"] == "ready"


async def test_past_date_without_row_is_none(client, g1):
    await client.put(S, json=G1_SETTINGS)
    t = (await client.get(URL, params={"date": "2026-11-06"})).json()
    assert t["status"] == "none" and t["date"] == "2026-11-06" and t["energy_kcal"] is None


async def test_past_date_returns_frozen_row(client, g1, db_session, seed_day):
    from app.features.members import service as members_service
    from tests.api.targets.conftest import ACC_A

    member = await members_service.get_or_create_primary(db_session, ACC_A)
    await seed_day(member, "2026-11-06", G1_SETTINGS)
    await client.put(S, json=G2_SETTINGS)  # today moves on; yesterday stays frozen
    t = (await client.get(URL, params={"date": "2026-11-06"})).json()
    assert t["status"] == "ready" and t["date"] == "2026-11-06"
    assert (t["energy_kcal"], t["protein_g"], t["fat_g"], t["carbs_g"]) == (2760, 112, 77, 405)
    assert t["rate_options"] == [] and t["basis"] == "formula" and t["direction"] == "gain"
    assert t["rate"] == {"pct_bw_per_week": 0.25, "kg_per_week": 0.18}
    assert t["explanation"]["bmr_kcal"] == 1659 and t["flags"] == []


async def test_frozen_row_redacted_with_current_display(client, g1, db_session, seed_day):
    from app.features.members import service as members_service
    from tests.api.targets.conftest import ACC_A

    member = await members_service.get_or_create_primary(db_session, ACC_A)
    await client.put(S, json=G1_SETTINGS)  # numbers_display "show" when yesterday froze
    await seed_day(member, "2026-11-06", G1_SETTINGS)
    shown = (await client.get(URL, params={"date": "2026-11-06"})).json()
    assert shown["energy_kcal"] == 2760
    assert (
        await client.put(f"{URL}/display", json={"numbers_display": "hide_all"})
    ).status_code == 200
    t = (await client.get(URL, params={"date": "2026-11-06"})).json()
    assert t["status"] == "ready" and t["numbers_hidden"] == {"energy": True, "macros": True}
    for key in ("energy_kcal", "protein_g", "fat_g", "carbs_g"):
        assert t[key] is None, key
    assert (
        all(v is None for k, v in t["explanation"].items() if k not in ("protein_basis",))
        or t["explanation"]["bmr_kcal"] is None
    )
    assert t["explanation"]["bmr_kcal"] is None and t["rate"]["kg_per_week"] is None


async def test_future_date_422(client, g1):
    r = await client.get(URL, params={"date": "2026-11-08"})
    assert r.status_code == 422
    assert _err(r)["code"] == "date_in_future" and _err(r)["message_key"] == "error.date_in_future"


async def test_today_follows_settings_change(client, g1):
    await client.put(S, json=G1_SETTINGS)
    assert (await client.get(URL)).json()["energy_kcal"] == 2760
    await client.put(S, json={**G1_SETTINGS, "activity_level": "sedentary"})
    t = (await client.get(URL)).json()
    assert t["energy_kcal"] != 2760 and t["explanation"]["activity_factor"] == 1.2


async def test_today_follows_a_member_edit(client, g1, set_primary):
    await client.put(S, json=G1_SETTINGS)
    await set_primary(weight_kg=80)
    t = (await client.get(URL)).json()
    assert t["explanation"]["weight_kg_used"] == 80.0


async def test_targets_get_after_weight_drop_is_maintenance(client, g2, set_primary):
    # The user saved "lose", then the weight dropped to BMI 17.7: GET never 422s.
    assert (await client.put(S, json=G2_SETTINGS)).json()["direction"] == "lose"
    await set_primary(height_cm=168, weight_kg=50)
    r = await client.get(URL)
    assert r.status_code == 200, r.text
    t = r.json()
    assert t["status"] == "ready" and t["direction"] == "maintain"
    assert "underweight_maintenance" in t["flags"]
    assert t["rate"] is None and t["explanation"]["adjustment_kcal"] == 0


async def test_minor_and_pregnancy_statuses(client, g1, set_primary):
    await client.put(S, json=G1_SETTINGS)
    await set_primary(birth_year=2011)  # a birth-year correction: age 15
    t = (await client.get(URL)).json()
    assert t["status"] == "not_available_minor" and t["energy_kcal"] is None
    assert t["explanation"] is None
    await set_primary(birth_year=1997)
    await client.put(S, json={**G1_SETTINGS, "pregnant_or_breastfeeding": True})
    t = (await client.get(URL)).json()
    assert t["status"] == "paused_pregnancy" and t["energy_kcal"] is None


async def test_needs_body_data_status(client, g1, set_primary):
    await client.put(S, json=G1_SETTINGS)
    await set_primary(height_cm=None, sex=None)
    t = (await client.get(URL)).json()
    assert t["status"] == "needs_body_data" and t["missing_fields"] == ["sex", "height_cm"]


async def test_body_fat_changes_the_basis(client, g1, set_primary):
    await client.put(S, json=G1_SETTINGS)
    await set_primary(body_fat_pct=15)
    t = (await client.get(URL)).json()
    assert t["explanation"]["protein_basis"] == "lean_mass" and t["protein_g"] == 119
    assert t["explanation"]["body_fat_pct_used"] == 15.0


async def test_unusual_fields_on_get(client, g1, set_primary):
    await client.put(S, json=G1_SETTINGS)
    await set_primary(height_cm=115)
    assert (await client.get(URL)).json()["unusual_fields"] == ["height_cm"]
