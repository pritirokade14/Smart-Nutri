from datetime import UTC, datetime, timedelta
from uuid import uuid4

import pytest
from sqlalchemy import select

from app.core.config import Settings
from app.features.products.models import OffProductCache, Product
from app.main import create_app
from tests.api.discovery.conftest import NAMKEEN, NAMKEEN_BARCODE
from tests.api.meals.conftest import ACC_A, ACC_C, FakeOff

pytestmark = pytest.mark.usefixtures("family")


@pytest.fixture
def fake_off_search():
    """OFF text search returns the recorded namkeen category products."""
    return FakeOff(by_barcode={NAMKEEN_BARCODE: NAMKEEN["source"]}, text=NAMKEEN["products"])


# --- plan tests --------------------------------------------------------------------------


async def test_compare_endpoint_member_status(
    client, family, sf_biscuit_product_id, oats_product_id
):
    r = (
        await client.get(
            f"/v1/products/compare?a={sf_biscuit_product_id}&b={oats_product_id}"
            f"&member_id={family.dad}"
        )
    ).json()
    assert r["a"]["member_status"] == "avoid" and r["better"]["grade"] == "b"


async def test_search_ours_first(client, login, sf_biscuit_product_id, fake_off_search):
    login(off=fake_off_search)
    hits = (await client.get("/v1/products/search?q=biscuit")).json()
    assert hits[0]["source"] == "ours"


async def test_search_query_too_short_422(client):
    assert (await client.get("/v1/products/search?q=a")).status_code == 422


# --- compare ------------------------------------------------------------------------------


async def test_compare_shape(client, sf_biscuit_product_id, oats_product_id):
    r = await client.get(f"/v1/products/compare?a={sf_biscuit_product_id}&b={oats_product_id}")
    assert r.status_code == 200
    j = r.json()
    assert j["a"]["name"] == "Sugar Free Biscuit" and j["a"]["member_status"] is None
    assert (j["a"]["grade"], j["b"]["grade"]) == ("D", "A")
    assert j["a"]["per_100g"]["sugars_g"] == 2.0 and j["a"]["attribution"] is None
    assert set(j["better"]) == {
        "energy_kcal",
        "sugars_g",
        "salt_g",
        "sat_fat_g",
        "protein_g",
        "fiber_g",
        "grade",
    }


async def test_compare_off_product_by_barcode(client, oats_product_id):
    r = await client.get(f"/v1/products/compare?a_barcode={NAMKEEN_BARCODE}&b={oats_product_id}")
    assert r.status_code == 200
    j = r.json()
    assert (j["a"]["product_id"], j["a"]["barcode"]) == (None, NAMKEEN_BARCODE)
    assert j["a"]["attribution"] == "attribution.off" and j["better"]["grade"] == "b"


@pytest.mark.parametrize(
    "query",
    [
        "b={b}",  # side a missing
        "a={a}&a_barcode=8900000000011&b={b}",  # side a twice
        "a={a}",  # side b missing
    ],
)
async def test_compare_needs_exactly_one_ref_per_side(
    client, sf_biscuit_product_id, oats_product_id, query
):
    q = query.format(a=sf_biscuit_product_id, b=oats_product_id)
    r = await client.get(f"/v1/products/compare?{q}")
    assert r.status_code == 422 and r.json()["error"]["code"] == "invalid_product_ref"


async def test_compare_foreign_member_404(
    client, sf_biscuit_product_id, oats_product_id, other_account_member_id
):
    r = await client.get(
        f"/v1/products/compare?a={sf_biscuit_product_id}&b={oats_product_id}"
        f"&member_id={other_account_member_id}"
    )
    assert r.status_code == 404 and r.json()["error"]["code"] == "member_not_found"


async def test_compare_unknown_product_404(client, sf_biscuit_product_id):
    r = await client.get(f"/v1/products/compare?a={sf_biscuit_product_id}&b={uuid4()}")
    assert r.status_code == 404 and r.json()["error"]["code"] == "product_not_found"


# --- search -------------------------------------------------------------------------------


async def test_search_merges_dedups_and_marks_sources(
    client, login, db_session, sf_biscuit_product_id, fake_off_search
):
    # Our own verified product shares a barcode with an OFF hit: ours wins, no duplicate.
    own = Product(
        barcode="8900000000028",
        name="Roasted Chana (ours)",
        source="label",
        verification_status="verified",
        per_100g={"sugars_g": 1},
        claims=[],
    )
    db_session.add(own)
    await db_session.flush()
    login(off=fake_off_search)
    hits = (await client.get("/v1/products/search?q=chana")).json()
    assert hits[0] == {
        "product_id": str(own.id),
        "barcode": "8900000000028",
        "name": "Roasted Chana (ours)",
        "brand": None,
        "grade": None,  # not enough data for a grade
        "source": "ours",
        "attribution": None,
    }
    barcodes = [h["barcode"] for h in hits]
    assert len(barcodes) == len(set(barcodes))
    off_hits = [h for h in hits if h["source"] == "off"]
    assert off_hits and all(h["attribution"] == "attribution.off" for h in off_hits)
    assert all(h["product_id"] is None for h in off_hits)
    assert all(h["barcode"] for h in off_hits)  # barcode-less OFF products are dropped


async def test_search_hides_other_accounts_pending_products(
    client, login, db_session, fake_off_search
):
    from app.core.security import AccountContext
    from app.features.me.service import ensure_account

    await ensure_account(db_session, AccountContext(ACC_C, None))
    db_session.add(
        Product(
            name="Secret Biscuit",
            source="user",
            verification_status="pending",
            created_by=ACC_C,
            claims=[],
        )
    )
    await db_session.flush()
    login(off=FakeOff())
    hits = (await client.get("/v1/products/search?q=secret")).json()
    assert hits == []


async def test_search_escapes_like_wildcards(client, login, sf_biscuit_product_id):
    login(off=FakeOff())
    assert (await client.get("/v1/products/search?q=%25%25")).json() == []
    assert (await client.get("/v1/products/search?q=__")).json() == []


async def test_search_off_down_returns_ours(client, login, sf_biscuit_product_id):
    login(off=FakeOff(fail=True))
    r = await client.get("/v1/products/search?q=sugar free")
    assert r.status_code == 200 and [h["source"] for h in r.json()] == ["ours"]


async def test_search_text_is_cached(client, login, db_session, fake_off_search):
    login(off=fake_off_search)
    await client.get("/v1/products/search?q=Namkeen")
    await client.get("/v1/products/search?q=  namkeen ")
    assert fake_off_search.search_calls == [("text", "namkeen")]
    row = await db_session.scalar(
        select(OffProductCache).where(OffProductCache.barcode == "search:text:namkeen")
    )
    row.fetched_at = datetime.now(UTC) - timedelta(hours=25)
    await db_session.flush()
    await client.get("/v1/products/search?q=namkeen")
    assert len(fake_off_search.search_calls) == 2


async def test_search_limit(client, login, fake_off_search):
    login(off=fake_off_search)
    hits = (await client.get("/v1/products/search?q=snack&limit=2")).json()
    assert len(hits) == 2
    assert (await client.get("/v1/products/search?q=snack&limit=0")).status_code == 422
    assert (await client.get("/v1/products/search?q=" + "x" * 81)).status_code == 422


async def test_search_is_rate_limited(db_session, login, family):
    import httpx

    from app.core.security import AccountContext, current_account
    from app.db.session import get_session
    from app.integrations.openfoodfacts import get_off_client

    app = create_app(Settings(_env_file=None, environment="test", rate_limit_search_per_minute=2))
    app.dependency_overrides[get_session] = lambda: db_session
    app.dependency_overrides[get_off_client] = lambda: FakeOff()
    app.dependency_overrides[current_account] = lambda: AccountContext(ACC_A, None)
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://t") as c:
        codes = [(await c.get("/v1/products/search?q=oats")).status_code for _ in range(3)]
    assert codes == [200, 200, 429]
