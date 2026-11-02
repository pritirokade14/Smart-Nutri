from datetime import UTC, datetime, timedelta

import pytest
from sqlalchemy import func, select

from app.core.config import Settings
from app.features.products.models import OffProductCache, Product
from app.features.products.service import (
    lookup_by_barcode,
    record_to_info,
    record_to_product,
)
from app.integrations.openfoodfacts import OffUnavailable
from app.scoring import Category

BARCODE = "8901063201089"
SETTINGS = Settings(_env_file=None, environment="test")
OFF_PAYLOAD = {
    "code": BARCODE,
    "product_name": "OFF Biscuit",
    "brands": "Acme",
    "ingredients_text": "wheat flour, sugar",
    "nutriments": {"sugars_100g": 20, "carbohydrates_100g": 70},
}


class FakeOff:
    def __init__(self, payload=OFF_PAYLOAD, *, fail=False):
        self.payload = payload
        self.fail = fail
        self.calls = 0

    async def get_product(self, barcode):
        self.calls += 1
        if self.fail:
            raise OffUnavailable("down")
        return self.payload


@pytest.fixture
def fake_off():
    return FakeOff()


@pytest.fixture
def failing_off():
    return FakeOff(fail=True)


@pytest.fixture
def fake_off_empty():
    return FakeOff(None)


def _product(**kw):
    base = {
        "barcode": BARCODE,
        "name": "Own Biscuit",
        "source": "label",
        "verification_status": "verified",
        "per_100g": {"sugars_g": 12.5, "sodium_mg": 300},
        "ingredients_text": "Wheat flour (atta), Sugar, Salt",
        "claims": ["no added sugar"],
        "category": "general",
    }
    base.update(kw)
    return Product(**base)


async def _cache(session, hours_old):
    session.add(
        OffProductCache(
            barcode=BARCODE,
            payload=OFF_PAYLOAD,
            fetched_at=datetime.now(UTC) - timedelta(hours=hours_old),
        )
    )
    await session.flush()


async def test_own_product_wins_without_off_call(db_session, fake_off):
    p = _product()
    db_session.add(p)
    await db_session.flush()
    r = await lookup_by_barcode(db_session, fake_off, BARCODE, settings=SETTINGS)
    assert r.source == "smartnutri"
    assert r.product_id == p.id
    assert r.attribution is None
    assert fake_off.calls == 0


async def test_rejected_own_product_falls_through_to_off(db_session, fake_off):
    db_session.add(_product(verification_status="rejected"))
    await db_session.flush()
    r = await lookup_by_barcode(db_session, fake_off, BARCODE, settings=SETTINGS)
    assert r.source == "openfoodfacts"
    assert r.product_id is None
    assert r.attribution == "attribution.off"
    assert r.product.extraction_confidence == 0.9


async def test_fresh_cache_hit_no_off_call(db_session, fake_off):
    await _cache(db_session, 1)
    r = await lookup_by_barcode(db_session, fake_off, BARCODE, settings=SETTINGS)
    assert fake_off.calls == 0
    assert r.source == "openfoodfacts"
    assert r.info.name == "OFF Biscuit"


async def test_stale_cache_refetches_and_updates(db_session, fake_off):
    await _cache(db_session, 200)
    r = await lookup_by_barcode(db_session, fake_off, BARCODE, settings=SETTINGS)
    assert fake_off.calls == 1
    assert r.source == "openfoodfacts"
    row = await db_session.get(OffProductCache, BARCODE, populate_existing=True)
    assert datetime.now(UTC) - row.fetched_at < timedelta(hours=1)


async def test_miss_populates_cache(db_session, fake_off):
    await lookup_by_barcode(db_session, fake_off, BARCODE, settings=SETTINGS)
    row = await db_session.get(OffProductCache, BARCODE)
    assert row is not None and row.payload["product_name"] == "OFF Biscuit"


async def test_off_down_uses_stale_cache(db_session, failing_off):
    await _cache(db_session, 200)
    r = await lookup_by_barcode(db_session, failing_off, BARCODE, settings=SETTINGS)
    assert failing_off.calls == 1
    assert r.info.name == "OFF Biscuit"


async def test_off_down_no_cache_raises(db_session, failing_off):
    with pytest.raises(OffUnavailable):
        await lookup_by_barcode(db_session, failing_off, BARCODE, settings=SETTINGS)


async def test_not_found_everywhere_returns_none(db_session, fake_off_empty):
    assert await lookup_by_barcode(db_session, fake_off_empty, BARCODE, settings=SETTINGS) is None


async def test_stale_cache_deleted_when_off_says_not_found(db_session, fake_off_empty):
    await _cache(db_session, 200)
    assert await lookup_by_barcode(db_session, fake_off_empty, BARCODE, settings=SETTINGS) is None
    assert await db_session.get(OffProductCache, BARCODE, populate_existing=True) is None


async def test_off_data_never_written_to_products(db_session, fake_off):
    count = select(func.count()).select_from(Product)
    before = await db_session.scalar(count)
    await lookup_by_barcode(db_session, fake_off, BARCODE, settings=SETTINGS)
    assert await db_session.scalar(count) == before


async def test_barcode_is_normalised(db_session, fake_off):
    r = await lookup_by_barcode(db_session, fake_off, "890 106-3201089", settings=SETTINGS)
    assert r is not None


def test_record_to_product_maps_values_and_never_invents():
    rec = _product(extraction_confidence=0.8, serving_size_g=30, veg_mark="veg")
    p = record_to_product(rec)
    assert p.per_100g.sugars_g == 12.5
    assert p.per_100g.sodium_mg == 300
    assert p.per_100g.protein_g is None
    assert p.category is Category.GENERAL
    assert p.ingredients == ("Wheat flour (atta)", "Sugar", "Salt")
    assert p.claims == ("no added sugar",)
    assert p.serving_size_g == 30
    assert p.veg_mark == "veg"
    assert p.extraction_confidence == 0.8


def test_record_to_product_confidence_defaults():
    assert record_to_product(_product()).extraction_confidence == 1.0
    pending = _product(verification_status="pending")
    assert record_to_product(pending).extraction_confidence < 0.7


def test_record_to_product_ignores_bad_json_values():
    p = record_to_product(_product(per_100g={"sugars_g": "x", "fat_g": True, "bogus": 3}))
    assert p.per_100g.sugars_g is None and p.per_100g.fat_g is None


def test_record_to_info():
    i = record_to_info(_product(brand="Acme"))
    assert (i.barcode, i.name, i.brand, i.image_url) == (BARCODE, "Own Biscuit", "Acme", None)
