"""foods_by_barcode (Plan 12 Task 13; G17): the barcode for LOGGING. Custom foods are found
here only; the verdict routes never see them."""

import pytest

from tests.api.foods.conftest import ACC_A, ACC_B, OFF_BARCODE, FakeOff

URL = "/v1/foods/barcode"
CODE = "8901234567890"


async def _custom(client, barcode=CODE, **cols):
    body = {
        "name": "My bar", "basis": "g", "values_per": "100", "barcode": barcode,
        "nutrients": {"energy_kcal": 400, "protein_g": 30},
    } | cols  # fmt: skip
    r = await client.post("/v1/custom-foods", json=body)
    assert r.status_code == 201, r.text
    return r.json()


async def test_own_custom_food_first(client, consented):
    food = await _custom(client, barcode=OFF_BARCODE)  # also an OFF barcode: yours wins
    r = await client.get(f"{URL}/{OFF_BARCODE}")
    assert r.status_code == 200, r.text
    d = r.json()
    assert (d["kind"], d["id"], d["name"]) == ("custom_food", food["id"], "My bar")
    assert d["per_100"]["energy_kcal"] == 400.0 and d["attribution"] is None
    assert {u["code"] for u in d["units"]} >= {"g"}
    spaced = await client.get(f"{URL}/{OFF_BARCODE[:4]}-{OFF_BARCODE[4:]}")
    assert spaced.json()["id"] == food["id"]  # normalised like every barcode


async def test_falls_back_to_product(client, consented, db_session, login):
    from scripts.export_fixture_responses import fixture_product_record

    record = fixture_product_record("sf_biscuit")
    record.barcode = "8901719101168"
    db_session.add(record)
    await db_session.flush()
    off = FakeOff(fail=True)  # OFF is never needed for our own catalogue
    login(ACC_A, off=off)
    r = await client.get(f"{URL}/{record.barcode}")
    assert r.status_code == 200, r.text
    d = r.json()
    assert (d["kind"], d["id"]) == ("product", str(record.id)) and off.calls == 0
    # No custom food, no product of ours: Open Food Facts answers.
    login(ACC_A)
    r = await client.get(f"{URL}/{OFF_BARCODE}")
    assert r.status_code == 200 and r.json()["kind"] == "off"
    assert r.json()["attributions"] == ["attribution.off"]


async def test_other_account_custom_barcode_not_used(client, consented, grant, login):
    await _custom(client, barcode=OFF_BARCODE, name="A's own")
    await grant(ACC_B)
    login(ACC_B)
    r = await client.get(f"{URL}/{OFF_BARCODE}")
    assert r.status_code == 200
    assert r.json()["kind"] == "off" and r.json()["name"] != "A's own"  # never A's food
    await _custom(client, barcode=CODE, name="B's own")  # B's own barcode is B's food
    assert (await client.get(f"{URL}/{CODE}")).json()["name"] == "B's own"
    login(ACC_A, off=FakeOff(payload=None))  # A has no food with this barcode, OFF knows none
    r = await client.get(f"{URL}/{CODE}")
    assert r.status_code == 404 and r.json()["error"]["code"] == "product_not_found"


async def test_errors(client, consented, login):
    r = await client.get(f"{URL}/12ab")
    assert r.status_code == 422 and r.json()["error"]["code"] == "invalid_barcode"
    login(ACC_A, off=FakeOff(fail=True))
    r = await client.get(f"{URL}/{OFF_BARCODE}")
    assert r.status_code == 503 and r.json()["error"]["code"] == "off_unavailable"
    # A custom food answers even when OFF is down.
    await _custom(client, barcode=OFF_BARCODE)
    assert (await client.get(f"{URL}/{OFF_BARCODE}")).status_code == 200


@pytest.mark.parametrize("path", ["/v1/products/barcode/{c}"])
async def test_verdict_routes_never_see_custom_foods(client, consented, login, path):
    await _custom(client, barcode=CODE)
    login(ACC_A, off=FakeOff(payload=None))
    r = await client.get(path.format(c=CODE))
    assert r.status_code == 404 and r.json()["error"]["code"] == "product_not_found"
    r = await client.post("/v1/analyze", json={"barcode": CODE})
    assert r.status_code in (404, 422), r.text
    assert r.json()["error"]["code"] != "custom_food_not_found"
    assert "My bar" not in r.text


async def test_requires_consent(client, login):
    login(ACC_A)
    r = await client.get(f"{URL}/{CODE}")
    assert r.status_code == 403 and r.json()["error"]["code"] == "consent_required"
