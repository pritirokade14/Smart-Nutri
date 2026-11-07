"""Daily targets routes (Plan 10 Task 4; spec 6.1, ADR 0022).

The router is not in `CONSENT_GATES`: each route lists its gate first, then its rate limit, so
a refused call costs no quota. Delete and display need only `terms`; everything else also needs
`health_data`.
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
from app.core.time import today_ist
from app.db.session import get_session
from app.features.me.dependencies import CurrentAccount, current_account_row
from app.features.targets import service
from app.features.targets.mapping import to_targets_out
from app.features.targets.models import DiaryGoalSettings
from app.features.targets.schemas import (
    DisplayIn,
    GoalSettingsIn,
    GoalSettingsOut,
    TargetsOut,
    TargetsPreviewIn,
)
from app.scoring import targets as engine

router = APIRouter(prefix="/v1/targets", tags=["targets"])

Current = Annotated[CurrentAccount, Depends(current_account_row)]
Session = Annotated[AsyncSession, Depends(get_session)]
AppSettings = Annotated[Settings, Depends(get_app_settings)]
MemberQuery = Annotated[UUID | None, Query(description="Defaults to the primary member")]

_RESPONSES = {**ERROR_RESPONSES, **CONSENT_RESPONSES}


def _settings_out(row: DiaryGoalSettings) -> GoalSettingsOut:
    return GoalSettingsOut.model_validate(row, from_attributes=True)


def _unusual(data: engine.BodyData) -> tuple[str, ...]:
    return engine.unusual_fields(data)


@router.get(
    "/settings",
    operation_id="targets_settings_get",
    response_model=GoalSettingsOut | None,
    responses=_RESPONSES,
    dependencies=[Depends(gate_for("targets"))],
)
async def targets_settings_get(
    current: Current, session: Session, settings: AppSettings, member_id: MemberQuery = None
) -> GoalSettingsOut | None:
    """The member's saved daily-guide settings, or null before setup."""
    member = await service.resolve_member(session, current.account.id, member_id, settings)
    row = await service.get_settings(session, member)
    await session.commit()  # the primary member may have been created
    return None if row is None else _settings_out(row)


@router.put(
    "/settings",
    operation_id="targets_settings_put",
    response_model=TargetsOut,
    responses=_RESPONSES,
    dependencies=[Depends(gate_for("targets")), Depends(limit("diary_settings"))],
)
async def targets_settings_put(
    body: GoalSettingsIn, current: Current, session: Session, settings: AppSettings
) -> TargetsOut:
    """Validate and save the settings; returns today's targets, recomputed. Information, not
    medical advice: the numbers are estimates pending clinician review."""
    member = await service.resolve_member(session, current.account.id, body.member_id, settings)
    row = await service.put_settings(session, member, body, settings)
    data = service.body_data(member, today_ist())
    result = engine.compute(data, service.goal_settings(row))
    out = to_targets_out(
        member.id, today_ist(), result, row.numbers_display, unusual=_unusual(data)
    )  # type: ignore[arg-type]
    await session.commit()
    return out


@router.post(
    "/preview",
    operation_id="targets_preview",
    response_model=TargetsOut,
    responses=_RESPONSES,
    dependencies=[Depends(gate_for("targets")), Depends(limit("targets_preview"))],
)
async def targets_preview(
    body: TargetsPreviewIn, current: Current, session: Session, settings: AppSettings
) -> TargetsOut:
    """Targets for unsaved settings and optional unsaved body data. Nothing is saved.
    `needs_body_data` is a status here, not an error."""
    member = await service.resolve_member(session, current.account.id, body.member_id, settings)
    data = service.check_input(member, body, settings, body.body)
    result = engine.compute(data, service.goal_settings(body))
    out = to_targets_out(
        member.id, today_ist(), result, body.numbers_display, unusual=_unusual(data)
    )
    await session.commit()  # the primary member may have been created
    return out


@router.get(
    "",
    operation_id="targets_get",
    response_model=TargetsOut,
    responses=_RESPONSES,
    dependencies=[Depends(gate_for("targets"))],
)
async def targets_get(
    current: Current,
    session: Session,
    settings: AppSettings,
    member_id: MemberQuery = None,
    date_: Annotated[
        date | None, Query(alias="date", description="Local date; default today")
    ] = None,
) -> TargetsOut:
    """Today's targets, computed live. A past date has no stored guide in this version, so it
    returns status `none`; a future date is 422 `date_in_future`."""
    today = today_ist()
    day = date_ or today
    if day > today:
        raise ApiError("date_in_future", 422)
    member = await service.resolve_member(session, current.account.id, member_id, settings)
    result, row = await service.targets_for_today(session, member)
    display = row.numbers_display if row is not None else "show"
    if day < today:
        result = None
    data = service.body_data(member, today)
    out = to_targets_out(
        member.id,
        day,
        result,
        display,  # type: ignore[arg-type]
        unusual=_unusual(data) if result is not None else (),
    )
    await session.commit()  # the primary member may have been created
    return out


@router.delete(
    "/settings",
    operation_id="targets_settings_delete",
    status_code=204,
    responses=_RESPONSES,
    dependencies=[Depends(gate_for("targets_prefs"))],
)
async def targets_settings_delete(
    current: Current, session: Session, settings: AppSettings, member_id: MemberQuery = None
) -> Response:
    """Erase the member's daily-guide settings. Needs only `terms`: erasure is never gated."""
    member = await service.resolve_member(session, current.account.id, member_id, settings)
    await service.delete_settings(session, member)
    await session.commit()
    return Response(status_code=204)


@router.put(
    "/display",
    operation_id="targets_display_put",
    response_model=GoalSettingsOut,
    responses=_RESPONSES,
    dependencies=[Depends(gate_for("targets_prefs")), Depends(limit("diary_settings"))],
)
async def targets_display_put(
    body: DisplayIn, current: Current, session: Session, settings: AppSettings
) -> GoalSettingsOut:
    """The eye toggle: change only how numbers are shown. Needs only `terms`, so hiding
    numbers works even after `health_data` was withdrawn (Ruling D4)."""
    member = await service.resolve_member(session, current.account.id, body.member_id, settings)
    row = await service.put_display(session, member, body)
    out = _settings_out(row)
    await session.commit()
    return out
