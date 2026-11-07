"""Fixtures for the diary routes (Plan 11). The real consent gate runs here.

The clock is pinned to 2026-11-07 12:00 IST; the primary member is the G1 profile (via `g1`)
or the G2 profile (via `g2`), as in the targets tests.
"""

import pytest

from tests.api.conftest import clock  # noqa: F401  (pinned clock)
from tests.api.targets.conftest import (  # noqa: F401  (shared fixtures)
    ACC_A,
    ACC_B,
    ACC_C,
    G1_BODY,
    G1_SETTINGS,
    G2_BODY,
    G2_SETTINGS,
    TODAY,
    add_member,
    consented,
    g1,
    g2,
    grant,
    login,
    set_primary,
    today,
)

YESTERDAY = "2026-11-06"


@pytest.fixture
async def product_id(db_session):
    """An existing own product, for seeded entries of kind `product`."""
    from scripts.export_fixture_responses import fixture_product_record

    record = fixture_product_record("sf_biscuit")
    db_session.add(record)
    await db_session.flush()
    return record.id


@pytest.fixture
async def slot_ids(client, consented):  # noqa: F811
    """The primary's default slots: key (breakfast, lunch, snack, dinner) -> id."""
    items = (await client.get("/v1/meal-slots")).json()["items"]
    return {i["label_key"].rsplit(".", 1)[1]: i["id"] for i in items}
