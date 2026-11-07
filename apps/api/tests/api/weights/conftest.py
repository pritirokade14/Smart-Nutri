"""Fixtures for the weights tests (Plan 12 slice 6). The real consent gate runs here."""

from datetime import UTC, date, datetime
from decimal import Decimal

import pytest

from app.features.members import service as members_service
from app.features.targets.models import DiaryGoalSettings
from app.features.weights import store
from tests.api.favourites.conftest import (  # noqa: F401  (shared fixtures)
    ACC_A,
    ACC_B,
    G1_SETTINGS,
    accounts,
    clock,
    consented,
    fake_off,
    g1,
    grant,
    login,
    set_primary,
    settings,
    today,
)
from tests.api.targets.conftest import add_member  # noqa: F401

URL = "/v1/weights"
TREND = "/v1/weights/trend"
NOW = datetime(2026, 11, 7, 6, 30, tzinfo=UTC)

# The G5 profile of the targets fixtures: male 35, 170 cm, lose 0.75 %/week toward 75 kg.
G5_BODY = {
    "birth_year": 1990,
    "sex": "male",
    "height_cm": 170,
    "weight_kg": 80,
    "goal": "weight_loss",
}
G5_SETTINGS = {
    "direction": "lose",
    "activity_level": "light",
    "rate_pct_bw_per_week": 0.75,
    "target_weight_kg": 75,
    "pregnant_or_breastfeeding": False,
}


@pytest.fixture
async def g5(consented, set_primary):  # noqa: F811
    """ACC_A with all consents and the G5 profile (member weight 80 kg)."""
    return await set_primary(**G5_BODY)


@pytest.fixture
def seed_weights(db_session):
    """Insert weigh-ins straight into the store: [(date, kg), ...] for the primary member."""

    async def _seed(rows, account=ACC_A):
        member = await members_service.get_or_create_primary(db_session, account)
        for day, kg in rows:
            await store.upsert_weigh_in(
                db_session, member, date.fromisoformat(str(day)), Decimal(str(kg)), NOW
            )
        await db_session.flush()
        return member

    return _seed


@pytest.fixture
def put_settings_row(db_session):
    """Write a goal-settings row without the API's body-data checks."""

    async def _put(member, **cols):
        values = {
            "direction": "lose",
            "activity_level": "light",
            "rate_pct_bw_per_week": Decimal("0.75"),
        } | cols
        db_session.add(
            DiaryGoalSettings(member_id=member.id, account_id=member.account_id, **values)
        )
        await db_session.flush()

    return _put


def body(kg, **extra) -> dict:
    return {"weight_kg": kg} | extra
