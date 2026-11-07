"""A recipe entry makes the day incomplete for what an ingredient does not know (Plan 12 Task 12;
G19): the day total is flagged, `remaining` is null for it and stays a number for the rest."""

from tests.api.diary.conftest import G1_SETTINGS

S = "/v1/targets/settings"


async def test_day_incomplete_after_recipe_entry(client, g1, slot_ids, clock):
    assert (await client.put(S, json=G1_SETTINGS)).status_code == 200
    base = {"name": "Lentil mix", "basis": "g", "values_per": "100"}
    full = await client.post(
        "/v1/custom-foods",
        json={**base, "nutrients": {"energy_kcal": 120, "protein_g": 9, "carbs_g": 20, "fat_g": 1}},
    )
    no_protein = await client.post(
        "/v1/custom-foods",
        json={
            **base,
            "name": "Rice",
            "nutrients": {"energy_kcal": 130, "carbs_g": 28, "fat_g": 0.3},
        },
    )
    recipe = await client.post(
        "/v1/recipes",
        json={
            "name": "Khichdi",
            "servings": 2,
            "ingredients": [
                {"custom_food_id": full.json()["id"], "quantity": 100, "unit": "g"},
                {"custom_food_id": no_protein.json()["id"], "quantity": 100, "unit": "g"},
            ],
        },
    )
    assert recipe.status_code == 201, recipe.text
    assert "protein_g" in recipe.json()["incomplete_nutrients"]
    entry = await client.post(
        "/v1/meals",
        json={"recipe_id": recipe.json()["id"], "servings": 1, "meal_slot_id": slot_ids["lunch"]},
    )
    assert entry.status_code == 201, entry.text
    day = (await client.get("/v1/diary/day")).json()
    assert day["incomplete"]["protein_g"] is True
    assert day["remaining"]["protein_g"] is None  # never a partial value counted as complete
    assert isinstance(day["remaining"]["energy_kcal"], float | int)
    assert day["incomplete"]["energy_kcal"] is False
    assert day["totals"]["protein_g"] is None or day["incomplete"]["protein_g"]
