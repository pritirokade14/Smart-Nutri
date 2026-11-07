"""Targets never change a verdict (Plan 10 Task 4; AGENTS rule 1): `POST /v1/analyze` is
identical (except the new scan's random id) before and after saving goal settings and a body-fat value."""

import json

import pytest

from scripts.export_fixture_responses import fixture_product_record
from tests.api.targets.conftest import ACC_A, G1_SETTINGS, URL

NAMES = [
    "cola",
    "curd",
    "kiwi_yogurt",
    "namkeen",
    "no_ingredients",
    "oats",
    "sf_biscuit",
    "water",
    "whey_powder",
]


@pytest.mark.parametrize("name", NAMES)
async def test_targets_never_change_verdicts(client, login, grant, db_session, set_primary, name):
    # terms + health_data only: no ai_processing, so no explanation call is ever made.
    await grant(ACC_A, ["terms", "health_data"])
    login(ACC_A)
    await set_primary(birth_year=1997, sex="male", height_cm=175, weight_kg=70, goal="build_muscle")
    product = fixture_product_record(name)
    db_session.add(product)
    await db_session.flush()

    async def analyze() -> str:
        r = await client.post("/v1/analyze", json={"product_id": str(product.id)})
        assert r.status_code == 200, r.text
        body = r.json()
        body.pop("scan_id")  # a new scan row (random id) per call; everything else must match
        return json.dumps(body, sort_keys=True)

    before = await analyze()
    await set_primary(body_fat_pct=15)
    assert (await client.put(f"{URL}/settings", json=G1_SETTINGS)).status_code == 200
    assert (await client.get(URL)).json()["status"] == "ready"
    after = await analyze()
    assert before == after
    assert json.loads(after)["verdicts"]
