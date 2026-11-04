from collections.abc import Iterable
from datetime import date
from uuid import UUID

import pytest
from sqlalchemy import func, select

from app.core.security import AccountContext, current_account
from app.core.time import today_ist
from app.db.session import get_session
from app.features.consents.models import Consent
from app.features.consents.policy import CURRENT_VERSIONS
from app.features.me.service import ensure_account
from app.features.members.models import Member
from app.features.members.service import get_or_create_primary
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


EMAIL = "asha@example.com"
ALL_PURPOSES = ("terms", "health_data", "ai_processing")


def today() -> date:
    """The API's "today" (IST, Ruling P8.2)."""
    return today_ist()


@pytest.fixture
def fake_off():
    return FakeOff(OFF_PAYLOAD)


@pytest.fixture
def login(app, db_session, fake_off):
    def _login(account_id: UUID = A, *, off=None):
        app.dependency_overrides[get_session] = lambda: db_session
        app.dependency_overrides[get_off_client] = lambda: off or fake_off
        app.dependency_overrides[current_account] = lambda: AccountContext(account_id, EMAIL)

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


@pytest.fixture
def grant(db_session):
    """Record active consents at the current version for an account."""

    async def _grant(account_id: UUID = A, purposes: Iterable[str] = ALL_PURPOSES) -> None:
        await _account(db_session, account_id)
        for purpose in purposes:
            db_session.add(
                Consent(account_id=account_id, purpose=purpose, version=CURRENT_VERSIONS[purpose])
            )
        await db_session.flush()

    return _grant


@pytest.fixture
async def seeded_family(db_session) -> dict[str, Member]:
    """Account A: Me (the primary, 1991, weight loss), Dad (parent, 1954, veg, diabetes) and
    Riya (child, 2018, veg, milk allergy), created in that order."""
    await _account(db_session, A)
    me = await get_or_create_primary(db_session, A)
    me.name, me.birth_year, me.goal = "Me", 1991, "weight_loss"
    dad = Member(
        account_id=A,
        name="Dad",
        relation="parent",
        birth_year=1954,
        diet="veg",
        conditions=["diabetes"],
        created_at=func.clock_timestamp(),
    )
    db_session.add(dad)
    await db_session.flush()
    riya = Member(
        account_id=A,
        name="Riya",
        relation="child",
        birth_year=2018,
        diet="veg",
        allergens=["milk"],
        created_at=func.clock_timestamp(),
    )
    db_session.add(riya)
    await db_session.flush()
    for m in (me, dad, riya):
        await db_session.refresh(m)
    return {"Me": me, "Dad": dad, "Riya": riya}


@pytest.fixture
async def sf_biscuit_product(db_session):
    return await _add(db_session, fixture_product_record("sf_biscuit"))
