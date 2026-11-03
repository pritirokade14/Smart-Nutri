"""Fixtures for the meals routes: ACC_A with a seeded family and fixture products."""

from dataclasses import dataclass
from uuid import UUID

import pytest

from app.core.security import AccountContext, current_account
from app.core.time import today_ist
from app.db.session import get_session
from app.features.me.service import ensure_account
from app.features.members.models import Member
from app.features.members.service import get_or_create_primary
from app.integrations.openfoodfacts import OffUnavailable, get_off_client
from scripts.export_fixture_responses import fixture_product_record

ACC_A = UUID("11111111-1111-1111-1111-111111111111")
ACC_C = UUID("33333333-3333-3333-3333-333333333333")
OFF_BARCODE = "8901063201089"

# A real-shaped OFF payload with no sugars value (missing stays missing).
OFF_PAYLOAD = {
    "code": OFF_BARCODE,
    "product_name": "OFF Namkeen",
    "brands": "Acme",
    "ingredients_text": "gram flour, oil, salt",
    "ingredients_lc": "en",
    "serving_quantity": 30,
    "nutriments": {
        "energy-kcal_100g": 550,
        "carbohydrates_100g": 40,
        "saturated-fat_100g": 10,
        "fat_100g": 35,
        "salt_100g": 2.5,
        "fiber_100g": 5,
        "proteins_100g": 15,
    },
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
def login(app, db_session, fake_off):
    def _login(account_id: UUID = ACC_A, *, off=None):
        app.dependency_overrides[get_session] = lambda: db_session
        app.dependency_overrides[get_off_client] = lambda: off or fake_off
        app.dependency_overrides[current_account] = lambda: AccountContext(
            account_id, "asha@example.com"
        )

    return _login


@dataclass(frozen=True)
class Family:
    me: UUID
    dad: UUID
    riya: UUID


@pytest.fixture
async def family(db_session, login) -> Family:
    """ACC_A logged in: Me (primary), Dad (diabetic, 70 kg) and Riya (8, milk allergy)."""
    await ensure_account(db_session, AccountContext(ACC_A, None))
    me = await get_or_create_primary(db_session, ACC_A)
    year = today_ist().year
    dad = Member(
        account_id=ACC_A,
        name="Ravi",
        relation="parent",
        birth_year=year - 61,
        diet="veg",
        conditions=["diabetes"],
        allergens=[],
        weight_kg=70,
    )
    riya = Member(
        account_id=ACC_A,
        name="Riya",
        relation="child",
        birth_year=year - 9,
        diet="veg",
        allergens=["milk"],
        conditions=[],
    )
    db_session.add_all([dad, riya])
    await db_session.flush()
    login(ACC_A)
    return Family(me=me.id, dad=dad.id, riya=riya.id)


@pytest.fixture
async def other_account_member_id(db_session) -> UUID:
    await ensure_account(db_session, AccountContext(ACC_C, None))
    member = Member(account_id=ACC_C, name="Other", relation="parent", diet="veg")
    db_session.add(member)
    await db_session.flush()
    return member.id


async def _product(db_session, name: str) -> UUID:
    record = fixture_product_record(name)
    db_session.add(record)
    await db_session.flush()
    return record.id


@pytest.fixture
async def sf_biscuit_product_id(db_session) -> UUID:
    return await _product(db_session, "sf_biscuit")


@pytest.fixture
async def oats_product_id(db_session) -> UUID:
    return await _product(db_session, "oats")
