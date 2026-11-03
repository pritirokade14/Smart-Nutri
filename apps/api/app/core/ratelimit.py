"""Fixed-window rate limiting backed by ``rate_limit_counters``.

Each request atomically upserts ``count + 1`` for (key, bucket, window_start) and compares the
returned count with the configured limit. Windows are UTC-aligned (``date_trunc(..., 'UTC')``)
and computed in the database, so every API instance agrees. The counter is committed
immediately, so rejected requests still count and a failed route does not refund the quota
(the one exception is an explicit ``refund()``, for work that provably never happened).
"""

from collections.abc import Awaitable, Callable
from typing import Annotated
from uuid import UUID

from fastapi import Depends, Request
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings, get_app_settings
from app.core.errors import ApiError
from app.core.security import AccountContext, auth_invalid_error, current_account
from app.db.session import get_session
from app.features.me import service as me_service

# bucket -> (window, settings attribute holding the limit)
BUCKETS: dict[str, tuple[str, str]] = {
    "label_scans": ("day", "rate_limit_label_scans_per_day"),
    "scan_uploads": ("day", "rate_limit_scan_uploads_per_day"),
    "label_requests": ("day", "rate_limit_label_requests_per_day"),
    "product_creates": ("day", "rate_limit_product_creates_per_day"),
    "voice": ("day", "rate_limit_voice_per_day"),
    "reports": ("day", "rate_limit_reports_per_day"),
    "analyze": ("hour", "rate_limit_analyze_per_hour"),
    "product_lookups": ("hour", "rate_limit_product_lookups_per_hour"),
    "public": ("minute", "rate_limit_public_per_minute"),
    "meal_logs": ("day", "rate_limit_meal_logs_per_day"),
    "search": ("minute", "rate_limit_search_per_minute"),
    # Ruling D1/S5: consent writes and account deletion.
    "consents": ("day", "rate_limit_consents_per_day"),
    "account_deletes": ("day", "rate_limit_account_deletes_per_day"),
}
ERROR_CODES = {"label_scans": "rate_limited_scans", "voice": "rate_limited_voice"}
_DEFAULT_CODE = "rate_limited"

# Fixed literals only (never user input): safe to interpolate into the statement.
_INTERVALS = {"day": "1 day", "hour": "1 hour", "minute": "1 minute"}


def client_ip(request: Request, settings: Settings) -> str:
    """Client IP for the ``public`` bucket.

    With ``trusted_proxy_hops`` = N > 0 the IP is the Nth entry from the right of
    X-Forwarded-For: trusted proxies append to the right, so anything further left is
    client-controlled and ignored. Falls back to the socket peer if the header is missing/short.
    """
    hops = settings.trusted_proxy_hops
    if hops > 0:
        header = request.headers.get("x-forwarded-for", "")
        parts = [p.strip() for p in header.split(",") if p.strip()]
        if len(parts) >= hops:
            return parts[-hops]
    return request.client.host if request.client else "unknown"


def _statement(window: str) -> str:
    return f"""
        WITH w AS (SELECT date_trunc('{window}', now(), 'UTC') AS start)
        INSERT INTO rate_limit_counters (key, bucket, window_start, count)
        SELECT :key, :bucket, w.start, 1 FROM w
        ON CONFLICT (key, bucket, window_start)
        DO UPDATE SET count = rate_limit_counters.count + 1
        RETURNING count,
            CEIL(EXTRACT(EPOCH FROM (window_start + interval '{_INTERVALS[window]}' - now())))
                AS retry_after
    """


async def _hit(session: AsyncSession, settings: Settings, key: str, bucket: str) -> None:
    window, attr = BUCKETS[bucket]
    max_count: int = getattr(settings, attr)
    row = (await session.execute(text(_statement(window)), {"key": key, "bucket": bucket})).one()
    await session.commit()
    if row.count > max_count:
        retry_after = max(1, int(row.retry_after))
        raise ApiError(
            ERROR_CODES.get(bucket, _DEFAULT_CODE),
            429,
            details={"retry_after": retry_after},
            headers={"Retry-After": str(retry_after)},
        )


async def consume(
    session: AsyncSession, settings: Settings, *, account_id: UUID, bucket: str
) -> None:
    """Count one use of an account bucket from inside a service (not as a dependency).

    For routes where only some requests may count (e.g. paid label extractions, not cache
    hits). Like `limit()`, it COMMITS `session` so the count survives a later failure; to
    keep that from committing the caller's work by surprise, it refuses to run while ORM
    writes are staged. Call it before staging any write.
    """
    _check_account_bucket(session, bucket, "consume")
    await _hit(session, settings, f"acct:{account_id}", bucket)


async def refund(
    session: AsyncSession, settings: Settings, *, account_id: UUID, bucket: str
) -> None:
    """Give back one use counted by `consume()` when the work never happened (e.g. the
    provider refused before any paid call). Floored at 0; a window that has rolled over is
    left alone. Commits like `consume()` and refuses to run while ORM writes are staged."""
    _check_account_bucket(session, bucket, "refund")
    window, _ = BUCKETS[bucket]
    await session.execute(
        text(_REFUND.format(window=window)),
        {"key": f"acct:{account_id}", "bucket": bucket},
    )
    await session.commit()


# `window` is a fixed literal from BUCKETS (never user input).
_REFUND = """
    UPDATE rate_limit_counters SET count = GREATEST(count - 1, 0)
    WHERE key = :key AND bucket = :bucket
      AND window_start = date_trunc('{window}', now(), 'UTC')
"""


def _check_account_bucket(session: AsyncSession, bucket: str, caller: str) -> None:
    if bucket not in BUCKETS or bucket == "public":
        raise KeyError(f"unknown account rate-limit bucket: {bucket}")
    if session.new or session.dirty or session.deleted:
        raise RuntimeError(f"{caller}() would commit staged writes; call it before staging them")


def limit(bucket: str, *, allow_deleted: bool = False) -> Callable[..., Awaitable[None]]:
    """FastAPI dependency enforcing ``bucket``. ``public`` is keyed by client IP, no auth.

    An erased account (tombstoned, ruling D1/B1) gets 401 `auth_invalid` before anything is
    counted, so its leftover token re-creates no counter row. Only `DELETE /v1/me` passes
    ``allow_deleted=True``: a retry after a partial failure must still reach it.
    """
    if bucket not in BUCKETS:
        raise KeyError(f"unknown rate-limit bucket: {bucket}")

    if bucket == "public":

        async def _by_ip(
            request: Request,
            session: Annotated[AsyncSession, Depends(get_session)],
            settings: Annotated[Settings, Depends(get_app_settings)],
        ) -> None:
            ip = client_ip(request, settings)
            await _hit(session, settings, f"ip:{ip}", bucket)

        return _by_ip

    async def _by_account(
        account: Annotated[AccountContext, Depends(current_account)],
        session: Annotated[AsyncSession, Depends(get_session)],
        settings: Annotated[Settings, Depends(get_app_settings)],
    ) -> None:
        if not allow_deleted and await me_service.is_deleted(session, account.account_id):
            raise auth_invalid_error()
        await _hit(session, settings, f"acct:{account.account_id}", bucket)

    return _by_account
