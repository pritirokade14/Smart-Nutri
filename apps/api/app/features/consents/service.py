from collections.abc import Iterable
from uuid import UUID

from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import ApiError
from app.features.consents.models import Consent
from app.features.consents.policy import CURRENT_VERSIONS
from app.features.consents.schemas import ConsentIn, ConsentState


async def _latest_by_purpose(session: AsyncSession, account_id: UUID) -> dict[str, Consent]:
    rows = await session.scalars(
        select(Consent)
        .where(Consent.account_id == account_id)
        .order_by(Consent.granted_at, Consent.id)
    )
    latest: dict[str, Consent] = {}
    for row in rows:  # ascending, so the last row per purpose wins
        latest[row.purpose] = row
    return latest


def _is_active(row: Consent | None, purpose: str) -> bool:
    return row is not None and row.withdrawn_at is None and row.version == CURRENT_VERSIONS[purpose]


async def consent_states(session: AsyncSession, account_id: UUID) -> list[ConsentState]:
    latest = await _latest_by_purpose(session, account_id)
    return [
        ConsentState(
            purpose=purpose,
            version=latest[purpose].version if purpose in latest else None,
            granted=_is_active(latest.get(purpose), purpose),
            current_version=current,
        )
        for purpose, current in CURRENT_VERSIONS.items()
    ]


async def record_consent(
    session: AsyncSession, account_id: UUID, body: ConsentIn
) -> list[ConsentState]:
    if body.version != CURRENT_VERSIONS[body.purpose]:
        raise ApiError(
            "consent_version_mismatch",
            422,
            details={"purpose": body.purpose, "current_version": CURRENT_VERSIONS[body.purpose]},
        )
    if body.granted:
        latest = (await _latest_by_purpose(session, account_id)).get(body.purpose)
        if not _is_active(latest, body.purpose):
            # Re-granting after a withdrawal adds a new row; history is never rewritten.
            session.add(
                Consent(
                    account_id=account_id,
                    purpose=body.purpose,
                    version=body.version,
                    granted_at=func.clock_timestamp(),
                )
            )
    else:
        # Withdrawal marks the open rows; the rows themselves (the audit trail) stay.
        await session.execute(
            update(Consent)
            .where(
                Consent.account_id == account_id,
                Consent.purpose == body.purpose,
                Consent.withdrawn_at.is_(None),
            )
            .values(withdrawn_at=func.clock_timestamp())
        )
    await session.flush()
    return await consent_states(session, account_id)


async def has_active_consent(
    session: AsyncSession, account_id: UUID, purposes: Iterable[str] | str
) -> bool:
    """True only if every purpose has an unwithdrawn latest grant at the current version."""
    wanted = [purposes] if isinstance(purposes, str) else list(purposes)
    if any(p not in CURRENT_VERSIONS for p in wanted):
        return False
    latest = await _latest_by_purpose(session, account_id)
    return all(_is_active(latest.get(p), p) for p in wanted)
