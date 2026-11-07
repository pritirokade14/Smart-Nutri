"""custom_foods_update / custom_foods_delete (Plan 12 Task 11; G18, G21)."""

from pathlib import Path
from uuid import uuid4

from sqlalchemy import select, text

from app.features.meals.models import MealLog
from app.features.members import service as members_service
from tests.api.custom_foods.conftest import ACC_A, ACC_B, FakeOff, bar

URL = "/v1/custom-foods"
APP = Path(__file__).resolve().parents[3] / "app"


async def _create(client, **cols) -> dict:
    r = await client.post(URL, json=bar(**cols))
    assert r.status_code == 201, r.text
    return r.json()


async def test_put_replaces_and_can_clear_nutrient(client, consented):
    food = await _create(
        client, nutrients={"energy_kcal": 400, "protein_g": 30, "fat_g": 12, "fibre_g": 5},
        portions=[{"unit": "piece", "grams_per_unit": 30}],
    )  # fmt: skip
    assert food["per_100"]["fibre_g"] == 5.0
    r = await client.put(
        f"{URL}/{food['id']}",
        json=bar(
            name="Bar v2",
            nutrients={"energy_kcal": 380, "protein_g": 28},  # fat and fibre left out: unknown
            portions=[{"unit": "slice", "grams_per_unit": 15}],
        ),
    )
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["id"] == food["id"] and body["name"] == "Bar v2"
    assert body["per_100"]["fibre_g"] is None and body["per_100"]["fat_g"] is None
    assert body["per_100"]["energy_kcal"] == 380.0
    assert body["portions"] == [{"unit": "slice", "grams_per_unit": 15.0}]  # replaced
    assert body["entered"]["nutrients"]["fibre_g"] is None
    got = (await client.get(URL)).json()["items"]
    assert [i["name"] for i in got] == ["Bar v2"]


async def test_put_validates_like_create(client, consented):
    food = await _create(client, barcode="8901063201089")
    other = await _create(client, name="Other", barcode="8901234567890")
    url = f"{URL}/{food['id']}"
    assert (await client.put(url, json=bar(nutrients={}))).json()["error"]["code"] == (
        "custom_food_nutrients_empty"
    )
    dup = await client.put(url, json=bar(barcode=other["barcode"]))
    assert dup.status_code == 422 and dup.json()["error"]["code"] == "barcode_already_used"
    same = await client.put(url, json=bar(barcode=food["barcode"]))  # its own barcode is fine
    assert same.status_code == 200


async def test_delete_custom_food_keeps_history_and_recents_skip_it(
    client, consented, db_session, clock, slot_ids=None
):
    food = await _create(client)
    items = (await client.get("/v1/meal-slots")).json()["items"]
    slot = items[0]["id"]
    member = await members_service.get_or_create_primary(db_session, ACC_A)
    snapshot = {
        "name": "Protein bar", "brand": None, "basis": "g",
        "per_100": {"energy_kcal": 400.0, "protein_g": 30.0}, "units": {"g": 1.0},
        "attribution": None, "attributions": [], "licence": None, "source": "custom_food",
    }  # fmt: skip
    entry = MealLog(
        id=uuid4(), account_id=ACC_A, member_id=member.id, meal_slot_id=slot,
        source_kind="custom_food", custom_food_id=food["id"], product_name="Protein bar",
        grams=60.0, nutrients={"energy_kcal": 240.0}, food_snapshot=snapshot,
        eaten_at=clock.now, local_date=clock.now.date(),
    )  # fmt: skip
    db_session.add(entry)
    await db_session.flush()

    assert (await client.delete(f"{URL}/{food['id']}")).status_code == 204
    await db_session.refresh(entry)
    assert entry.custom_food_id is None  # the entry stays ...
    assert entry.product_name == "Protein bar" and entry.nutrients == {"energy_kcal": 240.0}
    assert entry.food_snapshot["per_100"]["protein_g"] == 30.0  # ... with its own values
    assert (await client.get(URL)).json()["items"] == []
    recents = await client.get("/v1/diary/recents")
    assert recents.status_code == 200 and recents.json()["items"] == []  # nothing to log again
    assert (await client.delete(f"{URL}/{food['id']}")).status_code == 404
    left = await db_session.scalar(select(MealLog).where(MealLog.id == entry.id))
    assert left is not None


async def test_other_account_404(client, consented, grant, login):
    food = await _create(client)
    await grant(ACC_B)
    login(ACC_B)
    assert (await client.get(URL)).json()["items"] == []  # never listed
    for call in (
        client.put(f"{URL}/{food['id']}", json=bar()),
        client.delete(f"{URL}/{food['id']}"),
        client.put(f"{URL}/{uuid4()}", json=bar()),
    ):
        r = await call
        assert r.status_code == 404 and r.json()["error"]["code"] == "custom_food_not_found"
    login(ACC_A)
    assert len((await client.get(URL)).json()["items"]) == 1  # untouched


async def test_custom_food_never_reaches_analyze(client, consented, db_session, login):
    """The import graph: neither the rules engine nor `analyze` imports custom foods; and the
    product lookup by barcode for a custom food's barcode finds nothing."""
    for pkg in (APP / "scoring", APP / "features" / "analyze"):
        for path in pkg.rglob("*.py"):
            src = path.read_text()
            assert "custom_foods" not in src and "custom_food" not in src, path
    code = "8901063201089"
    await _create(client, barcode=code)
    login(ACC_A, off=FakeOff(fail=True))  # Open Food Facts down: only OUR catalogue can answer
    r = await client.get(f"/v1/products/barcode/{code}")
    assert r.status_code in (404, 503) and r.json()["error"]["code"] != "custom_food_not_found"
    assert r.json().get("name") != "Protein bar"
    n = await db_session.scalar(
        text("select count(*) from products where barcode = :b"), {"b": code}
    )
    assert n == 0  # never in the public catalogue
