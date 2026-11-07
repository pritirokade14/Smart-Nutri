"""favourites_add_meal (Plan 12 Task 17; G23): a saved meal keeps its entries as they were."""

import json
import logging

from app.integrations import posthog
from tests.api.favourites.conftest import log_custom, make_custom, save_meal

URL = "/v1/favourites"
NAME = "संध्याकाळचा नाश्ता ☕"


async def test_save_meal_snapshots_slot_entries(client, g1, slot_ids, clock):
    cf = await make_custom(client)
    clock.set("2026-11-07T04:00:00+00:00")
    await log_custom(client, cf, slot_ids["breakfast"], grams=50)
    clock.set("2026-11-07T04:05:00+00:00")
    await client.post(
        "/v1/meals",
        json={"quick": {"name": "Chai", "energy_kcal": 80}, "meal_slot_id": slot_ids["breakfast"]},
    )
    clock.set("2026-11-07T06:30:00+00:00")
    await log_custom(client, cf, slot_ids["lunch"], grams=100)  # another slot: not saved
    r = await save_meal(client, slot_ids["breakfast"])
    assert r.status_code == 201, r.text
    body = r.json()
    assert body["kind"] == "meal" and body["name"] == "My usual breakfast"
    assert body["source_kind"] is None and body["custom_food_id"] is None
    assert body["item_count"] == 2
    assert [(i["name"], i["source_kind"], i["grams"]) for i in body["items"]] == [
        ("Protein bar", "custom_food", 50.0),
        ("Chai", "quick_add", None),
    ]
    assert not any(k in json.dumps(body) for k in ("energy_kcal", "protein_g"))  # no numbers
    listing = (await client.get(URL)).json()["items"]
    assert [f["id"] for f in listing] == [body["id"]]


async def test_snapshot_survives_deleting_the_food(client, g1, slot_ids, clock):
    cf = await make_custom(client)
    await log_custom(client, cf, slot_ids["breakfast"])
    fav = (await save_meal(client, slot_ids["breakfast"])).json()
    await client.delete(f"/v1/custom-foods/{cf}")
    listing = (await client.get(URL)).json()["items"]
    assert [f["id"] for f in listing] == [fav["id"]]  # a meal keeps its snapshots
    assert listing[0]["items"][0]["name"] == "Protein bar"


async def test_empty_slot_copy_source_empty(client, g1, slot_ids, clock):
    r = await save_meal(client, slot_ids["breakfast"])
    assert r.status_code == 422 and r.json()["error"]["code"] == "copy_source_empty"


async def test_errors(client, g1, slot_ids, clock):
    from uuid import uuid4

    r = await save_meal(client, slot_ids["breakfast"], day="2026-11-08")
    assert r.status_code == 422 and r.json()["error"]["code"] == "date_in_future"
    r = await save_meal(client, str(uuid4()))
    assert r.status_code == 404 and r.json()["error"]["code"] == "meal_slot_not_found"
    for name in ("", "   ", "x" * 41):
        r = await save_meal(client, slot_ids["breakfast"], name=name)
        assert r.status_code == 422 and r.json()["error"]["code"] == "validation_error", name
    cf = await make_custom(client)
    for _ in range(51):
        await log_custom(client, cf, slot_ids["snack"], grams=10)
    r = await save_meal(client, slot_ids["snack"])
    assert r.status_code == 422 and r.json()["error"]["code"] == "copy_too_many"


async def test_name_kept_exactly_and_client_id_retry(client, g1, slot_ids, clock, db_session):
    cf = await make_custom(client)
    await log_custom(client, cf, slot_ids["breakfast"])
    name = f"  {NAME}  "  # no trimming: user text
    cid = "7b0d9a4e-0000-4000-8000-000000000001"
    r = await save_meal(client, slot_ids["breakfast"], name=name, client_id=cid)
    assert r.status_code == 201 and r.json()["name"] == name
    assert r.json()["name"].encode() == name.encode()
    again = await save_meal(client, slot_ids["breakfast"], name=name, client_id=cid)
    assert again.status_code == 200 and again.json()["id"] == r.json()["id"]
    assert len((await client.get(URL)).json()["items"]) == 1
    forty = await save_meal(client, slot_ids["breakfast"], name="é" * 40)  # 40 code points
    assert forty.status_code == 201


class _Spy:
    def __init__(self):
        self.captured: list = []

    def capture(self, *args, **kwargs):
        self.captured.append((args, kwargs))


async def test_name_kept_as_typed_and_never_in_analytics_or_logs(
    client, g1, slot_ids, clock, monkeypatch, caplog
):
    spy = _Spy()
    monkeypatch.setattr(posthog, "_client", spy)
    cf = await make_custom(client)
    await log_custom(client, cf, slot_ids["breakfast"])
    with caplog.at_level(logging.DEBUG):
        r = await save_meal(client, slot_ids["breakfast"], name=NAME)
        fav_id = r.json()["id"]
        await save_meal(client, slot_ids["breakfast"], name="")  # a refused name
        too_long = await save_meal(client, slot_ids["breakfast"], name=NAME * 5)
        await client.post(
            f"{URL}/{fav_id}/log", json={"client_id": "7b0d9a4e-0000-4000-8000-000000000002"}
        )
        await client.get(URL)
        await client.delete(f"{URL}/{fav_id}")
    assert r.json()["name"] == NAME
    assert "संध्या" not in too_long.text  # never echoed in an error
    assert "संध्या" not in json.dumps(spy.captured, ensure_ascii=False, default=str)
    assert "संध्या" not in caplog.text
    assert "संध्या" not in "".join(str(x.args) + x.getMessage() for x in caplog.records)
