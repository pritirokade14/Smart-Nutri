from datetime import UTC, datetime, timedelta

import pytest
from sqlalchemy import select

from app import scoring
from app.features.products.alternatives import Candidate, rank_alternatives, source_category
from app.features.products.models import OffProductCache
from tests.api.discovery.conftest import NAMKEEN, NAMKEEN_BARCODE
from tests.api.meals.conftest import FakeOff

pytestmark = pytest.mark.usefixtures("family")

NAMKEEN_URL = f"/v1/products/barcode/{NAMKEEN_BARCODE}/alternatives"


def prod(name, *, grade, sugars, ingredients=("rice flour", "salt")):
    return Candidate(
        product=scoring.Product(
            name=name,
            per_100g=scoring.Nutrients(sugars_g=sugars),
            ingredients=tuple(ingredients),
        ),
        grade=grade,
        payload={"code": name},
    )


PEANUT_ALLERGIC = scoring.Member(id="p", name="", age=30, allergens=("peanut",))


# --- plan tests --------------------------------------------------------------------------


def test_rank_strictly_better_and_never_ungraded():
    ranked = rank_alternatives(
        "D",
        [
            prod("x", grade="C", sugars=8),
            prod("y", grade="D", sugars=1),
            prod("z", grade=None, sugars=0),
            prod("w", grade="A", sugars=20),
        ],
    )
    assert [c.product.name for c in ranked] == ["w", "x"]


async def test_no_category_returns_empty_with_reason(client, label_only_product_id, fake_off):
    r = await client.get(f"/v1/products/{label_only_product_id}/alternatives")
    assert r.status_code == 200 and r.json() == {"items": [], "reason": "no_category"}
    assert fake_off.search_calls == []


async def test_never_worse_or_ungraded(client):
    r = await client.get(NAMKEEN_URL)
    items = r.json()["items"]
    assert items and all(i["grade"] < "E" for i in items)  # source is E
    assert all(i["grade"] is not None for i in items)


async def test_member_status_from_engine(client, family):
    items = (await client.get(f"{NAMKEEN_URL}?member_id={family.dad}")).json()["items"]
    assert items and all(i["member_status"] in {"ok", "caution", "unknown", "avoid"} for i in items)


# --- more ---------------------------------------------------------------------------------


def test_rank_sorts_by_grade_then_sugars_then_name_max_five():
    cands = [
        prod("b", grade="B", sugars=3),
        prod("a2", grade="B", sugars=None),  # unknown sugar sorts after known
        prod("a1", grade="B", sugars=3),
        prod("c", grade="A", sugars=9),
        prod("d", grade="B", sugars=1),
        prod("e", grade="C", sugars=0),
        prod("f", grade="B", sugars=2),
    ]
    assert [c.product.name for c in rank_alternatives("E", cands)] == ["c", "d", "f", "a1", "b"]


def test_rank_source_ungraded_returns_nothing():
    assert rank_alternatives(None, [prod("a", grade="A", sugars=0)]) == []


def test_source_category_is_the_last_tag():
    assert source_category({"categories_tags": ["en:snacks", "en:namkeen"]}) == "en:namkeen"
    assert source_category({"product": {"categories_tags": ["en:x"]}}) == "en:x"
    assert source_category({"categories_tags": []}) is None
    assert source_category({"categories_tags": "en:x"}) is None
    assert source_category(None) is None


async def test_ranked_items_and_shape(client):
    r = (await client.get(NAMKEEN_URL)).json()
    assert r["reason"] == "ok"
    # Source (E), Aloo Bhujia (E), Khatta Meetha (ungraded) and the barcode-less snack are out.
    assert [(i["name"], i["grade"]) for i in r["items"]] == [
        ("Roasted Chana", "A"),
        ("Puffed Rice Mix", "C"),
        ("Baked Moong Bites", "C"),
    ]
    first = r["items"][0]
    assert first["barcode"] == "8900000000028" and first["product_id"] is None
    assert first["attribution"] == "attribution.off" and first["member_status"] is None
    assert first["sugars_g"] == 1.0 and first["high_in"] == []


async def test_milk_allergic_child_never_offered_an_avoid(client, family):
    # Ruling M1 B2: Baked Moong Bites (milk solids) is `avoid` for Riya, so it is dropped.
    r = (await client.get(f"{NAMKEEN_URL}?member_id={family.riya}")).json()
    assert r["reason"] == "ok"
    names = [i["name"] for i in r["items"]]
    assert "Baked Moong Bites" not in names and names
    assert all(i["member_status"] != "avoid" for i in r["items"])
    # Without a member it is still a better-graded product.
    plain = (await client.get(NAMKEEN_URL)).json()["items"]
    assert "Baked Moong Bites" in [i["name"] for i in plain]


async def test_every_better_product_avoid_for_member_is_no_better_found(client, login, family):
    only_milk = [p for p in NAMKEEN["products"] if p.get("product_name") == "Baked Moong Bites"]
    login(off=FakeOff(by_barcode={NAMKEEN_BARCODE: NAMKEEN["source"]}, category=only_milk))
    r = (await client.get(f"{NAMKEEN_URL}?member_id={family.riya}")).json()
    assert r == {"items": [], "reason": "no_better_found"}


# --- Ruling M1 B2: member-safe ranking (pure) ---------------------------------------------


def test_rank_for_member_drops_avoid_before_the_top_five_cut():
    peanut = ("peanuts", "salt")
    cands = [prod(f"a{i}", grade="A", sugars=0, ingredients=peanut) for i in range(6)]
    cands.append(prod("safe", grade="C", sugars=5))
    ranked = rank_alternatives("D", cands, PEANUT_ALLERGIC)
    assert [c.product.name for c in ranked] == ["safe"]
    # Without a member the top five are the grade A products.
    assert [c.product.name for c in rank_alternatives("D", cands)] == [f"a{i}" for i in range(5)]


def test_rank_for_member_orders_ok_then_caution_then_unknown_then_grade():
    cands = [
        prod("unknown_a", grade="A", sugars=0, ingredients=()),  # no ingredients: unknown
        prod("ok_c", grade="C", sugars=0),
        prod("ok_b", grade="B", sugars=0),
        prod("avoid_a", grade="A", sugars=0, ingredients=("peanuts",)),
    ]
    statuses = {
        c.product.name: scoring.analyze(c.product, [PEANUT_ALLERGIC]).verdicts[0].status.value
        for c in cands
    }
    assert statuses == {"unknown_a": "unknown", "ok_c": "ok", "ok_b": "ok", "avoid_a": "avoid"}
    ranked = rank_alternatives("D", cands, PEANUT_ALLERGIC)
    assert [c.product.name for c in ranked] == ["ok_b", "ok_c", "unknown_a"]


def test_rank_for_member_caution_sorts_between_ok_and_unknown():
    diabetic = scoring.Member(id="d", name="", age=50, conditions=("diabetes",))
    full = {"energy_kcal": 400, "protein_g": 10, "carbs_g": 20, "fat_g": 10, "sat_fat_g": 2}
    full |= {"fiber_g": 5, "salt_g": 0.5}

    def labelled(name, grade, sugars):
        product = scoring.Product(
            name=name,
            per_100g=scoring.Nutrients(sugars_g=sugars, **full),
            ingredients=("rice flour", "salt"),
        )
        return Candidate(product=product, grade=grade, payload={"code": name})

    cands = [
        prod("unknown_a", grade="A", sugars=None, ingredients=()),
        labelled("caution_b", "B", 8),  # sugar_moderate
        labelled("ok_c", "C", 1),
    ]
    statuses = [scoring.analyze(c.product, [diabetic]).verdicts[0].status.value for c in cands]
    assert statuses == ["unknown", "caution", "ok"]
    ranked = rank_alternatives("D", cands, diabetic)
    assert [c.product.name for c in ranked] == ["ok_c", "caution_b", "unknown_a"]


def test_rank_for_member_all_avoid_is_empty():
    cands = [prod("a", grade="A", sugars=0, ingredients=("peanuts",))]
    assert rank_alternatives("D", cands, PEANUT_ALLERGIC) == []


async def test_foreign_member_404(client, other_account_member_id):
    r = await client.get(f"{NAMKEEN_URL}?member_id={other_account_member_id}")
    assert r.status_code == 404 and r.json()["error"]["code"] == "member_not_found"


async def test_source_ungraded(client, login):
    payload = {**NAMKEEN["source"], "nutriments": {"energy-kcal_100g": 500}}
    login(off=FakeOff(by_barcode={NAMKEEN_BARCODE: payload}, category=NAMKEEN["products"]))
    assert (await client.get(NAMKEEN_URL)).json() == {"items": [], "reason": "source_ungraded"}


async def test_no_better_found(client, login):
    worse = [p for p in NAMKEEN["products"] if p.get("product_name") == "Aloo Bhujia"]
    login(off=FakeOff(by_barcode={NAMKEEN_BARCODE: NAMKEEN["source"]}, category=worse))
    assert (await client.get(NAMKEEN_URL)).json() == {"items": [], "reason": "no_better_found"}


async def test_category_search_is_cached_24h(client, fake_off, db_session):
    await client.get(NAMKEEN_URL)
    await client.get(NAMKEEN_URL)
    assert fake_off.search_calls == [("category", "en:namkeen")]
    row = await db_session.scalar(
        select(OffProductCache).where(OffProductCache.barcode == "search:category:en:namkeen")
    )
    assert row is not None and len(row.payload["products"]) == len(NAMKEEN["products"])
    # Older than 24 h: asked again.
    row.fetched_at = datetime.now(UTC) - timedelta(hours=25)
    await db_session.flush()
    await client.get(NAMKEEN_URL)
    assert len(fake_off.search_calls) == 2


async def test_off_down_without_cache_is_503(client, login):
    login(off=FakeOff(by_barcode={NAMKEEN_BARCODE: NAMKEEN["source"]}))
    await client.get(f"/v1/products/barcode/{NAMKEEN_BARCODE}")  # caches the source
    down = FakeOff(fail=True)
    login(off=down)
    r = await client.get(NAMKEEN_URL)
    assert r.status_code == 503 and r.json()["error"]["code"] == "off_unavailable"


async def test_unknown_product_404(client):
    from uuid import uuid4

    r = await client.get(f"/v1/products/{uuid4()}/alternatives")
    assert r.status_code == 404 and r.json()["error"]["code"] == "product_not_found"


async def test_invalid_barcode_422(client):
    r = await client.get("/v1/products/barcode/12ab/alternatives")
    assert r.status_code == 422 and r.json()["error"]["code"] == "invalid_barcode"
