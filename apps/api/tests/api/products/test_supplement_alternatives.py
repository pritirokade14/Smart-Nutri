# ruff: noqa: F811  (fixtures imported from the discovery conftest, used by name)
"""Plan 9 Task 7 (P9-R10, P9-R11): supplements are never offered as alternatives or swaps.

A supplement source returns `source_supplement`; supplement candidates are dropped by both
sorts and by the higher-protein search; a plain (relevance) search still shows them, ungraded.
"""

import copy

import pytest

from app import scoring
from app.features.products.alternatives import (
    Candidate,
    rank_alternatives,
    rank_alternatives_by_protein,
)
from app.features.products.models import Product
from tests.api.discovery.conftest import (  # noqa: F401  (shared fixtures)
    NAMKEEN,
    NAMKEEN_BARCODE,
    fake_off,
    family,
    login,
)
from tests.api.meals.conftest import FakeOff

pytestmark = pytest.mark.usefixtures("family")

NAMKEEN_URL = f"/v1/products/barcode/{NAMKEEN_BARCODE}/alternatives"
CHANA_BARCODE = "8900000000028"  # Roasted Chana: grade A, 5.9 g protein per 100 kcal


def _as_supplement(payload: dict) -> dict:
    out = copy.deepcopy(payload)
    out["categories_tags"] = [*out.get("categories_tags", []), "en:protein-powders"]
    return out


def _category_with_supplement_chana() -> list[dict]:
    return [_as_supplement(p) if p.get("code") == CHANA_BARCODE else p for p in NAMKEEN["products"]]


# --- pure ranking -------------------------------------------------------------------------


def _cand(name, *, grade, protein, category):
    product = scoring.Product(
        name=name,
        category=category,
        per_100g=scoring.Nutrients(
            energy_kcal=100,
            protein_g=protein,
            carbs_g=10,
            sugars_g=1,
            fat_g=1,
            sat_fat_g=0.1,
            fiber_g=1,
            salt_g=0.1,
        ),
        ingredients=("rice flour",),
    )
    return Candidate(product=product, grade=grade, payload={})


def test_supplement_never_a_candidate_pure():
    adult = scoring.Member(id="a", name="", age=30)
    cands = [
        _cand("whey", grade="A", protein=20, category=scoring.Category.SUPPLEMENT),
        _cand("chana", grade="A", protein=9, category=scoring.Category.GENERAL),
    ]
    assert [c.product.name for c in rank_alternatives("E", cands)] == ["chana"]
    assert [c.product.name for c in rank_alternatives("E", cands, adult)] == ["chana"]
    source = scoring.Product(
        name="src",
        per_100g=scoring.Nutrients(
            energy_kcal=100,
            protein_g=2,
            carbs_g=10,
            sugars_g=1,
            fat_g=1,
            sat_fat_g=0.1,
            fiber_g=1,
            salt_g=0.1,
        ),
    )
    items, _ = rank_alternatives_by_protein(source, cands, adult)
    assert [c.product.name for c in items] == ["chana"]


# --- routes -------------------------------------------------------------------------------


async def test_supplement_source_returns_source_supplement(client, db_session):
    own = Product(
        barcode=None,
        name="Whey Protein",
        source="label",
        verification_status="verified",
        category="supplement",
        per_100g={
            "energy_kcal": 400,
            "protein_g": 80,
            "sugars_g": 4,
            "sat_fat_g": 3,
            "salt_g": 0.5,
            "fat_g": 6,
            "carbs_g": 8,
        },
        serving_size_g=30,
        ingredients_text="whey protein concentrate, cocoa",
        claims=[],
    )
    db_session.add(own)
    await db_session.flush()
    for sort in ("grade", "protein"):
        r = await client.get(f"/v1/products/{own.id}/alternatives?sort={sort}")
        assert r.status_code == 200, r.text
        assert r.json() == {"items": [], "reason": "source_supplement"}


async def test_off_supplement_source_returns_source_supplement(client, fake_off):
    fake_off.by_barcode[NAMKEEN_BARCODE] = _as_supplement(NAMKEEN["source"])
    for sort in ("grade", "protein"):
        body = (await client.get(f"{NAMKEEN_URL}?sort={sort}")).json()
        assert body == {"items": [], "reason": "source_supplement"}
    assert fake_off.search_calls == []  # nothing is searched for a supplement


@pytest.mark.parametrize("sort", ["grade", "protein"])
async def test_supplement_never_a_candidate(client, fake_off, sort):
    fake_off.category = _category_with_supplement_chana()
    body = (await client.get(f"{NAMKEEN_URL}?sort={sort}")).json()
    assert "Roasted Chana" not in [i["name"] for i in body["items"]]
    assert all(i["grade"] is not None for i in body["items"])


async def test_protein_search_excludes_supplements(client, login, family):
    off = FakeOff(text=_category_with_supplement_chana())
    login(off=off)
    hits = (
        await client.get(
            "/v1/products/search", params={"q": "snack", "sort": "protein", "member_id": family.dad}
        )
    ).json()
    assert "Roasted Chana" not in [h["name"] for h in hits]
    plain = (await client.get("/v1/products/search?q=snack")).json()
    chana = next(h for h in plain if h["name"] == "Roasted Chana")
    assert chana["grade"] is None  # shown, ungraded
