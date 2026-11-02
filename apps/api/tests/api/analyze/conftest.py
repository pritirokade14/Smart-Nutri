from datetime import UTC, date, datetime
from uuid import UUID

import pytest
from sqlalchemy import func, select

from app.core.security import AccountContext, current_account
from app.db.session import get_session
from app.features.me.service import ensure_account
from app.features.members.models import Member
from app.features.products.models import Product
from app.integrations.openfoodfacts import get_off_client
from scripts.export_fixture_responses import fixture_product_record
from tests.api.products.test_lookup_service import FakeOff

A = UUID("11111111-1111-1111-1111-111111111111")
B = UUID("22222222-2222-2222-2222-222222222222")
OFF_BARCODE = "8901063201089"
OWN_BARCODE = "8901725181222"

# Ingredients need a language tag, and a Nutri-Score grade needs the full nutrient set.
OFF_PAYLOAD = {
    "code": OFF_BARCODE,
    "product_name": "OFF Biscuit",
    "brands": "Acme",
    "ingredients_text": "wheat flour, sugar",
    "ingredients_lc": "en",
    "nutriments": {
        "energy-kcal_100g": 480,
        "sugars_100g": 15,
        "carbohydrates_100g": 70,
        "saturated-fat_100g": 4,
        "fat_100g": 20,
        "salt_100g": 0.5,
        "fiber_100g": 1,
        "proteins_100g": 6,
    },
}


def today() -> date:
    return datetime.now(UTC).date()


@pytest.fixture
def fake_off():
    return FakeOff(OFF_PAYLOAD)


@pytest.fixture
def login(app, db_session, fake_off):
    def _login(account_id: UUID = A, *, off=None):
        app.dependency_overrides[get_session] = lambda: db_session
        app.dependency_overrides[get_off_client] = lambda: off or fake_off
        app.dependency_overrides[current_account] = lambda: AccountContext(
            account_id, "asha@example.com"
        )

    return _login


@pytest.fixture
def auth_client(client, login):
    login(A)
    client.account_id = A
    return client


@pytest.fixture
def count_members(db_session):
    async def _count(account_id: UUID) -> int:
        return await db_session.scalar(
            select(func.count()).select_from(Member).where(Member.account_id == account_id)
        )

    return _count


async def _add(db_session, row):
    db_session.add(row)
    await db_session.flush()
    return row


@pytest.fixture
async def seeded_product(db_session):
    return await _add(
        db_session,
        Product(
            barcode=OWN_BARCODE,
            name="Own Biscuit",
            source="label",
            verification_status="verified",
            category="general",
            per_100g={"sugars_g": 12.5, "sodium_mg": 300, "energy_kcal": 450},
            ingredients_text="Wheat flour (atta), Sugar, Salt",
            claims=[],
        ),
    )


@pytest.fixture
async def cola_product(db_session):
    return await _add(db_session, fixture_product_record("cola"))


async def _account(db_session, account_id: UUID) -> None:
    await ensure_account(db_session, AccountContext(account_id, None))


@pytest.fixture
async def member_no_birth_year(db_session):
    await _account(db_session, A)
    return await _add(
        db_session,
        Member(account_id=A, name="Asha", relation="other", birth_year=None, diet="non_veg"),
    )


@pytest.fixture
async def own_member(db_session):
    await _account(db_session, A)
    return await _add(
        db_session,
        Member(
            account_id=A,
            name="Ravi",
            relation="parent",
            birth_year=today().year - 60,
            diet="veg",
            conditions=["diabetes"],
            allergens=[],
        ),
    )


@pytest.fixture
async def other_account_member(db_session):
    await _account(db_session, B)
    return await _add(
        db_session,
        Member(account_id=B, name="Other", relation="self", birth_year=1990, diet="non_veg"),
    )
