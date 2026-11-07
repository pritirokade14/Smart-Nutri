"""Fixtures for the favourites tests (Plan 12 slice 5). The real consent gate runs here."""

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
from tests.api.foods.conftest import dal  # noqa: F401
from tests.api.targets.conftest import add_member  # noqa: F401


@pytest.fixture
async def slot_ids(client, consented):  # noqa: F811
    items = (await client.get("/v1/meal-slots")).json()["items"]
    return {i["label_key"].rsplit(".", 1)[1]: i["id"] for i in items}


async def make_custom(client, name: str = "Protein bar") -> str:
    r = await client.post("/v1/custom-foods", json=bar(name=name, serving_g=50))
    assert r.status_code == 201, r.text
    return r.json()["id"]


async def log_custom(client, custom_id: str, slot_id: str, *, grams=50, day=None) -> dict:
    body = {"custom_food_id": custom_id, "grams": grams, "meal_slot_id": slot_id}
    if day:
        body["local_date"] = day
    r = await client.post("/v1/meals", json=body)
    assert r.status_code == 201, r.text
    return r.json()


async def save_meal(client, slot_id: str, name="My usual breakfast", day="2026-11-07", **extra):
    return await client.post(
        "/v1/favourites/meals",
        json={"from_date": day, "from_slot_id": slot_id, "name": name} | extra,
    )
