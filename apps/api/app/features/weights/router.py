"""Weight log routes (Plan 12 Task 23; spec 6.5, 6.6; rulings G24-G28).

The router is not in `CONSENT_GATES`: each route lists its gate first, then its rate limit, so a
refused call costs no quota. Put, list and trend need `terms` and `health_data` (weights are
body data); delete needs only `terms`, because erasure is never gated. Solo only: the member
resolves like the diary's (Q9).
"""

from datetime import date
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query, Response
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings, get_app_settings
from app.core.consent import CONSENT_RESPONSES, gate_for
from app.core.errors import ERROR_RESPONSES, ApiError
from app.core.ratelimit import limit
from app.db.session import get_session
from app.features.me.dependencies import CurrentAccount, current_account_row
from app.features.targets import service as targets_service
from app.features.weights import service
from app.features.weights.schemas import WeightIn, WeightOut, WeightsOut, WeightTrendOut

router = APIRouter(prefix="/v1/weights", tags=["weights"])

Current = Annotated[CurrentAccount, Depends(current_account_row)]
Session = Annotated[AsyncSession, Depends(get_session)]
AppSettings = Annotated[Settings, Depends(get_app_settings)]
MemberQuery = Annotated[UUID | None, Query(description="Defaults to the primary member")]

_RESPONSES = {**ERROR_RESPONSES, **CONSENT_RESPONSES}


@router.get(
    "/trend",
    operation_id="weights_trend_get",
    response_model=WeightTrendOut,
    response_model_by_alias=True,
    responses=_RESPONSES,
    dependencies=[Depends(gate_for("weights"))],
)
async def weights_trend_get(
    current: Current,
    session: Session,
    settings: AppSettings,
    member_id: MemberQuery = None,
    days: Annotated[
        int,
        Query(
            description="Window in days: 30, 90 or 365", json_schema_extra={"enum": [30, 90, 365]}
        ),
    ] = 90,
) -> WeightTrendOut:
    """The weight trend, weekly rate and projection, computed from the member's full history
    and sliced to the window. Every kg, the rate and the target are null under `hide_all`
    (`y` is kept for the chart's shape). Information, not medical advice; the thresholds are
    pending clinician review."""
    if days not in (30, 90, 365):
        raise ApiError("validation_error", 422, details={"fields": ["query.days"]})
    member = await targets_service.resolve_member(session, current.account.id, member_id, settings)
    today = await service.local_today(session, current.account.id)
    out = await service.trend(session, member, days, today)
    await session.commit()  # the primary member may have been created
    return out


@router.get(
    "",
    operation_id="weights_list",
    response_model=WeightsOut,
    responses=_RESPONSES,
    dependencies=[Depends(gate_for("weights"))],
)
async def weights_list(
    current: Current,
    session: Session,
    settings: AppSettings,
    member_id: MemberQuery = None,
    from_: Annotated[
        date | None, Query(alias="from", description="Local date; default 89 days back")
    ] = None,
    to: Annotated[date | None, Query(description="Local date; default today")] = None,
) -> WeightsOut:
    """The member's weigh-ins, oldest first. Default the last 90 local days; a range longer
    than 400 days is 422 `date_range_too_long`."""
    member = await targets_service.resolve_member(session, current.account.id, member_id, settings)
    today = await service.local_today(session, current.account.id)
    out = await service.list_range(session, member, from_, to, today)
    await session.commit()  # the primary member may have been created
    return out


@router.put(
    "/{day}",
    operation_id="weights_put",
    response_model=WeightOut,
    responses=_RESPONSES,
    dependencies=[Depends(gate_for("weights")), Depends(limit("weights"))],
)
async def weights_put(
    day: date, body: WeightIn, current: Current, session: Session, settings: AppSettings
) -> WeightOut:
    """Create or replace the weigh-in of a local day (200 either way; one per day). 422
    `weight_out_of_range` (outside 2 to 300 kg), `weight_needs_confirm` (outside 30 to 200 kg,
    or a big change since the last weigh-in; resend with `confirm_unusual`; `details.previous` is
    null under `hide_all`), `date_in_future`, `date_too_old` (over 400 days). A repeated
    `client_id` returns the stored row. Today's daily guide is recomputed."""
    member = await targets_service.resolve_member(
        session, current.account.id, body.member_id, settings
    )
    today = await service.local_today(session, current.account.id)
    row, hidden = await service.put_weigh_in(session, member, day, body, today)
    out = service.to_out(row, hidden)
    await session.commit()
    return out


@router.delete(
    "/{day}",
    operation_id="weights_delete",
    status_code=204,
    responses=_RESPONSES,
    dependencies=[Depends(gate_for("weights_erase"))],
)
async def weights_delete(
    day: date,
    current: Current,
    session: Session,
    settings: AppSettings,
    member_id: MemberQuery = None,
) -> Response:
    """Delete a weigh-in. Needs only `terms`: erasure is never gated. 404 `weight_not_found`."""
    member = await targets_service.resolve_member(session, current.account.id, member_id, settings)
    today = await service.local_today(session, current.account.id)
    await service.delete_weigh_in(session, member, day, today)
    await session.commit()
    return Response(status_code=204)
