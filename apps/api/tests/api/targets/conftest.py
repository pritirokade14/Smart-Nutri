"""Fixtures for the targets routes (Plan 10 Task 4).

"Today" is pinned to 2026-11-07, and the primary member is seeded so that the engine's age
(`youngest_age`, Ruling D2) is the golden-case age: birth_year 1997 gives 28.
"""

from datetime import date
from uuid import UUID

import pytest

from app.features.members import service as members_service
from tests.api.members.conftest import (  # noqa: F401  (shared fixtures)
    ACC_A,
    ACC_B,
    ACC_C,
    add_member,
    consented,
    grant,
    login,
)

TODAY = date(2026, 11, 7)
URL = "/v1/targets"

G1_SETTINGS = {
    "direction": "gain",
    "activity_level": "moderate",
    "rate_pct_bw_per_week": 0.25,
    "pregnant_or_breastfeeding": False,
}
G2_SETTINGS = {
    "direction": "lose",
    "activity_level": "light",
    "rate_pct_bw_per_week": 0.5,
    "pregnant_or_breastfeeding": False,
}


@pytest.fixture(autouse=True)
def today(monkeypatch, clock):
    """The clock reads 2026-11-07 12:00 IST (the `clock` fixture)."""
    monkeypatch.setattr("app.features.targets.service.today_ist", lambda: TODAY)
    return TODAY


@pytest.fixture
def set_primary(db_session):
    """Create or update ACC_A's primary member with the given body fields."""

    async def _set(**fields):
        member = await members_service.get_or_create_primary(db_session, ACC_A)
        for key, value in fields.items():
            setattr(member, key, value)
        await db_session.flush()
        return member

    return _set


G1_BODY = {
    "birth_year": 1997,
    "sex": "male",
    "height_cm": 175,
    "weight_kg": 70,
    "goal": "build_muscle",
}
G2_BODY = {
    "birth_year": 1985,
    "sex": "female",
    "height_cm": 160,
    "weight_kg": 80,
    "goal": "weight_loss",
}


@pytest.fixture
async def g1(consented, set_primary) -> UUID:  # noqa: F811
    """ACC_A, all consents, primary member = the G1 profile (male 28, 175 cm, 70 kg)."""
    return (await set_primary(**G1_BODY)).id


@pytest.fixture
async def g2(consented, set_primary) -> UUID:  # noqa: F811
    return (await set_primary(**G2_BODY)).id
