"""foods_search (Plan 12 Task 4; G16): generic foods and dishes first, then packaged."""

import pytest
from sqlalchemy import func, select, text

from app.features.foods.service import rank
from app.features.products.models import Product
from tests.api.foods.conftest import ACC_A, OFF_PAYLOAD, FakeOff

URL = "/v1/foods/search"
NUTRIENTS = {
    "energy_kcal", "protein_g", "carbs_g", "fat_g", "fibre_g", "sugars_g", "salt_g",
    "sat_fat_g", "per_100", "nutrients",
}  # fmt: skip


async def _search(client, q, **params):
    r = await client.get(URL, params={"q": q, **params})
    assert r.status_code == 200, r.text
    return r.json()


async def test_search_finds_dish_by_alias(client, consented, seeded, food_ids):
    j = await _search(client, "dal")
    by_id = {i["id"]: i for i in j["items"]}
    dish = by_id[food_ids["dal_tadka"]]
    assert dish["name"] == "Dal tadka (toor)" and dish["is_dish"] is True
    assert dish["group"] == "indian" and dish["kind"] == "food"
    fdc = by_id[food_ids["172437"]]  # cooked pigeon peas: the alias "dal"
    assert fdc["is_dish"] is False and fdc["group"] == "indian"
    assert j["partial"] is False and j["failed_sources"] == []


async def test_indian_before_packaged(client, consented, seeded, db_session, login):
    db_session.add(
        Product(
            name="Dal Makhani ready meal",
            brand="Acme",
            category="general",
            source="label",
            verification_status="verified",
            per_100g={"energy_kcal": 120},
        )
    )
    await db_session.flush()
    login(ACC_A, off=FakeOff(text=[OFF_PAYLOAD | {"product_name": "OFF Dal fry"}]))
    j = await _search(client, "dal", limit=50)
    groups = [i["group"] for i in j["items"]]
    assert "packaged" in groups and "indian" in groups
    assert groups == sorted(groups, key=lambda g: g != "indian")  # every indian hit first
    packaged = [i for i in j["items"] if i["group"] == "packaged"]
    assert {p["kind"] for p in packaged} == {"product", "off"}
    ours = next(p for p in packaged if p["kind"] == "product")
    assert ours["name"] == "Dal Makhani ready meal" and ours["brand"] == "Acme"


async def test_rank_prefix_first(client, consented, seeded):
    j = await _search(client, "rice", kinds="food", limit=50)
    names = [i["name"] for i in j["items"]]
    assert len(names) > 3
    ranks = [rank("rice", n, n.lower()) for n in names]
    assert ranks == sorted(ranks)  # name prefix, then word prefix, then substring
    assert names[0].lower().startswith("rice")
    assert rank("rice", "Plain rice, boiled", "plain rice, boiled chawal") == 1
    assert rank("ice", "Plain rice, boiled", "plain rice, boiled") == 2
    # Within a rank: the shorter name first.
    same = [n for n, r in zip(names, ranks, strict=True) if r == 0]
    assert same == sorted(same, key=lambda n: (len(n), n))


async def test_query_too_short(client, consented, db_session):
    for q in ("a", " a ", "  "):
        r = await client.get(URL, params={"q": q})
        assert r.status_code == 422, q
        assert r.json()["error"]["code"] == "search_query_too_short"
    used = await db_session.scalar(select(func.count()).select_from(text("rate_limit_counters")))
    assert used == 0  # a refused query costs no quota
    r = await client.get(URL, params={"q": "da"})  # two characters are enough
    assert r.status_code == 200
    assert (await client.get(URL, params={"q": "x" * 81})).status_code == 422
    assert (await client.get(URL)).status_code == 422


async def test_off_down_returns_partial(client, consented, seeded, login):
    login(ACC_A, off=FakeOff(fail=True))
    j = await _search(client, "dal")
    assert j["partial"] is True and j["failed_sources"] == ["off"]
    assert any(i["group"] == "indian" for i in j["items"])  # foods still returned


async def test_off_throttled_returns_partial_not_503(client, consented, seeded, login, app):
    from app.integrations.openfoodfacts import OffThrottled

    class Throttled(FakeOff):
        async def search_text(self, query, page_size=20):
            raise OffThrottled(7)

    login(ACC_A, off=Throttled())
    r = await client.get(URL, params={"q": "dal"})
    assert r.status_code == 200
    assert r.json()["partial"] is True and r.json()["items"]


async def test_hits_have_no_nutrients(client, consented, seeded, login):
    login(ACC_A, off=FakeOff(text=[OFF_PAYLOAD]))
    j = await _search(client, "dal", limit=50)
    assert j["items"]
    for hit in j["items"]:
        assert not NUTRIENTS & set(hit), hit
    assert set(j) == {"items", "partial", "failed_sources"}  # no cursor


async def test_attribution_on_hits(client, consented, seeded, login, food_ids):
    login(ACC_A, off=FakeOff(text=[OFF_PAYLOAD]))
    j = await _search(client, "dal", limit=50)
    by_id = {i["id"]: i for i in j["items"]}
    assert by_id[food_ids["172437"]]["attribution"] == "attribution.usda_fdc"
    assert by_id[food_ids["172437"]]["attributions"] == ["attribution.usda_fdc"]
    dish = by_id[food_ids["dal_tadka"]]
    assert dish["attribution"] == "attribution.smartnutri_recipe"
    assert "attribution.usda_fdc" in dish["attributions"]  # the dish credits its ingredients too
    off = await _search(client, "namkeen", kinds="product")
    [hit] = [i for i in off["items"] if i["kind"] == "off"]
    assert hit["attribution"] == "attribution.off" and hit["attributions"] == ["attribution.off"]
    assert hit["id"] == "8901063201089"


async def test_kinds_and_limit(client, consented, seeded, login):
    off = FakeOff(text=[OFF_PAYLOAD])
    login(ACC_A, off=off)
    j = await _search(client, "dal", kinds="food", limit=3)
    assert len(j["items"]) == 3 and off.search_calls == []  # no OFF call for kinds=food
    j = await _search(client, "namkeen", kinds="product")
    assert {i["group"] for i in j["items"]} == {"packaged"}
    assert (await client.get(URL, params={"q": "dal", "kinds": "recipe"})).status_code == 422
    assert (await client.get(URL, params={"q": "dal", "limit": 51})).status_code == 422
    j = await _search(client, "dal", limit=4)
    assert len(j["items"]) <= 4


async def test_like_wildcards_are_escaped(client, consented, seeded):
    j = await _search(client, "%%", kinds="food")
    assert j["items"] == []


@pytest.mark.parametrize("q", ["दाल"])
async def test_unmatched_query_is_empty_not_an_error(client, consented, seeded, q):
    j = await _search(client, q, kinds="food")
    assert j["items"] == [] and j["partial"] is False
