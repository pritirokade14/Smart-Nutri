"""Hidden numbers on every diary surface (Plan 11 Task 7; Q7, spec 6.2): the API redacts, so a
client bug can never show a hidden value."""

from uuid import uuid4

import pytest

from tests.api.diary.conftest import G1_SETTINGS

NUTRIENT_KEYS = {
    "energy_kcal",
    "protein_g",
    "fat_g",
    "carbs_g",
    "fibre_g",
    "sugars_g",
    "salt_g",
    "sat_fat_g",
}


def _walk(node, path=""):
    """Every (path, key, value) of a JSON body."""
    if isinstance(node, dict):
        for k, v in node.items():
            yield path, k, v
            yield from _walk(v, f"{path}.{k}")
    elif isinstance(node, list):
        for i, v in enumerate(node):
            yield from _walk(v, f"{path}[{i}]")


def _check(name: str, body, display: str) -> None:
    """The rules: under hide_energy every key with energy or kcal is null; under hide_all every
    nutrient key is null wherever it appears. `progress` (0.25 steps) and the limits (which are
    not totals) are the documented exceptions."""
    for path, key, value in _walk(body):
        if ".progress" in f"{path}.{key}" or ".limits" in path or path.endswith(".limits"):
            continue
        if value is None or isinstance(value, bool | str | dict | list):
            continue
        if "energy" in key or "kcal" in key:
            raise AssertionError(f"{name}: {path}.{key} = {value} (energy is hidden)")
        if display == "hide_all" and key in NUTRIENT_KEYS:
            raise AssertionError(f"{name}: {path}.{key} = {value} (macros are hidden)")


@pytest.mark.parametrize("display", ["hide_energy", "hide_all"])
async def test_hidden_numbers_every_diary_surface(client, g1, slot_ids, product_id, clock, display):
    assert (
        await client.put("/v1/targets/settings", json={**G1_SETTINGS, "numbers_display": display})
    ).status_code == 200
    bodies: dict[str, object] = {}

    log = await client.post(
        "/v1/meals",
        json={"product_id": str(product_id), "grams": 100, "meal_slot_id": slot_ids["lunch"]},
    )
    assert log.status_code == 201, log.text
    bodies["meals_log product"] = log.json()
    quick = await client.post("/v1/meals", json={"quick": {"energy_kcal": 450, "protein_g": 12}})
    bodies["meals_log quick"] = quick.json()
    past = await client.post(
        "/v1/meals",
        json={
            "product_id": str(product_id),
            "grams": 50,
            "local_date": "2026-11-06",
            "meal_slot_id": slot_ids["dinner"],
        },
    )
    bodies["meals_update"] = (
        await client.patch(f"/v1/meals/{log.json()['id']}", json={"grams": 150})
    ).json()
    bodies["meals_update quick"] = (
        await client.patch(f"/v1/meals/{quick.json()['id']}", json={"quick": {"energy_kcal": 300}})
    ).json()
    bodies["meals_list"] = (await client.get("/v1/meals")).json()
    bodies["meals_list local_date"] = (
        await client.get("/v1/meals", params={"local_date": "2026-11-07"})
    ).json()
    copied = await client.post(
        "/v1/meals/copy",
        json={"from_date": "2026-11-06", "to_date": "2026-11-05", "client_id": str(uuid4())},
    )
    assert copied.status_code == 201, copied.text
    bodies["meals_copy"] = copied.json()
    day = await client.get("/v1/diary/day")
    bodies["diary_day_get"] = day.json()
    bodies["diary_day_get past"] = (
        await client.get("/v1/diary/day", params={"date": "2026-11-06"})
    ).json()
    bodies["diary_week_get"] = (await client.get("/v1/diary/week")).json()
    bodies["diary_recents_list"] = (await client.get("/v1/diary/recents")).json()
    bodies["targets_get"] = (await client.get("/v1/targets")).json()
    bodies["meals_summary"] = (
        await client.get("/v1/meals/summary", params={"member_id": str(g1), "period": "week"})
    ).json()
    assert past.status_code == 201

    for name, body in bodies.items():
        _check(name, body, display)

    # What stays: portions, slot structure, bands and progress in quarter steps.
    day_body = bodies["diary_day_get"]
    assert day_body["numbers_hidden"] == {"energy": True, "macros": display == "hide_all"}
    grams = [e["grams"] for s in day_body["slots"] for e in s["entries"]]
    assert sorted(grams, key=lambda g: (g is None, g)) == [150.0, None]  # portions stay
    assert day_body["slots"][1]["label_key"] == "diary.slot.lunch"
    assert day_body["limits_bands"]["sugar_g"] in ("ok", "near", "over", "unknown")
    for key, value in day_body["progress"].items():
        assert value is None or value * 4 == int(value * 4), (key, value)
    if display == "hide_energy":
        assert day_body["totals"]["protein_g"] is not None  # macros are still shown
        assert day_body["remaining"]["energy_kcal"] is None
