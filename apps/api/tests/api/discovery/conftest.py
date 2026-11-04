"""Fixtures for alternatives, search and compare: the meals family plus recorded OFF data."""

import json
from pathlib import Path
from uuid import UUID

import pytest

from app.features.products.models import Product
from tests.api.meals.conftest import (  # noqa: F401  (shared fixtures)
    FakeOff,
    family,
    login,
    oats_product_id,
    other_account_member_id,
    sf_biscuit_product_id,
)

OFF_DIR = Path(__file__).resolve().parents[2] / "fixtures" / "off"
NAMKEEN = json.loads((OFF_DIR / "namkeen_category.json").read_text())
NAMKEEN_BARCODE = NAMKEEN["source"]["code"]


@pytest.fixture
def fake_off():
    """OFF knows the namkeen (by barcode) and its category; no network."""
    return FakeOff(by_barcode={NAMKEEN_BARCODE: NAMKEEN["source"]}, category=NAMKEEN["products"])


@pytest.fixture
async def label_only_product_id(db_session) -> UUID:
    """Our own verified product from a label scan: no barcode, so no OFF category."""
    record = Product(
        barcode=None,
        name="Homemade Chakli",
        source="label",
        verification_status="verified",
        category="general",
        per_100g={
            "energy_kcal": 520,
            "sugars_g": 2,
            "sat_fat_g": 8,
            "salt_g": 1.5,
            "fat_g": 30,
            "carbs_g": 55,
            "protein_g": 9,
            "fiber_g": 3,
        },
        ingredients_text="rice flour, oil, salt",
        claims=[],
    )
    db_session.add(record)
    await db_session.flush()
    return record.id
