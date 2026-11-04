from collections.abc import Iterable
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import ApiError
from app.features.consents.models import Consent
from app.features.consents.policy import CURRENT_VERSIONS
from app.features.consents.schemas import ConsentIn, ConsentState

# Rows are append-only (DPDP audit trail): a grant row is never updated. A withdrawal is a
# new row that copies the withdrawn grant's version and granted_at and sets withdrawn_at, so
# rows order by the time of their event: withdrawn_at for withdrawals, granted_at for grants.
_EVENT_TIME = func.coalesce(Consent.withdrawn_at, Consent.granted_at)


async def _latest_by_purpose(session: AsyncSession, account_id: UUID) -> dict[str, Consent]:
    rows = await session.scalars(
        select(Consent).where(Consent.account_id == account_id).order_by(_EVENT_TIME, Consent.id)
    )
    latest: dict[str, Consent] = {}
    for row in rows:  # ascending, so the last row per purpose wins
        latest[row.purpose] = row
    return latest


def _is_active(row: Consent | None, purpose: str) -> bool:
    return row is not None and row.withdrawn_at is None and row.version == CURRENT_VERSIONS[purpose]


def _needs_update(row: Consent | None, purpose: str) -> bool:
    return row is not None and row.withdrawn_at is None and row.version != CURRENT_VERSIONS[purpose]


async def consent_states(session: AsyncSession, account_id: UUID) -> list[ConsentState]:
    latest = await _latest_by_purpose(session, account_id)
    return [
        ConsentState(
            purpose=purpose,
            version=latest[purpose].version if purpose in latest else None,
            granted=_is_active(latest.get(purpose), purpose),
            current_version=current,
            needs_update=_needs_update(latest.get(purpose), purpose),
        )
        for purpose, current in CURRENT_VERSIONS.items()
    ]


async def record_consent(
    session: AsyncSession, account_id: UUID, body: ConsentIn
) -> list[ConsentState]:
    latest = (await _latest_by_purpose(session, account_id)).get(body.purpose)
    if body.granted:
        if body.version != CURRENT_VERSIONS[body.purpose]:
            raise ApiError(
                "consent_version_mismatch",
                422,
                details={
                    "purpose": body.purpose,
                    "current_version": CURRENT_VERSIONS[body.purpose],
                },
            )
        if not _is_active(latest, body.purpose):
            # Re-granting after a withdrawal (or a version change) adds a new row.
            session.add(
                Consent(
                    account_id=account_id,
                    purpose=body.purpose,
                    version=body.version,
                    granted_at=func.clock_timestamp(),
                )
            )
    elif latest is not None and latest.withdrawn_at is None:
        # Withdrawal is always accepted, whatever version the client shows: it appends a row
        # naming the grant it withdraws. Withdrawing twice adds nothing.
        session.add(
            Consent(
                account_id=account_id,
                purpose=body.purpose,
                version=latest.version,
                granted_at=latest.granted_at,
                withdrawn_at=func.clock_timestamp(),
            )
        )
    await session.flush()
    return await consent_states(session, account_id)


async def missing_consents(
    session: AsyncSession, account_id: UUID, purposes: Iterable[str] | str
) -> list[str]:
    """The purposes (in the order given) without an unwithdrawn grant at the current version."""
    wanted = [purposes] if isinstance(purposes, str) else list(purposes)
    latest = await _latest_by_purpose(session, account_id)
    return [p for p in wanted if p not in CURRENT_VERSIONS or not _is_active(latest.get(p), p)]


async def has_active_consent(
    session: AsyncSession, account_id: UUID, purposes: Iterable[str] | str
) -> bool:
    """True only if every purpose has an unwithdrawn latest grant at the current version."""
    return not await missing_consents(session, account_id, purposes)
