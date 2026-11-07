"""Fixtures for the recipe tests (Plan 12 slice 4). The real consent gate runs here."""

import pytest

from tests.api.custom_foods.conftest import (  # noqa: F401  (shared fixtures)
    ACC_A,
    ACC_B,
    G1_SETTINGS,
    OFF_BARCODE,
    FakeOff,
    accounts,
    bar,
    clock,
    consented,
    fake_off,
    g1,
    grant,
    login,
    make_food,
    portion,
    set_primary,
    settings,
    today,
)


@pytest.fixture
async def slot_ids(client, consented):  # noqa: F811
    items = (await client.get("/v1/meal-slots")).json()["items"]
    return {i["label_key"].rsplit(".", 1)[1]: i["id"] for i in items}


async def make_custom(client, name: str, **nutrients) -> str:
    """A custom food (per 100 g, serving 50 g); an omitted nutrient is unknown."""
    body = bar(name=name, serving_g=50, nutrients=nutrients or bar()["nutrients"])
    r = await client.post("/v1/custom-foods", json=body)
    assert r.status_code == 201, r.text
    return r.json()["id"]


def ing(custom_food_id, grams=100, unit="g", **ref):
    ref = ref or {"custom_food_id": custom_food_id}
    return {**ref, "quantity": grams, "unit": unit}
