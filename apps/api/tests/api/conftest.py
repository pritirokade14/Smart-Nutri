from collections.abc import AsyncIterator

import pytest
from sqlalchemy.ext.asyncio import AsyncConnection, AsyncSession

from tests.db.conftest import alembic_cfg, db, migrated, pg_url  # noqa: F401  (shared DB fixtures)


@pytest.fixture
async def db_session(db: AsyncConnection) -> AsyncIterator[AsyncSession]:  # noqa: F811
    """A session on the rolled-back test connection (superuser, so it bypasses RLS like the API)."""
    async with AsyncSession(
        bind=db, expire_on_commit=False, join_transaction_mode="create_savepoint"
    ) as session:
        yield session


@pytest.fixture
def consents_granted(monkeypatch):
    """Bypass the consent route gate (Plan 8 Task 1) for tests about something else, in
    every app the test builds. Only the gate: the members health-data check still runs.

    The gate itself is tested in tests/api/test_consent_gate.py against real consent rows.
    """
    from app.core import consent

    async def _none_missing(*_args) -> list[str]:
        return []

    monkeypatch.setattr(consent, "_missing", _none_missing)


# Test folders whose routes are gated but whose tests are about something else.
_GATE_BYPASS_DIRS = ("analyze", "scans", "products", "meals", "discovery")


@pytest.fixture(autouse=True)
def _bypass_consent_gate_outside_gate_tests(request):
    if request.node.path.parent.name in _GATE_BYPASS_DIRS:
        request.getfixturevalue("consents_granted")


class Clock:
    """Pins `app.core.time.now_utc` (Plan 11). `set("2026-11-07T06:30:00Z")` moves it."""

    def __init__(self, monkeypatch, start: str) -> None:
        self._monkeypatch = monkeypatch
        self.set(start)

    def set(self, iso: str) -> None:
        from datetime import datetime

        self.now = datetime.fromisoformat(iso)
        self._monkeypatch.setattr("app.core.time.now_utc", lambda: self.now)


@pytest.fixture
def clock(monkeypatch) -> Clock:
    """The clock, pinned to 2026-11-07 12:00 IST (06:30Z). Opt in per test or via autouse."""
    return Clock(monkeypatch, "2026-11-07T06:30:00+00:00")


@pytest.fixture
def seed_day(db_session):
    """Insert a frozen `diary_days` row computed from a settings dict and body dict."""
    from datetime import date

    from sqlalchemy.dialects.postgresql import insert

    from app.features.diary.frozen import to_row_values
    from app.features.diary.models import DiaryDay
    from app.features.targets import service as targets_service
    from app.features.targets.schemas import GoalSettingsIn
    from app.scoring import targets as engine

    async def _seed(member, day: str, settings: dict, age: int | None = None, **extra):
        body = targets_service.body_data(member, date.fromisoformat(day))
        goal = targets_service.goal_settings(GoalSettingsIn(**settings))
        values = to_row_values(engine.compute(body, goal)) | extra
        await db_session.execute(
            insert(DiaryDay).values(
                member_id=member.id,
                local_date=date.fromisoformat(day),
                account_id=member.account_id,
                **values,
            )
        )
        await db_session.flush()

    return _seed
