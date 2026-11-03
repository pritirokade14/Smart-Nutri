"""Retention job: label photos after 30 days, voice answers after 24 hours (Plan 8 Task 3),
deletion tombstones after 7 days (ruling D1/B1).

Run as a Cloud Run Job, daily at 02:30 IST (Plan 8 Task 10):

    python -m app.jobs.retention [--dry-run] [--photo-days 30] [--voice-hours 24]

What it does:
- Deletes every object in the private bucket outside `voice/` (label photos and orphan uploads,
  `<account_id>/<uuid>.<ext>`) created more than `photo_days` ago.
- Deletes every `voice/` object (spoken answers) created more than `voice_hours` ago, in the
  voice-answers bucket (`settings.supabase_voice_bucket`, Plan 7) when `voice_storage` is given,
  else in the label-photo bucket.
- Sets `scans.image_path = NULL` on scans older than `photo_days`, and on any scan whose photo
  it just deleted. Scans whose object is already gone are nulled too.
- Retries the Supabase auth-user removal for every tombstone whose removal `DELETE /v1/me`
  did not confirm (`auth_deleted_at` is NULL), and records each success (m2).
- Deletes `deleted_accounts` tombstones written more than 7 days ago whose auth user is
  confirmed gone, with the erased account's leftover `account_deletes` rate-limit counter.
  Seven days is far longer than any access token of the erased account stays valid (Supabase
  JWT expiry, 1 hour by default). An unconfirmed tombstone stays: the sign-in could still
  mint tokens.

Storage is changed first, then the auth retries, then the rows in one transaction. If
storage fails, no row changes and the job exits 1. If an auth retry fails, everything else
is still done and the job exits 1. Running it again is safe: there is nothing left to delete. Logs carry
counts only, never paths, account IDs or connection details.
"""

from __future__ import annotations

import argparse
import asyncio
import logging
from collections.abc import Sequence
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from uuid import UUID

import httpx
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.logging import configure_logging
from app.db.session import build_engine, build_sessionmaker
from app.integrations.storage import STORAGE_TIMEOUT_S, StorageClient, SupabaseStorage
from app.integrations.supabase_admin import AdminUnavailable, SupabaseAdmin, SupabaseAuthAdmin

logger = logging.getLogger("app.jobs.retention")

VOICE_PREFIX = "voice"
PHOTO_DAYS = 30
VOICE_HOURS = 24
TOMBSTONE_DAYS = 7


@dataclass(frozen=True)
class RetentionResult:
    photos_deleted: int
    voice_deleted: int
    scans_nulled: int
    tombstones_purged: int = 0
    # m2: auth users of erased accounts whose removal DELETE /v1/me could not confirm.
    auth_deletes_retried: int = 0  # removed now
    auth_deletes_failed: int = 0  # still there; their tombstones stay


_NULL_FILTER = (
    "image_path is not null and (created_at < :cutoff or image_path = any(cast(:paths as text[])))"
)


async def run_retention(
    now: datetime,
    session: AsyncSession,
    storage: StorageClient,
    photo_days: int = PHOTO_DAYS,
    voice_hours: int = VOICE_HOURS,
    *,
    voice_storage: StorageClient | None = None,
    admin: SupabaseAdmin | None = None,
    dry_run: bool = False,
) -> RetentionResult:
    voice_store = voice_storage if voice_storage is not None else storage
    photo_cutoff = now - timedelta(days=photo_days)
    voice_cutoff = now - timedelta(hours=voice_hours)

    old_photos = [
        p
        for p in await storage.list_prefix("", older_than=photo_cutoff)
        if not p.startswith(VOICE_PREFIX + "/")
    ]
    old_voice = await voice_store.list_prefix(VOICE_PREFIX, older_than=voice_cutoff)
    params = {"cutoff": photo_cutoff, "paths": old_photos}
    # Scan rows past the cutoff whose object the listing did not show (already gone, or no
    # timestamp): delete their path too, so nothing older than the window survives.
    scan_paths = list(
        await session.scalars(
            text(f"select image_path from scans where {_NULL_FILTER}"),
            params,
        )
    )
    tombstone_cutoff = now - timedelta(days=TOMBSTONE_DAYS)
    old_tombstones = list(
        await session.scalars(
            text(
                "select id from deleted_accounts "
                "where deleted_at < :cutoff and auth_deleted_at is not null"
            ),
            {"cutoff": tombstone_cutoff},
        )
    )
    # m2: erased accounts whose auth user DELETE /v1/me could not confirm removing.
    unconfirmed = list(
        await session.scalars(
            text("select id from deleted_accounts where auth_deleted_at is null order by id")
        )
    )
    await session.commit()  # release the connection during the storage and auth calls

    if dry_run:
        return RetentionResult(
            len(old_photos), len(old_voice), len(scan_paths), len(old_tombstones)
        )

    if voice_store is storage:
        await storage.delete_paths(sorted(set(old_photos) | set(scan_paths) | set(old_voice)))
    else:
        await voice_store.delete_paths(sorted(old_voice))
        await storage.delete_paths(sorted(set(old_photos) | set(scan_paths)))

    removed, failed = await _retry_auth_deletes(admin, unconfirmed)

    result = await session.execute(
        text(f"update scans set image_path = null where {_NULL_FILTER}"),
        params,
    )
    if removed:
        await session.execute(
            text(
                "update deleted_accounts set auth_deleted_at = now() "
                "where id = any(cast(:ids as uuid[]))"
            ),
            {"ids": removed},
        )
    # Only tombstones whose auth user is confirmed gone: otherwise the sign-in could still
    # mint tokens, which the tombstone must keep refusing.
    purged = list(
        await session.scalars(
            text(
                "delete from deleted_accounts "
                "where deleted_at < :cutoff and auth_deleted_at is not null returning id"
            ),
            {"cutoff": tombstone_cutoff},
        )
    )
    # The erased account's account_deletes counter was kept with its tombstone.
    await session.execute(
        text("delete from rate_limit_counters where key = any(cast(:keys as text[]))"),
        {"keys": [f"acct:{account_id}" for account_id in purged]},
    )
    await session.commit()
    return RetentionResult(
        len(old_photos),
        len(old_voice),
        result.rowcount,
        len(purged),
        auth_deletes_retried=len(removed),
        auth_deletes_failed=failed,
    )


async def _retry_auth_deletes(
    admin: SupabaseAdmin | None, account_ids: Sequence[UUID]
) -> tuple[list[UUID], int]:
    """Remove these auth users again (an already-removed one counts as success). Returns the
    ids now confirmed gone and the number that failed. Without an admin client nothing is
    confirmed, so those tombstones stay."""
    if admin is None:
        return [], 0
    removed: list[UUID] = []
    for account_id in account_ids:
        try:
            await admin.delete_user(account_id)
        except AdminUnavailable:
            continue
        removed.append(account_id)
    return removed, len(account_ids) - len(removed)


async def _run_from_settings(
    *, dry_run: bool, photo_days: int, voice_hours: int
) -> RetentionResult:
    settings = get_settings()
    if not settings.supabase_url or settings.supabase_secret_key is None:
        raise RuntimeError("storage is not configured")
    engine = build_engine(settings)
    try:
        async with (
            build_sessionmaker(engine)() as session,
            httpx.AsyncClient(timeout=STORAGE_TIMEOUT_S) as http,
        ):
            storage = SupabaseStorage(
                http,
                url=settings.supabase_url,
                secret_key=settings.supabase_secret_key,
                bucket=settings.supabase_storage_bucket,
            )
            voice_storage = SupabaseStorage(
                http,
                url=settings.supabase_url,
                secret_key=settings.supabase_secret_key,
                bucket=settings.supabase_voice_bucket,
            )
            admin = SupabaseAuthAdmin(
                http, url=settings.supabase_url, secret_key=settings.supabase_secret_key
            )
            return await run_retention(
                datetime.now(UTC),
                session,
                storage,
                photo_days,
                voice_hours,
                voice_storage=voice_storage,
                admin=admin,
                dry_run=dry_run,
            )
    finally:
        await engine.dispose()


def _parse(argv: Sequence[str] | None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(prog="python -m app.jobs.retention")
    parser.add_argument("--dry-run", action="store_true", help="count only; delete nothing")
    parser.add_argument("--photo-days", type=int, default=PHOTO_DAYS)
    parser.add_argument("--voice-hours", type=int, default=VOICE_HOURS)
    args = parser.parse_args(argv)
    if args.photo_days < 1 or args.voice_hours < 1:
        parser.error("--photo-days and --voice-hours must be at least 1")
    return args


def main(argv: Sequence[str] | None = None) -> int:
    args = _parse(argv)
    configure_logging(get_settings().log_level)
    try:
        result = asyncio.run(
            _run_from_settings(
                dry_run=args.dry_run, photo_days=args.photo_days, voice_hours=args.voice_hours
            )
        )
    except Exception as exc:  # noqa: BLE001 - exit 1 with the type only (no URLs or paths)
        logger.error("retention status=failed error=%s", type(exc).__name__)
        return 1
    logger.info(
        "retention photos_deleted=%d voice_deleted=%d scans_nulled=%d tombstones_purged=%d "
        "dry_run=%s auth_deletes_retried=%d auth_deletes_failed=%d",
        result.photos_deleted,
        result.voice_deleted,
        result.scans_nulled,
        result.tombstones_purged,
        args.dry_run,
        result.auth_deletes_retried,
        result.auth_deletes_failed,
    )
    # Everything else was done; exit 1 so a sign-in that could not be removed gets noticed.
    return 1 if result.auth_deletes_failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
