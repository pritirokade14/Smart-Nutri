"""Fixtures for the meal-slot routes (Plan 11 Task 2). The real consent gate runs here."""

import pytest

from tests.api.conftest import clock  # noqa: F401  (pinned clock)
from tests.api.members.conftest import (  # noqa: F401  (shared fixtures)
    ACC_A,
    ACC_B,
    ACC_C,
    add_member,
    consented,
    grant,
    login,
)

URL = "/v1/meal-slots"


@pytest.fixture
async def terms_only(login, grant):  # noqa: F811
    """ACC_A with only the `terms` consent (slots need nothing else)."""
    await grant(ACC_A, ("terms",))
    login(ACC_A)
    return ACC_A
