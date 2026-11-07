"""The consent gate for routes that process health data or send data to AI models (F11).

`create_app()` attaches `gate_for(<feature>)` to every route of the routers listed in
`app.main.CONSENT_GATES`, so a consent withdrawn mid-session refuses the very next call with
`403 consent_required` and `details.purposes` (the missing purposes, in order). Clients route
that error to the consent screen.

The gate runs before the route's own dependencies (including `limit()`), so a refused call
does not use up rate-limit quota. Withdrawal stops processing; it does not erase stored data
(ADR 0018). Erasure is `DELETE /v1/me`.
"""

from collections.abc import Awaitable, Callable
from functools import cache
from typing import Annotated, Any, Literal
from uuid import UUID

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import ApiError, ErrorEnvelope
from app.core.security import AccountContext, auth_invalid_error, current_account
from app.db.session import get_session
from app.features.consents import service as consents_service
from app.features.me import service as me_service

Purpose = Literal["terms", "health_data", "ai_processing"]

# Feature -> purposes its routes need. Edit here only. Ruling G1 (the user's decision):
# everything that processes a product needs only `terms`; voice sends the question to AI models,
# so it also needs `ai_processing`. `health_data` is not a route gate: it gates saving member
# health fields (members/service), and analyze keeps reading stored allergies and conditions
# after a withdrawal, so an allergic member never gets `ok` (ADR 0018). The analyze explanation
# keeps its own `ai_processing` check (analyze/service).
REQUIRED: dict[str, tuple[Purpose, ...]] = {
    "analyze": ("terms",),
    "scans": ("terms",),
    "meals": ("terms",),
    # Gated on the route, not by prefix: /v1/products/{barcode}/public is public.
    "products_create": ("terms",),
    # Alternatives and compare (I3): they return rules-engine statuses, for a member's stored
    # allergies and conditions when member_id is given. Gated always, with or without it.
    "product_verdicts": ("terms",),
    "voice": ("terms", "ai_processing"),
    # Daily targets (Plan 10, ADR 0022): they process body data, so they need health_data too.
    # Gated per route (not by prefix): erasure and the display toggle need only terms.
    "targets": ("terms", "health_data"),
    "targets_prefs": ("terms",),
    # The diary and its meal slots (Plan 11, Q13): they work on `terms`. The targets part of the
    # day and week views checks `health_data` inside the handler (spec 6.6).
    "meal_slots": ("terms",),
    "diary": ("terms",),
    # Foods, units and portion overrides (Plan 12, Q13): `terms`.
    "foods": ("terms",),
}

CONSENT_RESPONSES: dict[int | str, dict[str, Any]] = {
    403: {
        "model": ErrorEnvelope,
        "description": (
            "consent_required: details.purposes lists the consents to grant (or re-grant at "
            "the current version) before this call"
        ),
    }
}


async def _missing(session: AsyncSession, account_id: UUID, purposes: tuple[str, ...]) -> list[str]:
    return await consents_service.missing_consents(session, account_id, purposes)


def require_consents(*purposes: Purpose) -> Callable[..., Awaitable[None]]:
    """FastAPI dependency: 403 `consent_required` unless every purpose is active."""

    async def _gate(
        ctx: Annotated[AccountContext, Depends(current_account)],
        session: Annotated[AsyncSession, Depends(get_session)],
    ) -> None:
        # An erased account's token is refused as invalid, not sent to the consent screen.
        if await me_service.is_deleted(session, ctx.account_id):
            raise auth_invalid_error()
        missing = await _missing(session, ctx.account_id, purposes)
        if missing:
            raise ApiError("consent_required", 403, details={"purposes": missing})

    return _gate


@cache
def gate_for(feature: str) -> Callable[..., Awaitable[None]]:
    """The (single, cached) gate dependency for a feature in `REQUIRED`."""
    return require_consents(*REQUIRED[feature])
