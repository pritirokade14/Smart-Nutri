# ruff: noqa: F811  (fixtures imported from the discovery conftest, used by name)
"""Plan 9 Task 6: the higher-protein sort (alternatives and search) and protein compare columns.

Never `avoid` for the member (member_id, else the primary member), never a worse grade, and
every protein number from the engine's report.protein. Missing is `unknown`, never a win.
"""

import pytest
from sqlalchemy import select

from app.features.members.models import Member
from tests.api.discovery.conftest import (  # noqa: F401  (shared fixtures)
    NAMKEEN,
    NAMKEEN_BARCODE,
    fake_off,
    family,
    label_only_product_id,
    login,
    oats_product_id,
    other_account_member_id,
    sf_biscuit_product_id,
)
from tests.api.meals.conftest import ACC_A, FakeOff

pytestmark = pytest.mark.usefixtures("family")

NAMKEEN_URL = f"/v1/products/barcode/{NAMKEEN_BARCODE}/alternatives"
# Namkeen (source, grade E, 2.5 g protein per 100 kcal). Higher-protein candidates in the
# category: Roasted Chana (A, 5.9) and Baked Moong Bites (C, 4.3, contains milk).
CHANA, MOONG = "Roasted Chana", "Baked Moong Bites"


@pytest.fixture
def fake_off_search():
    return FakeOff(by_barcode={NAMKEEN_BARCODE: NAMKEEN["source"]}, text=NAMKEEN["products"])


async def _primary(db_session) -> Member:
    return await db_session.scalar(
        select(Member).where(Member.account_id == ACC_A, Member.is_primary.is_(True))
    )


# --- alternatives -------------------------------------------------------------------------


async def test_alternatives_sort_protein_route(client, family):
    r = await client.get(f"{NAMKEEN_URL}?sort=protein&member_id={family.dad}")
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["reason"] == "ok"
    names = [i["name"] for i in body["items"]]
    assert set(names) == {CHANA, MOONG}
    for item in body["items"]:
        assert item["protein_per_100kcal"] > 2.5
        assert item["grade"] <= "E" and item["member_status"] != "avoid"
        assert item["protein_g"] is not None and item["attribution"] == "attribution.off"
    statuses = [i["member_status"] for i in body["items"]]
    assert statuses == sorted(statuses, key=["ok", "caution", "unknown"].index)


async def test_alternatives_sort_protein_drops_avoid_for_member(client, family):
    body = (await client.get(f"{NAMKEEN_URL}?sort=protein&member_id={family.riya}")).json()
    assert [i["name"] for i in body["items"]] == [CHANA]  # Moong contains milk


async def test_alternatives_grade_sort_unchanged_with_protein_fields(client):
    body = (await client.get(NAMKEEN_URL)).json()
    assert body["reason"] == "ok" and body["items"]
    assert all(i["member_status"] is None for i in body["items"])
    assert all("protein_per_100kcal" in i and "protein_g" in i for i in body["items"])


async def test_defaults_to_primary_member(client, db_session):
    me = await _primary(db_session)
    me.allergens = ["milk"]
    await db_session.flush()
    body = (await client.get(f"{NAMKEEN_URL}?sort=protein")).json()
    assert [i["name"] for i in body["items"]] == [CHANA]
    assert body["items"][0]["member_status"] is not None


async def test_alternatives_sort_protein_source_protein_unknown(
    client, label_only_product_id, db_session, fake_off
):
    # The OFF source without a protein value: nothing to compare against.
    no_protein = {
        **NAMKEEN["source"],
        "nutriments": {
            k: v for k, v in NAMKEEN["source"]["nutriments"].items() if "protein" not in k
        },
    }
    fake_off.by_barcode[NAMKEEN_BARCODE] = no_protein
    body = (await client.get(f"{NAMKEEN_URL}?sort=protein")).json()
    assert body == {"items": [], "reason": "source_protein_unknown"}


async def test_alternatives_bad_sort_422(client):
    r = await client.get(f"{NAMKEEN_URL}?sort=price")
    assert r.status_code == 422


# --- search -------------------------------------------------------------------------------


async def test_search_sort_protein_drops_avoid(client, login, family, fake_off_search):
    login(off=fake_off_search)
    r = await client.get(
        "/v1/products/search", params={"q": "snack", "sort": "protein", "member_id": family.riya}
    )
    assert r.status_code == 200, r.text
    hits = r.json()
    names = [h["name"] for h in hits]
    assert MOONG not in names and CHANA in names
    assert all(h["member_status"] in {"ok", "caution", "unknown"} for h in hits)
    known = [h["protein_per_100kcal"] for h in hits if h["protein_per_100kcal"] is not None]
    assert known == sorted(known, reverse=True)
    # Unknown protein sorts last.
    seen_unknown = False
    for h in hits:
        if h["protein_per_100kcal"] is None:
            seen_unknown = True
        else:
            assert not seen_unknown


async def test_search_sort_protein_defaults_to_primary(client, login, db_session, fake_off_search):
    me = await _primary(db_session)
    me.allergens = ["milk"]
    await db_session.flush()
    login(off=fake_off_search)
    hits = (await client.get("/v1/products/search?q=snack&sort=protein")).json()
    assert MOONG not in [h["name"] for h in hits]
    assert all(h["member_status"] is not None for h in hits)


async def test_search_relevance_unchanged(client, login, family, fake_off_search):
    login(off=fake_off_search)
    plain = (await client.get("/v1/products/search?q=snack")).json()
    assert MOONG in [h["name"] for h in plain]
    assert all(h["member_status"] is None for h in plain)
    chana = next(h for h in plain if h["name"] == CHANA)
    assert chana["protein_per_100kcal"] == 5.9 and chana["protein_g"] is not None
    # With member_id, relevance keeps every hit (avoid included) and fills member_status.
    with_member = (
        await client.get("/v1/products/search", params={"q": "snack", "member_id": family.riya})
    ).json()
    assert [h["name"] for h in with_member] == [h["name"] for h in plain]
    assert next(h for h in with_member if h["name"] == MOONG)["member_status"] == "avoid"


# --- compare ------------------------------------------------------------------------------


async def test_compare_protein_columns_and_better(client, oats_product_id, sf_biscuit_product_id):
    # oats: 13 g/100 g, 389 kcal, 40 g serving, 1 g sugars; sf_biscuit: 8 g, 450 kcal, 25 g, 2 g.
    r = await client.get(f"/v1/products/compare?a={oats_product_id}&b={sf_biscuit_product_id}")
    assert r.status_code == 200, r.text
    j = r.json()
    a, b = j["a"], j["b"]
    assert (a["serving_size_g"], a["protein_per_serving_g"], a["sugars_per_serving_g"]) == (
        40.0,
        5.2,
        0.4,
    )
    assert a["protein_per_100kcal"] == 3.3
    assert (b["serving_size_g"], b["protein_per_serving_g"], b["sugars_per_serving_g"]) == (
        25.0,
        2.0,
        0.5,
    )
    assert b["protein_per_100kcal"] == 1.8
    better = j["better"]
    assert better["protein_per_serving_g"] == "a"
    assert better["protein_per_100kcal"] == "a"
    assert better["sugars_per_serving_g"] == "a"


async def test_compare_missing_serving_is_unknown(client, oats_product_id, label_only_product_id):
    j = (
        await client.get(f"/v1/products/compare?a={label_only_product_id}&b={oats_product_id}")
    ).json()
    a = j["a"]
    assert a["serving_size_g"] is None
    assert a["protein_per_serving_g"] is None and a["sugars_per_serving_g"] is None
    assert a["protein_per_100kcal"] == 1.7  # 9 g / 520 kcal
    assert j["better"]["protein_per_serving_g"] == "unknown"
    assert j["better"]["sugars_per_serving_g"] == "unknown"
    assert j["better"]["protein_per_100kcal"] == "b"


# --- isolation ----------------------------------------------------------------------------


async def test_other_accounts_member_404(client, login, other_account_member_id, fake_off_search):
    r = await client.get(f"{NAMKEEN_URL}?sort=protein&member_id={other_account_member_id}")
    assert r.status_code == 404 and r.json()["error"]["code"] == "member_not_found"
    login(off=fake_off_search)
    r = await client.get(
        "/v1/products/search",
        params={"q": "snack", "sort": "protein", "member_id": str(other_account_member_id)},
    )
    assert r.status_code == 404 and r.json()["error"]["code"] == "member_not_found"
    assert fake_off_search.search_calls == []  # a foreign member never reaches OFF
