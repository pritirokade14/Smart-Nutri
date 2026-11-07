"""Quick add (Plan 11 Task 4; Ruling E11): typed kcal and macros, blanks stay unknown."""

import pytest

pytestmark = pytest.mark.usefixtures("family")

URL = "/v1/meals"
UNKNOWN_WHEN_KCAL_ONLY = [
    "protein_g",
    "fat_g",
    "carbs_g",
    "fibre_g",
    "sugars_g",
    "salt_g",
    "sat_fat_g",
]


async def test_quick_kcal_only(client, family):
    r = await client.post(URL, json={"member_id": str(family.me), "quick": {"energy_kcal": 450}})
    assert r.status_code == 201, r.text
    j = r.json()
    assert j["source_kind"] == "quick_add" and j["grams"] is None
    assert j["product_id"] is None and j["barcode"] is None and j["grade"] is None
    assert j["nutrients"]["energy_kcal"] == 450.0
    assert j["nutrients"]["protein_g"] is None  # never 0
    assert set(UNKNOWN_WHEN_KCAL_ONLY) <= set(j["incomplete"])
    assert "energy_kcal" not in j["incomplete"]
    assert j["product_name"] == "" and j["attribution"] is None


async def test_quick_with_macros(client, family):
    quick = {"energy_kcal": 300, "protein_g": 10, "fat_g": 0, "carbs_g": 40.5, "fibre_g": 3}
    j = (await client.post(URL, json={"quick": quick})).json()
    assert j["nutrients"]["fat_g"] == 0.0  # a typed zero is a value, not unknown
    assert j["nutrients"]["carbs_g"] == 40.5
    assert sorted(j["incomplete"]) == ["salt_g", "sat_fat_g", "sugars_g"]


async def test_quick_without_energy_422(client, family):
    for quick in ({}, {"protein_g": 10}, {"name": "Chai"}):
        r = await client.post(URL, json={"member_id": str(family.me), "quick": quick})
        assert r.status_code == 422, quick
        assert r.json()["error"]["code"] == "quick_add_energy_required"


async def test_quick_with_grams_422(client, family):
    for extra in ({"grams": 30}, {"servings": 1}):
        r = await client.post(
            URL, json={"member_id": str(family.me), "quick": {"energy_kcal": 100}, **extra}
        )
        assert r.status_code == 422 and r.json()["error"]["code"] == "validation_error"
        assert r.json()["error"]["details"]["fields"] == [f"body.{next(iter(extra))}"]


@pytest.mark.parametrize(
    "quick",
    [
        {"energy_kcal": 5001},
        {"energy_kcal": 0},
        {"energy_kcal": -5},
        {"energy_kcal": 100, "protein_g": 501},
        {"energy_kcal": 100, "fat_g": -1},
        {"energy_kcal": 100, "carbs_g": 500.1},
        {"energy_kcal": 100, "fibre_g": 201},
        {"energy_kcal": 100, "name": "x" * 61},
    ],
)
async def test_quick_bounds(client, family, quick):
    r = await client.post(URL, json={"member_id": str(family.me), "quick": quick})
    assert r.status_code == 422 and r.json()["error"]["code"] == "validation_error"


async def test_quick_bounds_accept_the_limits(client, family):
    quick = {"energy_kcal": 5000, "protein_g": 500, "fat_g": 500, "carbs_g": 500, "fibre_g": 200}
    assert (await client.post(URL, json={"quick": quick})).status_code == 201


async def test_quick_name_is_user_text(client, family, db_session):
    r = await client.post(URL, json={"quick": {"energy_kcal": 120, "name": "  Evening chai ☕  "}})
    assert r.json()["product_name"] == "Evening chai ☕"
    blank = await client.post(URL, json={"quick": {"energy_kcal": 120, "name": "   "}})
    assert blank.json()["product_name"] == ""


async def test_quick_and_product_together_422(client, family, sf_biscuit_product_id):
    r = await client.post(
        URL,
        json={
            "member_id": str(family.me),
            "product_id": str(sf_biscuit_product_id),
            "quick": {"energy_kcal": 100},
        },
    )
    assert r.status_code == 422 and r.json()["error"]["code"] == "invalid_product_ref"
    none = await client.post(URL, json={"member_id": str(family.me), "grams": 10})
    assert none.json()["error"]["code"] == "invalid_product_ref"


async def test_quick_idempotent_by_client_id(client, family):
    from uuid import uuid4

    body = {"quick": {"energy_kcal": 100}, "client_id": str(uuid4())}
    a = await client.post(URL, json=body)
    b = await client.post(URL, json=body)
    assert (a.status_code, b.status_code) == (201, 200) and a.json()["id"] == b.json()["id"]
