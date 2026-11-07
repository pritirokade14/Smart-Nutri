"""Fixtures for the foods tests: ACC_A, a few seeded foods and a fake OFF."""

from decimal import Decimal
from uuid import UUID

import pytest

from app.core.config import Settings
from app.core.security import AccountContext, current_account
from app.db.session import get_session
from app.features.foods.models import Food, FoodPortion
from app.features.me.service import ensure_account
from app.integrations.openfoodfacts import get_off_client
from tests.api.conftest import clock  # noqa: F401  (pinned clock)
from tests.api.meals.conftest import ACC_A, OFF_BARCODE, OFF_PAYLOAD, FakeOff  # noqa: F401
from tests.api.members.conftest import add_member, consented, grant  # noqa: F401
from tests.api.targets.conftest import (  # noqa: F401  (shared fixtures)
    G1_SETTINGS,
    g1,
    set_primary,
    today,
)

ACC_B = UUID("22222222-2222-2222-2222-222222222222")


@pytest.fixture
def settings() -> Settings:
    return Settings(_env_file=None, environment="test")


@pytest.fixture
def fake_off() -> FakeOff:
    return FakeOff()


@pytest.fixture
def login(app, db_session, fake_off):
    """Act as `account_id` on the rolled-back test session with a fake Open Food Facts."""

    def _login(account_id: UUID = ACC_A, *, off=None) -> None:
        app.dependency_overrides[get_session] = lambda: db_session
        app.dependency_overrides[get_off_client] = lambda: off or fake_off
        app.dependency_overrides[current_account] = lambda: AccountContext(
            account_id, "asha@example.com"
        )

    return _login


@pytest.fixture
async def accounts(db_session):
    for acc in (ACC_A, ACC_B):
        await ensure_account(db_session, AccountContext(acc, None))
    await db_session.flush()


def make_food(code: str, name: str, **cols) -> Food:
    values = {
        "source": "usda_fdc",
        "source_code": code,
        "name_en": name,
        "aliases": [],
        "search_text": name.lower(),
        "basis": "g",
        "per_100": {
            "energy_kcal": 116.0,
            "protein_g": 7.0,
            "carbs_g": 20.0,
            "sugars_g": 1.8,
            "fat_g": 0.4,
            "sat_fat_g": None,
            "fiber_g": 4.5,
            "sodium_mg": 4.0,
        },
        "density_g_per_ml": None,
        "serving_g": None,
        "licence": "CC0 1.0",
        "data_version": "test",
    } | cols
    return Food(**values)


@pytest.fixture
async def dal(db_session):
    """A cooked-dal-like food: density 0.71, so a katori converts."""
    food = make_food("t-dal", "Lentils, cooked", density_g_per_ml=Decimal("0.71"))
    db_session.add(food)
    await db_session.flush()
    return food


def portion(food_id, unit, grams, *, account_id=None) -> FoodPortion:
    return FoodPortion(
        food_id=food_id,
        unit=unit,
        grams_per_unit=Decimal(str(grams)),
        source="user" if account_id else "reference_table",
        account_id=account_id,
    )
