"""PUT /v1/targets/display: the eye toggle (Plan 10 Task 4, Ruling D4, D19)."""

from sqlalchemy import update

from app.features.targets.models import DiaryGoalSettings
from tests.api.targets.conftest import ACC_A, G1_SETTINGS, URL

D = f"{URL}/display"
S = f"{URL}/settings"


def _err(r) -> dict:
    return r.json()["error"]


async def test_display_toggle(client, g1):
    await client.put(S, json=G1_SETTINGS)
    r = await client.put(D, json={"numbers_display": "hide_all"})
    assert r.status_code == 200, r.text
    assert r.json()["numbers_display"] == "hide_all" and r.json()["summary_view"] == "remaining"
    t = (await client.get(URL)).json()
    assert t["numbers_hidden"] == {"energy": True, "macros": True} and t["energy_kcal"] is None
    r = await client.put(D, json={"numbers_display": "show"})
    assert r.json()["numbers_display"] == "show"
    assert (await client.get(URL)).json()["energy_kcal"] == 2760


async def test_display_changes_only_the_two_fields(client, g1):
    await client.put(S, json={**G1_SETTINGS, "target_weight_kg": 80})
    r = await client.put(D, json={"summary_view": "consumed"})
    got = r.json()
    assert got["summary_view"] == "consumed" and got["numbers_display"] == "show"
    saved = (await client.get(S)).json()
    assert saved["direction"] == "gain" and saved["target_weight_kg"] == 80
    assert saved["rate_pct_bw_per_week"] == 0.25


async def test_display_response_is_minimal_even_without_health_data(client, g1):
    await client.put(S, json={**G1_SETTINGS, "target_weight_kg": 80})
    await client.post(
        "/v1/consents", json={"purpose": "health_data", "version": "2026-11-01", "granted": False}
    )
    r = await client.put(D, json={"numbers_display": "hide_all"})
    assert r.status_code == 200
    assert set(r.json()) == {"member_id", "numbers_display", "summary_view", "updated_at"}
    text = r.text
    for secret in ("pregnant", "target_weight", "direction", "activity", "rate_pct"):
        assert secret not in text, secret
    # Compare values, not raw text: ids and timestamps can contain the digits "80".
    assert 80 not in r.json().values()


async def test_hiding_is_never_rate_limited(client, g1, app, db_session):
    await client.put(S, json=G1_SETTINGS)
    app.state.settings.rate_limit_diary_settings_per_day = 1  # the settings save used it up
    for i in range(36):  # past the default 30/day
        target = "hide_energy" if i % 2 == 0 else "hide_all"
        r = await client.put(D, json={"numbers_display": target})
        assert r.status_code == 200, (i, r.text)
        if target == "hide_all":  # back to "show" behind the API's back, to hide again
            await db_session.execute(update(DiaryGoalSettings).values(numbers_display="show"))
            await db_session.commit()
    # showing again (away from hiding) does count and is refused once the budget is gone
    r = await client.put(D, json={"numbers_display": "show"})
    assert r.status_code == 429


async def test_hide_energy_after_hide_all_counts_but_hide_all_does_not(client, g1, app):
    await client.put(S, json=G1_SETTINGS)
    app.state.settings.rate_limit_diary_settings_per_day = 1
    assert (await client.put(D, json={"numbers_display": "hide_all"})).status_code == 200
    # hide_all -> hide_energy shows more numbers: it is not "toward hiding"
    assert (await client.put(D, json={"numbers_display": "hide_energy"})).status_code == 429


async def test_display_null_means_unchanged(client, g1):
    await client.put(S, json={**G1_SETTINGS, "numbers_display": "hide_energy"})
    r = await client.put(D, json={"numbers_display": None, "summary_view": "consumed"})
    assert r.json()["numbers_display"] == "hide_energy"


async def test_display_without_settings_404(client, g1):
    r = await client.put(D, json={"numbers_display": "hide_all"})
    assert r.status_code == 404
    assert _err(r)["code"] == "goal_settings_not_found"
    assert _err(r)["message_key"] == "error.goal_settings_not_found"


async def test_display_works_without_health_data(client, g1, login, grant, db_session):
    await client.put(S, json=G1_SETTINGS)
    r = await client.post(
        "/v1/consents", json={"purpose": "health_data", "version": "2026-11-01", "granted": False}
    )
    assert r.status_code == 200
    assert (await client.get(URL)).status_code == 403
    r = await client.put(D, json={"numbers_display": "hide_all"})
    assert r.status_code == 200 and r.json()["numbers_display"] == "hide_all"


async def test_display_does_not_revalidate_stored_settings(client, g1, set_primary):
    # Stored settings that no longer validate (weight below BMI 18.5 with "lose") must not
    # stop the eye toggle.
    await set_primary(weight_kg=80, height_cm=160, goal="weight_loss")
    await client.put(
        S,
        json={
            "direction": "lose",
            "activity_level": "light",
            "rate_pct_bw_per_week": 0.5,
            "pregnant_or_breastfeeding": False,
        },
    )
    await set_primary(weight_kg=40)
    r = await client.put(D, json={"numbers_display": "hide_all"})
    assert r.status_code == 200


async def test_display_rate_limited_with_the_settings_bucket(client, g1, app):
    await client.put(S, json=G1_SETTINGS)  # 1
    app.state.settings.rate_limit_diary_settings_per_day = 3
    assert (await client.put(D, json={"numbers_display": "show"})).status_code == 200  # 2
    assert (await client.put(D, json={"numbers_display": "show"})).status_code == 200  # 3
    r = await client.put(D, json={"numbers_display": "show"})
    assert r.status_code == 429 and _err(r)["code"] == "rate_limited"
    assert ACC_A
