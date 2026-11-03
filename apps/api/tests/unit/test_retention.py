"""Plan 8 Task 3: the retention job (30-day label photos, 24-hour voice answers).

Uses the throwaway test database (tests/db) and FakeStorage with object timestamps.
"""

from collections.abc import AsyncIterator
from datetime import UTC, datetime, timedelta
from uuid import UUID, uuid4

import pytest
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncConnection, AsyncSession

from app.core.security import AccountContext
from app.features.me.service import ensure_account
from app.jobs import retention
from app.jobs.retention import RetentionResult, run_retention
from tests.db.conftest import alembic_cfg, db, migrated, pg_url  # noqa: F401
from tests.fakes.storage import FakeStorage, missing_bucket_storage

A = UUID("11111111-1111-1111-1111-111111111111")
NOW = datetime(2026, 11, 3, 21, 0, tzinfo=UTC)


@pytest.fixture
async def session(db: AsyncConnection) -> AsyncIterator[AsyncSession]:  # noqa: F811
    async with AsyncSession(
        bind=db, expire_on_commit=False, join_transaction_mode="create_savepoint"
    ) as s:
        yield s


async def add_scan(session: AsyncSession, path: str | None, age: timedelta) -> UUID:
    await ensure_account(session, AccountContext(A, None))
    return (
        await session.execute(
            text(
                "insert into scans (account_id, image_path, created_at) values (:a, :p, :c) "
                "returning id"
            ),
            {"a": A, "p": path, "c": NOW - age},
        )
    ).scalar_one()


async def image_path(session: AsyncSession, scan_id: UUID) -> str | None:
    return (
        await session.execute(text("select image_path from scans where id = :i"), {"i": scan_id})
    ).scalar_one()


def label(age: timedelta) -> tuple[str, datetime]:
    return f"{A}/{uuid4()}.jpg", NOW - age


def storage_with(*objects: tuple[str, datetime]) -> FakeStorage:
    return FakeStorage({p: b"x" for p, _ in objects}, created=dict(objects))


async def test_photos_older_than_30_days_deleted_and_image_path_nulled(session):
    path, created = label(timedelta(days=31))
    storage = storage_with((path, created))
    scan = await add_scan(session, path, timedelta(days=31))
    result = await run_retention(NOW, session, storage)
    assert result == RetentionResult(photos_deleted=1, voice_deleted=0, scans_nulled=1)
    assert path not in storage.objects
    assert await image_path(session, scan) is None


async def test_photo_29_days_old_kept(session):
    path, created = label(timedelta(days=29))
    storage = storage_with((path, created))
    scan = await add_scan(session, path, timedelta(days=29))
    result = await run_retention(NOW, session, storage)
    assert result == RetentionResult(0, 0, 0)
    assert path in storage.objects
    assert await image_path(session, scan) == path


async def test_orphan_upload_without_a_scan_is_deleted(session):
    old, old_at = label(timedelta(days=40))
    new, new_at = label(timedelta(hours=1))
    storage = storage_with((old, old_at), (new, new_at))
    result = await run_retention(NOW, session, storage)
    assert result.photos_deleted == 1
    assert list(storage.objects) == [new]


async def test_voice_older_than_24h_deleted(session):
    old = (f"voice/{A}/{uuid4()}.mp3", NOW - timedelta(hours=25))
    new = (f"voice/{A}/{uuid4()}.mp3", NOW - timedelta(hours=23))
    storage = storage_with(old, new)
    result = await run_retention(NOW, session, storage)
    assert result == RetentionResult(photos_deleted=0, voice_deleted=1, scans_nulled=0)
    assert list(storage.objects) == [new[0]]


async def test_voice_is_not_counted_as_a_label_photo(session):
    storage = storage_with((f"voice/{A}/{uuid4()}.mp3", NOW - timedelta(days=40)))
    result = await run_retention(NOW, session, storage)
    assert result.photos_deleted == 0 and result.voice_deleted == 1


async def test_separate_voice_bucket_is_cleaned(session):
    """Plan 7 keeps voice answers in their own bucket (settings.supabase_voice_bucket)."""
    photo = label(timedelta(days=31))
    photos = storage_with(photo)
    old = (f"voice/{A}/{uuid4()}.mp3", NOW - timedelta(hours=25))
    new = (f"voice/{A}/{uuid4()}.mp3", NOW - timedelta(hours=23))
    voices = storage_with(old, new)
    result = await run_retention(NOW, session, photos, voice_storage=voices)
    assert result == RetentionResult(photos_deleted=1, voice_deleted=1, scans_nulled=0)
    assert list(voices.objects) == [new[0]]
    assert photos.objects == {} and voices.deleted == [old[0]]


async def test_voice_bucket_outage_changes_nothing(session):
    path, created = label(timedelta(days=31))
    photos = storage_with((path, created))
    voices = storage_with((f"voice/{A}/{uuid4()}.mp3", NOW - timedelta(days=2)))
    voices.unavailable = True
    scan = await add_scan(session, path, timedelta(days=31))
    with pytest.raises(Exception):  # noqa: B017 - StorageUnavailable surfaces; the job exits 1
        await run_retention(NOW, session, photos, voice_storage=voices)
    assert photos.deleted == [] and await image_path(session, scan) == path


async def test_missing_storage_object_still_nulls_image_path(session):
    scan = await add_scan(session, f"{A}/{uuid4()}.jpg", timedelta(days=45))
    result = await run_retention(NOW, session, FakeStorage())
    assert result.scans_nulled == 1
    assert await image_path(session, scan) is None


async def test_object_deleted_by_age_nulls_a_younger_scan_row(session):
    # The photo is uploaded before the scan row is created, so it can pass 30 days first.
    path = f"{A}/{uuid4()}.jpg"
    storage = storage_with((path, NOW - timedelta(days=30, minutes=1)))
    scan = await add_scan(session, path, timedelta(days=29, hours=23))
    result = await run_retention(NOW, session, storage)
    assert result == RetentionResult(photos_deleted=1, voice_deleted=0, scans_nulled=1)
    assert await image_path(session, scan) is None


async def test_run_is_idempotent(session):
    path, created = label(timedelta(days=31))
    voice = (f"voice/{A}/{uuid4()}.mp3", NOW - timedelta(days=2))
    storage = storage_with((path, created), voice)
    await add_scan(session, path, timedelta(days=31))
    first = await run_retention(NOW, session, storage)
    assert first == RetentionResult(1, 1, 1)
    assert await run_retention(NOW, session, storage) == RetentionResult(0, 0, 0)


async def test_dry_run_counts_but_changes_nothing(session):
    path, created = label(timedelta(days=31))
    voice = (f"voice/{A}/{uuid4()}.mp3", NOW - timedelta(days=2))
    storage = storage_with((path, created), voice)
    scan = await add_scan(session, path, timedelta(days=31))
    result = await run_retention(NOW, session, storage, dry_run=True)
    assert result == RetentionResult(1, 1, 1)
    assert set(storage.objects) == {path, voice[0]} and storage.deleted == []
    assert await image_path(session, scan) == path


async def test_custom_windows(session):
    path, created = label(timedelta(days=8))
    storage = storage_with((path, created))
    assert (await run_retention(NOW, session, storage, photo_days=7)).photos_deleted == 1


async def test_storage_outage_changes_no_rows(session):
    path, created = label(timedelta(days=31))
    storage = storage_with((path, created))
    storage.unavailable = True
    scan = await add_scan(session, path, timedelta(days=31))
    with pytest.raises(Exception):  # noqa: B017 - StorageUnavailable surfaces; the job exits 1
        await run_retention(NOW, session, storage)
    assert await image_path(session, scan) == path


def test_main_logs_counts_only(monkeypatch, capsys):
    async def fake_run(*, dry_run, photo_days, voice_hours):
        assert (dry_run, photo_days, voice_hours) == (True, 30, 24)
        return RetentionResult(2, 3, 1, tombstones_purged=4)

    monkeypatch.setattr(retention, "_run_from_settings", fake_run)
    assert retention.main(["--dry-run"]) == 0
    out = capsys.readouterr().out  # configure_logging writes JSON lines to stdout
    assert "photos_deleted=2 voice_deleted=3 scans_nulled=1 tombstones_purged=4 dry_run=True" in out


def test_main_failure_exits_1_without_details(monkeypatch, capsys):
    async def boom(**_):
        raise RuntimeError("postgresql://user:secret@host/db")

    monkeypatch.setattr(retention, "_run_from_settings", boom)
    assert retention.main([]) == 1
    out = capsys.readouterr().out
    assert "secret" not in out and "error=RuntimeError" in out


# --- D1/B1: deletion tombstones are kept 7 days, then purged ---------------------------------


async def add_tombstone(session: AsyncSession, account_id: UUID, age: timedelta) -> None:
    await session.execute(
        text("insert into deleted_accounts (id, deleted_at) values (:a, :d)"),
        {"a": account_id, "d": NOW - age},
    )
    # The account_deletes counter is kept with the tombstone (D1/S5) and goes with it.
    await session.execute(
        text(
            "insert into rate_limit_counters (key, bucket, window_start, count) "
            "values (:k, 'account_deletes', :d, 1)"
        ),
        {"k": f"acct:{account_id}", "d": NOW - age},
    )


async def tombstone_ids(session: AsyncSession) -> set[UUID]:
    return set(await session.scalars(text("select id from deleted_accounts")))


async def counter_keys(session: AsyncSession) -> set[str]:
    return set(await session.scalars(text("select key from rate_limit_counters")))


async def test_tombstones_older_than_7_days_are_purged_with_their_counter(session):
    old, young = uuid4(), uuid4()
    await add_tombstone(session, old, timedelta(days=7, minutes=1))
    await add_tombstone(session, young, timedelta(days=6, hours=23))
    result = await run_retention(NOW, session, FakeStorage())
    assert result == RetentionResult(0, 0, 0, tombstones_purged=1)
    assert await tombstone_ids(session) == {young}
    assert await counter_keys(session) == {f"acct:{young}"}


async def test_dry_run_counts_tombstones_but_keeps_them(session):
    old = uuid4()
    await add_tombstone(session, old, timedelta(days=10))
    result = await run_retention(NOW, session, FakeStorage(), dry_run=True)
    assert result.tombstones_purged == 1
    assert await tombstone_ids(session) == {old}


async def test_storage_outage_purges_no_tombstone(session):
    old = uuid4()
    await add_tombstone(session, old, timedelta(days=10))
    storage = FakeStorage()
    storage.unavailable = True
    with pytest.raises(Exception):  # noqa: B017 - StorageUnavailable surfaces; the job exits 1
        await run_retention(NOW, session, storage)
    assert await tombstone_ids(session) == {old}


async def test_missing_buckets_mean_nothing_to_delete(session):
    """C1: both buckets missing (not created yet on an environment): the job still nulls old
    scan paths and purges tombstones instead of failing."""
    path, _ = label(timedelta(days=31))
    scan = await add_scan(session, path, timedelta(days=31))
    old = uuid4()
    await add_tombstone(session, old, timedelta(days=10))
    result = await run_retention(
        NOW,
        session,
        missing_bucket_storage("label-photos"),
        voice_storage=missing_bucket_storage("voice-answers"),
    )
    assert result == RetentionResult(0, 0, scans_nulled=1, tombstones_purged=1)
    assert await image_path(session, scan) is None
    assert await tombstone_ids(session) == set()


def test_tombstone_window_is_7_days():
    # Ruling D1: well past the access-token lifetime (Supabase JWT expiry, 1 h by default).
    assert retention.TOMBSTONE_DAYS == 7
