"""Shared helpers for the meal-slot write tests."""

URL = "/v1/meal-slots"


async def add(client, label, **kw):
    return await client.post(URL, json={"custom_label": label, **kw})


async def listing(client, **params):
    return (await client.get(URL, params=params)).json()["items"]


async def log_quick(client, slot_id, day="2026-11-07", name="x"):
    r = await client.post(
        "/v1/meals",
        json={
            "meal_slot_id": slot_id,
            "local_date": day,
            "quick": {"name": name, "energy_kcal": 100},
        },
    )
    assert r.status_code == 201, r.text
    return r.json()
