"""GET /v1/diary/recents (Plan 11 Task 7; Ruling E18)."""

from datetime import UTC, date, datetime, timedelta, timezone
from uuid import uuid4

from app.features.meals.models import MealLog
from app.features.members import service as members_service
from tests.api.diary.conftest import ACC_A

URL = "/v1/diary/recents"
IST = timezone(timedelta(hours=5, minutes=30))


def _off(member, slot, barcode, at, *, name="OFF thing", grams=30.0, day=None):
    return MealLog(
        id=uuid4(),
        account_id=ACC_A,
        member_id=member.id,
        meal_slot_id=slot,
        source_kind="off",
        off_barcode=barcode,
        product_name=name,
        grams=grams,
        nutrients={},
        eaten_at=at,
        local_date=day or at.astimezone(IST).date(),
    )


async def test_recents_dedupe_and_order(client, g1, db_session, slot_ids, product_id, clock):
    member = await members_service.get_or_create_primary(db_session, ACC_A)
    lunch = slot_ids["lunch"]
    # The same product three times (newest wins), then another, then an OFF barcode.
    await client.post(
        "/v1/meals",
        json={
            "product_id": str(product_id),
            "grams": 10,
            "local_date": "2026-11-04",
            "meal_slot_id": lunch,
        },
    )
    newest = await client.post(
        "/v1/meals",
        json={
            "product_id": str(product_id),
            "grams": 40,
            "local_date": "2026-11-06",
            "meal_slot_id": lunch,
        },
    )
    db_session.add(
        _off(member, lunch, "8901", datetime(2026, 11, 5, 8, 0, tzinfo=IST), name="Namkeen")
    )
    db_session.add(
        _off(member, lunch, "8901", datetime(2026, 11, 3, 8, 0, tzinfo=IST), name="Namkeen")
    )
    await db_session.flush()
    items = (await client.get(URL)).json()["items"]
    assert [(i["source_kind"], i["product_id"] or i["barcode"]) for i in items] == [
        ("product", str(product_id)),
        ("off", "8901"),
    ]
    assert items[0]["grams"] == 40.0 and items[0]["last_eaten_at"] == newest.json()["eaten_at"]
    assert items[1]["grams"] == 30.0 and items[1]["name"] == "Namkeen"


async def test_recents_slot_first(client, g1, db_session, slot_ids, clock):
    member = await members_service.get_or_create_primary(db_session, ACC_A)
    newer_in_lunch = _off(
        member, slot_ids["lunch"], "8001", datetime(2026, 11, 6, 13, 0, tzinfo=IST)
    )
    older_in_dinner = _off(
        member, slot_ids["dinner"], "8002", datetime(2026, 11, 5, 20, 0, tzinfo=IST)
    )
    db_session.add_all([newer_in_lunch, older_in_dinner])
    await db_session.flush()
    plain = [i["barcode"] for i in (await client.get(URL)).json()["items"]]
    assert plain == ["8001", "8002"]
    first_dinner = (await client.get(URL, params={"slot_id": slot_ids["dinner"]})).json()["items"]
    assert [i["barcode"] for i in first_dinner] == ["8002", "8001"]
    ghost = await client.get(URL, params={"slot_id": str(uuid4())})
    assert ghost.status_code == 404 and ghost.json()["error"]["code"] == "meal_slot_not_found"


async def test_recents_exclude_quick_add(client, g1, slot_ids, clock):
    await client.post("/v1/meals", json={"quick": {"energy_kcal": 300, "name": "Chai"}})
    assert (await client.get(URL)).json() == {"items": []}


async def test_recents_max_30(client, g1, db_session, slot_ids, clock):
    member = await members_service.get_or_create_primary(db_session, ACC_A)
    for i in range(35):
        at = datetime(2026, 11, 6, 0, 0, tzinfo=IST) + timedelta(minutes=i)
        db_session.add(_off(member, slot_ids["lunch"], f"89{i:04d}", at))
    await db_session.flush()
    items = (await client.get(URL)).json()["items"]
    assert len(items) == 30
    assert items[0]["barcode"] == "890034"  # newest first
    assert len((await client.get(URL, params={"limit": 5})).json()["items"]) == 5
    assert (await client.get(URL, params={"limit": 31})).status_code == 422
    assert (await client.get(URL, params={"limit": 0})).status_code == 422


async def test_recents_last_90_days_only(client, g1, db_session, slot_ids, clock):
    member = await members_service.get_or_create_primary(db_session, ACC_A)
    today = date(2026, 11, 7)
    db_session.add(
        _off(
            member,
            slot_ids["lunch"],
            "7001",
            datetime(2026, 8, 10, 12, 0, tzinfo=IST),
            day=today - timedelta(days=89),
        )  # in
    )
    db_session.add(
        _off(
            member,
            slot_ids["lunch"],
            "7002",
            datetime(2026, 8, 9, 12, 0, tzinfo=IST),
            day=today - timedelta(days=90),
        )  # out
    )
    await db_session.flush()
    assert [i["barcode"] for i in (await client.get(URL)).json()["items"]] == ["7001"]


async def test_recents_off_attribution(client, g1, db_session, slot_ids, product_id, clock):
    member = await members_service.get_or_create_primary(db_session, ACC_A)
    db_session.add(
        _off(member, slot_ids["lunch"], "8003", datetime(2026, 11, 6, 13, 0, tzinfo=IST))
    )
    await client.post(
        "/v1/meals",
        json={"product_id": str(product_id), "grams": 20, "local_date": "2026-11-05"},
    )
    await db_session.flush()
    by_kind = {i["source_kind"]: i for i in (await client.get(URL)).json()["items"]}
    assert by_kind["off"]["attribution"] == "attribution.off"
    assert by_kind["product"]["attribution"] is None


# ---- Plan 12 Task 5: generic foods, quantity and unit


async def test_recents_dedupe_by_food(client, g1, slot_ids, food_ids, clock):
    dal, roti = food_ids["172437"], food_ids["171844"]
    for day, food, body in (
        ("2026-11-04", dal, {"quantity": 1, "unit": "katori"}),
        ("2026-11-05", roti, {"quantity": 2, "unit": "roti"}),
        ("2026-11-06", dal, {"grams": 100}),
    ):
        r = await client.post(
            "/v1/meals",
            json={"food_id": food, "local_date": day, "meal_slot_id": slot_ids["lunch"], **body},
        )
        assert r.status_code == 201, r.text
    j = (await client.get(URL)).json()
    assert [(i["source_kind"], i["food_id"]) for i in j["items"]] == [
        ("food", dal),  # the newest entry of dal; the 4 Nov one is folded in
        ("food", roti),
    ]
    assert all(i["product_id"] is None and i["barcode"] is None for i in j["items"])
    assert j["items"][0]["attributions"] == ["attribution.usda_fdc"]


async def test_recents_carry_quantity_unit(client, g1, slot_ids, food_ids, clock):
    r = await client.post(
        "/v1/meals",
        json={
            "food_id": food_ids["172437"],
            "quantity": 1.5,
            "unit": "katori",
            "meal_slot_id": slot_ids["lunch"],
        },
    )
    assert r.status_code == 201, r.text
    [item] = (await client.get(URL)).json()["items"]
    assert (item["quantity"], item["unit"], item["grams"]) == (1.5, "katori", 213.0)
    assert item["name"].startswith("Pigeon peas") and item["grade"] is None


async def test_legacy_rows_have_null_unit(client, g1, db_session, slot_ids, clock):
    member = await members_service.get_or_create_primary(db_session, ACC_A)
    at = datetime(2026, 11, 6, 7, 0, tzinfo=UTC)
    db_session.add(_off(member, slot_ids["lunch"], "8901", at, name="Legacy namkeen", grams=30.0))
    await db_session.flush()
    [item] = (await client.get(URL)).json()["items"]
    assert item["source_kind"] == "off" and item["barcode"] == "8901"
    assert item["quantity"] is None and item["unit"] is None and item["food_id"] is None
    assert item["attributions"] == ["attribution.off"]


# ---- Plan 12 slice 4: custom foods, recipes and the resolved amount


async def _custom(client, **cols):
    body = {
        "name": "Protein bar", "basis": "g", "values_per": "100",
        "nutrients": {"energy_kcal": 400, "protein_g": 30},
    } | cols  # fmt: skip
    r = await client.post("/v1/custom-foods", json=body)
    assert r.status_code == 201, r.text
    return r.json()


async def test_recents_include_custom_and_recipe(client, g1, slot_ids, clock):
    food = await _custom(client, name="Bar", density_g_per_ml=0.8)
    recipe = (
        await client.post(
            "/v1/recipes",
            json={
                "name": "Stew", "servings": 2,
                "ingredients": [{"custom_food_id": food["id"], "quantity": 100, "unit": "g"}],
            },
        )
    ).json()  # fmt: skip
    shake = await _custom(client, name="Shake", basis="ml")
    for ref, portion in (
        ({"custom_food_id": food["id"]}, {"quantity": 1, "unit": "katori"}),
        ({"recipe_id": recipe["id"]}, {"servings": 1}),
        ({"custom_food_id": shake["id"]}, {"quantity": 200, "unit": "ml"}),
    ):
        r = await client.post(
            "/v1/meals", json={**ref, **portion, "meal_slot_id": slot_ids["lunch"]}
        )
        assert r.status_code == 201, r.text
    items = (await client.get(URL)).json()["items"]
    by = {i["name"]: i for i in items}
    assert set(by) == {"Bar", "Stew", "Shake"}
    bar = by["Bar"]
    assert (bar["source_kind"], bar["custom_food_id"], bar["recipe_id"]) == (
        "custom_food",
        food["id"],
        None,
    )
    assert (bar["unit"], bar["unit_source"], bar["basis"]) == ("katori", "density", "g")
    assert bar["grams"] == 160.0  # resolved: "1 katori" is 160 g of this food
    stew = by["Stew"]
    assert (stew["source_kind"], stew["recipe_id"], stew["grams"]) == ("recipe", recipe["id"], 50.0)
    shake_item = by["Shake"]
    assert (shake_item["basis"], shake_item["grams"], shake_item["unit"]) == ("ml", 200.0, "ml")
    # Log one again from its recents shape.
    again = await client.post(
        "/v1/meals",
        json={
            "custom_food_id": bar["custom_food_id"], "quantity": bar["quantity"],
            "unit": bar["unit"], "meal_slot_id": slot_ids["dinner"],
        },
    )  # fmt: skip
    assert again.status_code == 201


async def test_recents_skip_null_refs(client, g1, slot_ids, db_session, clock):
    food = await _custom(client)
    recipe = (
        await client.post(
            "/v1/recipes",
            json={
                "name": "Stew", "servings": 1,
                "ingredients": [{"custom_food_id": food["id"], "quantity": 100, "unit": "g"}],
            },
        )
    ).json()  # fmt: skip
    for ref in ({"custom_food_id": food["id"]}, {"recipe_id": recipe["id"]}):
        r = await client.post(
            "/v1/meals", json={**ref, "grams": 50, "meal_slot_id": slot_ids["lunch"]}
        )
        assert r.status_code == 201
    assert len((await client.get(URL)).json()["items"]) == 2
    assert (await client.delete(f"/v1/custom-foods/{food['id']}")).status_code == 204
    assert (await client.delete(f"/v1/recipes/{recipe['id']}")).status_code == 204
    assert (await client.get(URL)).json()["items"] == []  # nothing left to log again
    assert len((await client.get("/v1/meals")).json()) == 2  # the entries themselves stay


async def test_recents_basis_and_unit_source_for_foods(client, g1, slot_ids, food_ids, clock):
    r = await client.post(
        "/v1/meals",
        json={
            "food_id": food_ids["171844"],
            "quantity": 2,
            "unit": "roti",
            "meal_slot_id": slot_ids["lunch"],
        },
    )
    assert r.status_code == 201
    item = (await client.get(URL)).json()["items"][0]
    assert (item["basis"], item["unit"], item["quantity"], item["grams"]) == (
        "g",
        "roti",
        2.0,
        136.0,
    )
    assert item["unit_source"] == "portion"  # "2 rotis" is 136 g by a per-piece weight: approximate
