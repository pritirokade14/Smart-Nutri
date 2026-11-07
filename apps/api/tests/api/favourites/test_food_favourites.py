"""favourites_list / favourites_add / favourites_delete for foods (Plan 12 Task 17; G23)."""

from uuid import uuid4

from sqlalchemy import select

from app.features.favourites.models import Favourite
from app.features.members import service as members_service
from tests.api.favourites.conftest import ACC_A, ACC_B, OFF_BARCODE, log_custom, make_custom

URL = "/v1/favourites"


async def test_add_returns_201_then_200(client, g1, db_session):
    cf = await make_custom(client)
    first = await client.post(URL, json={"custom_food_id": cf})
    assert first.status_code == 201, first.text
    body = first.json()
    assert body["kind"] == "food" and body["source_kind"] == "custom_food"
    assert body["custom_food_id"] == cf and body["name"] == "Protein bar"
    assert body["items"] is None and body["item_count"] == 1
    assert body["default_quantity"] is None and body["default_unit"] is None
    again = await client.post(
        URL, json={"custom_food_id": cf, "default_quantity": 2, "default_unit": "g"}
    )
    assert again.status_code == 200 and again.json()["id"] == body["id"]
    assert again.json()["default_unit"] is None  # unchanged: the stored favourite is returned
    n = len(list(await db_session.scalars(select(Favourite))))
    assert n == 1


async def test_add_with_default_portion_and_food_kinds(client, g1, dal, db_session):
    r = await client.post(
        URL, json={"food_id": str(dal.id), "default_quantity": 1.5, "default_unit": "katori"}
    )
    assert r.status_code == 201, r.text
    assert r.json()["source_kind"] == "food" and r.json()["default_unit"] == "katori"
    assert r.json()["default_quantity"] == 1.5
    assert r.json()["attributions"]  # the USDA credit is kept with the favourite
    off = await client.post(URL, json={"barcode": OFF_BARCODE})
    assert off.status_code == 201, off.text
    assert off.json()["source_kind"] == "off" and off.json()["barcode"] == OFF_BARCODE
    assert off.json()["attributions"] == ["Open Food Facts (ODbL)"] or off.json()["attributions"]


async def test_unit_that_cannot_convert_is_refused(client, g1, dal):
    # A roti of lentils has no weight: never guessed.
    r = await client.post(
        URL, json={"food_id": str(dal.id), "default_quantity": 1, "default_unit": "roti"}
    )
    assert r.status_code == 422 and r.json()["error"]["code"] == "unit_grams_unknown"
    half = await client.post(URL, json={"food_id": str(dal.id), "default_quantity": 1})
    assert half.status_code == 422 and half.json()["error"]["code"] == "validation_error"
    none = await client.post(URL, json={})
    assert none.json()["error"]["code"] == "invalid_product_ref"


async def test_retired_dish_is_not_starred(client, g1, dal, db_session):
    dal.review_status = "retired"
    await db_session.flush()
    r = await client.post(URL, json={"food_id": str(dal.id)})
    assert r.status_code == 422 and r.json()["error"]["code"] == "food_retired"


async def test_limit_200(client, g1, db_session):
    member = await members_service.get_or_create_primary(db_session, ACC_A)
    for i in range(200):
        db_session.add(
            Favourite(
                account_id=ACC_A,
                member_id=member.id,
                kind="food",
                source_kind="off",
                off_barcode=f"89{i:011d}",
                name=f"Food {i}",
            )
        )
    await db_session.flush()
    cf = await make_custom(client)
    r = await client.post(URL, json={"custom_food_id": cf})
    assert r.status_code == 422 and r.json()["error"]["code"] == "favourite_limit"
    assert len((await client.get(URL)).json()["items"]) == 200


async def test_list_newest_first(client, g1, clock):
    ids = []
    for i, minute in enumerate(("06:30", "06:40", "06:50")):
        clock.set(f"2026-11-07T{minute}:00+00:00")
        ids.append(
            (
                await client.post(
                    URL, json={"custom_food_id": await make_custom(client, f"Bar {i}")}
                )
            ).json()["id"]
        )
    items = (await client.get(URL)).json()["items"]
    assert [i["id"] for i in items] == ids[::-1]


async def test_recents_star_id(client, g1, slot_ids, clock):
    cf = await make_custom(client)
    other = await make_custom(client, "Other bar")
    await log_custom(client, cf, slot_ids["lunch"])
    await log_custom(client, other, slot_ids["lunch"])
    items = (await client.get("/v1/diary/recents")).json()["items"]
    assert [i["favourite_id"] for i in items] == [None, None]
    fav = (await client.post(URL, json={"custom_food_id": cf})).json()
    items = (await client.get("/v1/diary/recents")).json()["items"]
    by_id = {i["custom_food_id"]: i["favourite_id"] for i in items}
    assert by_id == {cf: fav["id"], other: None}
    assert (await client.delete(f"{URL}/{fav['id']}")).status_code == 204
    items = (await client.get("/v1/diary/recents")).json()["items"]
    assert all(i["favourite_id"] is None for i in items)


async def test_non_primary_422(client, g1, add_member):
    other = await add_member(ACC_A, name="Dad")
    cf = await make_custom(client)
    r = await client.post(URL, json={"member_id": str(other.id), "custom_food_id": cf})
    assert r.status_code == 422 and r.json()["error"]["code"] == "diary_member_not_enabled"
    r = await client.get(URL, params={"member_id": str(other.id)})
    assert r.status_code == 422 and r.json()["error"]["code"] == "diary_member_not_enabled"


async def test_other_account_404(client, g1, accounts, grant, login, add_member):
    cf = await make_custom(client)
    fav = (await client.post(URL, json={"custom_food_id": cf})).json()
    foreign = await add_member(ACC_B, name="Foreign")
    await grant(ACC_B)
    login(ACC_B)
    assert (await client.get(URL)).json()["items"] == []  # never listed
    r = await client.get(URL, params={"member_id": fav["member_id"]})
    assert r.status_code == 404 and r.json()["error"]["code"] == "member_not_found"
    assert foreign.id
    for call in (
        client.delete(f"{URL}/{fav['id']}"),
        client.delete(f"{URL}/{uuid4()}"),
        client.post(f"{URL}/{fav['id']}/log", json={"client_id": str(uuid4())}),
    ):
        r = await call
        assert r.status_code == 404 and r.json()["error"]["code"] == "favourite_not_found"
    # Another account's custom food cannot be starred either.
    r = await client.post(URL, json={"custom_food_id": cf})
    assert r.status_code == 404 and r.json()["error"]["code"] == "custom_food_not_found"


async def test_custom_food_delete_removes_its_favourite(client, g1):
    cf = await make_custom(client)
    await client.post(URL, json={"custom_food_id": cf})
    assert (await client.delete(f"/v1/custom-foods/{cf}")).status_code == 204
    assert (await client.get(URL)).json()["items"] == []


async def test_consent_gate_before_limit(client, login):
    login(ACC_A)  # no consent granted
    r = await client.get(URL)
    assert r.status_code == 403 and r.json()["error"]["code"] == "consent_required"
