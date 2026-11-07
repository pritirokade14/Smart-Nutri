"""Weigh-in store (Plan 12 Task 21)."""

from datetime import UTC, date, datetime
from decimal import Decimal
from uuid import uuid4

from app.features.members import service as members_service
from app.features.weights import store
from tests.api.favourites.conftest import (
    ACC_A,
    accounts,  # noqa: F401
)

NOW = datetime(2026, 11, 7, 6, 0, tzinfo=UTC)


async def test_upsert_replaces_same_day(db_session, accounts):  # noqa: F811
    member = await members_service.get_or_create_primary(db_session, ACC_A)
    first = await store.upsert_weigh_in(db_session, member, date(2026, 11, 7), Decimal("80.0"), NOW)
    cid = uuid4()
    second = await store.upsert_weigh_in(
        db_session, member, date(2026, 11, 7), Decimal("79.4"), NOW, cid
    )
    assert second.id == first.id and second.weight_kg == Decimal("79.4")
    assert second.client_id == cid and second.source == "manual"
    assert len(await store.list_weigh_ins(db_session, member)) == 1


async def test_list_order_and_bounds(db_session, accounts):  # noqa: F811
    member = await members_service.get_or_create_primary(db_session, ACC_A)
    for d in (5, 1, 3, 2, 4):
        await store.upsert_weigh_in(db_session, member, date(2026, 11, d), Decimal(70 + d), NOW)
    days = [r.local_date.day for r in await store.list_weigh_ins(db_session, member)]
    assert days == [1, 2, 3, 4, 5]
    both = await store.list_weigh_ins(
        db_session, member, since=date(2026, 11, 2), until=date(2026, 11, 4)
    )
    assert [r.local_date.day for r in both] == [2, 3, 4]
    assert (await store.latest(db_session, member)).local_date.day == 5
    assert await store.latest(db_session, member) is not None


async def test_delete_returns_row(db_session, accounts):  # noqa: F811
    member = await members_service.get_or_create_primary(db_session, ACC_A)
    await store.upsert_weigh_in(db_session, member, date(2026, 11, 7), Decimal(80), NOW)
    gone = await store.delete_weigh_in(db_session, member, date(2026, 11, 7))
    assert gone is not None and gone.weight_kg == Decimal(80)
    assert await store.delete_weigh_in(db_session, member, date(2026, 11, 7)) is None
    assert await store.latest(db_session, member) is None
