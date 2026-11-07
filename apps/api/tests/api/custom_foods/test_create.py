"""custom_foods_create (Plan 12 Task 11; spec 5.8; G15, G18)."""

from sqlalchemy import func, select

from app.features.custom_foods.models import CustomFood
from app.features.foods.models import FoodPortion
from tests.api.custom_foods.conftest import ACC_A, bar

URL = "/v1/custom-foods"


async def test_create_per_100(client, consented):
    r = await client.post(URL, json=bar(brand="Acme", serving_g=60))
    assert r.status_code == 201, r.text
    body = r.json()
    assert body["name"] == "Protein bar" and body["brand"] == "Acme" and body["basis"] == "g"
    assert body["per_100"] == {
        "energy_kcal": 400.0, "protein_g": 30.0, "carbs_g": 40.0, "fat_g": 12.0,
        "sugars_g": None, "salt_g": None, "sat_fat_g": None, "fibre_g": None,
    }  # fmt: skip
    assert body["entered"]["values_per"] == "100" and body["entered"]["serving_g"] == 60.0
    assert body["entered"]["nutrients"]["protein_g"] == 30.0
    assert body["serving_g"] == 60.0 and body["portions"] == [] and body["barcode"] is None


async def test_create_per_serving_converts(client, consented):
    r = await client.post(
        URL,
        json=bar(
            values_per="serving",
            serving_g=30,
            nutrients={"energy_kcal": 120, "protein_g": 12, "fibre_g": 3},
        ),
    )
    assert r.status_code == 201, r.text
    body = r.json()
    assert body["per_100"]["protein_g"] == 40.0  # 12 g per 30 g serving
    assert body["per_100"]["energy_kcal"] == 400.0 and body["per_100"]["fibre_g"] == 10.0
    assert body["entered"] == {
        "values_per": "serving",
        "serving_g": 30.0,
        "nutrients": {
            "energy_kcal": 120.0, "protein_g": 12.0, "carbs_g": None, "sugars_g": None,
            "fat_g": None, "sat_fat_g": None, "fibre_g": 3.0, "salt_g": None, "sodium_mg": None,
        },
    }  # fmt: skip
    assert body["serving_g"] == 30.0


async def test_per_serving_needs_a_serving_size(client, consented):
    r = await client.post(URL, json=bar(values_per="serving"))
    assert r.status_code == 422 and r.json()["error"]["code"] == "validation_error"
    assert r.json()["error"]["details"]["fields"] == ["body.serving_g"]


async def test_blank_stays_null_never_zero(client, consented, db_session):
    r = await client.post(URL, json=bar(nutrients={"energy_kcal": 90, "sugars_g": None}))
    assert r.status_code == 201
    per_100 = r.json()["per_100"]
    assert per_100["energy_kcal"] == 90.0
    assert all(per_100[k] is None for k in per_100 if k != "energy_kcal")
    row = await db_session.scalar(select(CustomFood))
    assert row.per_100 == {"energy_kcal": 90.0}  # absent, not 0
    # A typed zero is a known zero, kept as 0.
    r = await client.post(URL, json=bar(name="Water", nutrients={"energy_kcal": 0}))
    assert r.status_code == 201 and r.json()["per_100"]["energy_kcal"] == 0.0


async def test_salt_and_sodium_follow_the_engine_rule(client, consented):
    r = await client.post(
        URL, json=bar(nutrients={"energy_kcal": 100, "salt_g": 0.5, "sodium_mg": 400})
    )
    assert r.status_code == 201
    assert r.json()["per_100"]["salt_g"] == 1.0  # sodium 400 mg = 1.0 g salt, the higher wins


async def test_nutrients_empty_422(client, consented):
    for nutrients in ({}, {"sugars_g": 5, "salt_g": 1, "fibre_g": 2}):
        r = await client.post(URL, json=bar(nutrients=nutrients))
        assert r.status_code == 422, nutrients
        assert r.json()["error"]["code"] == "custom_food_nutrients_empty"


async def test_implausible_422(client, consented):
    r = await client.post(URL, json=bar(nutrients={"energy_kcal": 400, "protein_g": 120}))
    assert r.status_code == 422 and r.json()["error"]["code"] == "implausible_value"
    assert "body.nutrients.protein_g" in r.json()["error"]["details"]["fields"]
    # Sugars above carbs is implausible too.
    r = await client.post(URL, json=bar(nutrients={"carbs_g": 10, "sugars_g": 30}))
    assert r.status_code == 422 and r.json()["error"]["code"] == "implausible_value"
    # Per serving that blows up per 100 is caught after the conversion.
    r = await client.post(
        URL,
        json=bar(values_per="serving", serving_g=1, nutrients={"energy_kcal": 90}),
    )
    assert r.status_code == 422 and r.json()["error"]["code"] == "implausible_value"
    assert (await client.get(URL)).json()["items"] == []  # nothing stored


async def test_negative_and_bad_shapes_422(client, consented):
    for cols in (
        {"nutrients": {"energy_kcal": -1}},
        {"name": "   "},
        {"name": "x" * 81},
        {"basis": "kg"},
        {"density_g_per_ml": 0.1},
        {"density_g_per_ml": 2.5},
    ):
        r = await client.post(URL, json=bar(**cols))
        assert r.status_code == 422, cols
        assert r.json()["error"]["code"] == "validation_error", cols


async def test_name_is_trimmed(client, consented):
    r = await client.post(URL, json=bar(name="  Bar  ", brand="   "))
    assert r.json()["name"] == "Bar" and r.json()["brand"] is None


async def test_barcode_normalised_and_invalid(client, consented):
    r = await client.post(URL, json=bar(barcode="8901-0630 1089"))
    assert r.status_code == 201 and r.json()["barcode"] == "890106301089"
    r = await client.post(URL, json=bar(barcode="12ab"))
    assert r.status_code == 422 and r.json()["error"]["code"] == "invalid_barcode"


async def test_barcode_duplicate_422(client, consented, grant, login):
    from tests.api.custom_foods.conftest import ACC_B

    first = await client.post(URL, json=bar(barcode="8901063201089"))
    assert first.status_code == 201
    r = await client.post(URL, json=bar(name="Other", barcode="8901063201089"))
    assert r.status_code == 422 and r.json()["error"]["code"] == "barcode_already_used"
    # Another account may use the same barcode for its own food.
    await grant(ACC_B)
    login(ACC_B)
    assert (await client.post(URL, json=bar(barcode="8901063201089"))).status_code == 201


async def test_client_id_retry_200(client, consented, cid, db_session):
    first = await client.post(URL, json=bar(client_id=cid))
    again = await client.post(URL, json=bar(client_id=cid, name="Changed"))
    assert (first.status_code, again.status_code) == (201, 200)
    assert again.json()["id"] == first.json()["id"] and again.json()["name"] == "Protein bar"
    n = await db_session.scalar(select(func.count()).select_from(CustomFood))
    assert n == 1


async def test_client_id_concurrent_race(client, consented, cid, db_session, monkeypatch):
    """The first lookup finds nothing (a concurrent post is about to win); the insert then hits
    the unique key and the stored row is returned with 200."""
    from app.features.custom_foods import service

    first = await client.post(URL, json=bar(client_id=cid))
    real = service._by_client_id
    calls = 0

    async def blind_once(*args, **kwargs):
        nonlocal calls
        calls += 1
        return None if calls == 1 else await real(*args, **kwargs)

    monkeypatch.setattr(service, "_by_client_id", blind_once)
    again = await client.post(URL, json=bar(client_id=cid))
    assert again.status_code == 200 and again.json()["id"] == first.json()["id"]
    assert await db_session.scalar(select(func.count()).select_from(CustomFood)) == 1


async def test_portions_created_as_user_rows(client, consented, db_session):
    r = await client.post(
        URL,
        json=bar(
            portions=[
                {"unit": "piece", "grams_per_unit": 30},
                {"unit": "katori", "grams_per_unit": 120.5},
            ],
        ),
    )
    assert r.status_code == 201, r.text
    assert r.json()["portions"] == [
        {"unit": "piece", "grams_per_unit": 30.0},
        {"unit": "katori", "grams_per_unit": 120.5},
    ]
    rows = (await db_session.scalars(select(FoodPortion))).all()
    assert {(p.unit, p.source, p.account_id) for p in rows} == {
        ("piece", "user", ACC_A),
        ("katori", "user", ACC_A),
    }
    assert all(p.custom_food_id is not None for p in rows)


async def test_portion_units_refused(client, consented):
    for portions, code in (
        ([{"unit": "g", "grams_per_unit": 1}], "unit_not_supported"),
        ([{"unit": "serving", "grams_per_unit": 30}], "unit_not_supported"),
        (
            [{"unit": "piece", "grams_per_unit": 3}, {"unit": "piece", "grams_per_unit": 4}],
            "validation_error",
        ),
        ([{"unit": "piece", "grams_per_unit": 0}], "validation_error"),
        ([{"unit": "piece", "grams_per_unit": 2001}], "validation_error"),
        ([{"unit": "ladle", "grams_per_unit": 5}], "validation_error"),
    ):
        r = await client.post(URL, json=bar(portions=portions))
        assert r.status_code == 422 and r.json()["error"]["code"] == code, portions


async def test_ml_basis_with_density(client, consented):
    r = await client.post(
        URL,
        json=bar(name="Shake", basis="ml", density_g_per_ml=1.05, serving_g=300),
    )
    assert r.status_code == 201
    body = r.json()
    assert body["basis"] == "ml" and body["density_g_per_ml"] == 1.05
    assert body["serving_g"] == 300.0 and body["per_100"]["energy_kcal"] == 400.0


async def test_requires_consent(client, login):
    login(ACC_A)  # signed in, no consent
    r = await client.post(URL, json=bar())
    assert r.status_code == 403 and r.json()["error"]["code"] == "consent_required"
