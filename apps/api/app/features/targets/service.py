"""Daily targets: settings storage and the mapping between rows, members and the engine
(Plan 10 Task 4). No FastAPI imports.

The engine (`app.scoring.targets`) decides every number. Targets are information, never
verdicts: nothing here touches `analyze`.
"""

from datetime import date
from decimal import Decimal
from uuid import UUID

from sqlalchemy import delete, func, select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings
from app.core.errors import ApiError
from app.core.time import today_ist
from app.features.members import service as members_service
from app.features.members.models import Member
from app.features.targets.models import DiaryGoalSettings
from app.features.targets.schemas import BodyDataIn, DisplayIn, GoalSettingsIn
from app.scoring import targets as engine
from app.scoring.config import ScoringConfig, load_config


def _dec(value: object) -> Decimal | None:
    return None if value is None else Decimal(str(value))


def settings_error(exc: engine.SettingsRuleError) -> ApiError:
    """The engine's rule error as a 422 with a literal code (each has an `error.<code>` key)."""
    match exc.code:
        case "fat_pct_out_of_range":
            return ApiError("fat_pct_out_of_range", 422, details=exc.details)
        case "rate_not_allowed":
            return ApiError("rate_not_allowed", 422, details=exc.details)
        case "goal_not_allowed_minor":
            return ApiError("goal_not_allowed_minor", 422, details=exc.details)
        case "goal_not_allowed_underweight":
            return ApiError("goal_not_allowed_underweight", 422, details=exc.details)
        case "target_weight_too_low":
            return ApiError("target_weight_too_low", 422, details=exc.details)
        case "body_fat_out_of_range":
            return ApiError("body_fat_out_of_range", 422, details=exc.details)
    raise exc  # an engine code without an API mapping is a bug, not a 422


async def resolve_member(
    session: AsyncSession, account_id: UUID, member_id: UUID | None, settings: Settings
) -> Member:
    """None -> the primary; another account's member -> 404 `member_not_found`; a non-primary
    member -> 422 `diary_member_not_enabled` while Family is off (Q9)."""
    if member_id is None:
        return await members_service.get_or_create_primary(session, account_id)
    member = await members_service.get_member(session, account_id, member_id)
    if not member.is_primary and not settings.diary_family_enabled:
        raise ApiError("diary_member_not_enabled", 422)
    return member


def body_data(member: Member, today: date, overrides: BodyDataIn | None = None) -> engine.BodyData:
    """The member's body data for the engine. Age is `youngest_age` (Ruling D2). A field the
    request SENT in ``overrides`` (even as null) replaces the stored one."""
    birth_year, sex = member.birth_year, member.sex
    height, weight, body_fat = member.height_cm, member.weight_kg, member.body_fat_pct
    if overrides is not None:
        sent = overrides.model_fields_set
        if "birth_year" in sent:
            birth_year = overrides.birth_year
        if "sex" in sent:
            sex = overrides.sex
        if "height_cm" in sent:
            height = overrides.height_cm
        if "weight_kg" in sent:
            weight = overrides.weight_kg
        if "body_fat_pct" in sent:
            body_fat = overrides.body_fat_pct
    return engine.BodyData(
        age=members_service.youngest_age(birth_year, today),
        sex=sex,  # type: ignore[arg-type]
        height_cm=_dec(height),
        weight_kg=_dec(weight),
        body_fat_pct=_dec(body_fat),
        goal=member.goal,
    )


def goal_settings(row: DiaryGoalSettings | GoalSettingsIn) -> engine.GoalSettings:
    return engine.GoalSettings(
        direction=row.direction,  # type: ignore[arg-type]
        activity_level=row.activity_level,  # type: ignore[arg-type]
        rate_pct_bw_per_week=_dec(row.rate_pct_bw_per_week),
        target_weight_kg=_dec(row.target_weight_kg),
        sex_reference=row.sex_reference,  # type: ignore[arg-type]
        pregnant_or_breastfeeding=bool(row.pregnant_or_breastfeeding),
        fat_pct_energy=_dec(row.fat_pct_energy),
    )


async def get_settings(session: AsyncSession, member: Member) -> DiaryGoalSettings | None:
    return await session.scalar(
        select(DiaryGoalSettings)
        .where(
            DiaryGoalSettings.member_id == member.id,
            DiaryGoalSettings.account_id == member.account_id,
        )
        .execution_options(populate_existing=True)
    )


def check_input(
    member: Member,
    body: GoalSettingsIn,
    settings: Settings,
    overrides: BodyDataIn | None = None,
    cfg: ScoringConfig | None = None,
) -> engine.BodyData:
    """The rules a save or preview must pass (422). Returns the body data it checked."""
    if body.energy_mode == "adaptive" and not settings.adaptive_tdee_enabled:
        raise ApiError("adaptive_not_enabled", 422)
    data = body_data(member, today_ist(), overrides)
    try:
        if overrides is not None and "body_fat_pct" in overrides.model_fields_set:
            engine.check_body_fat(data.body_fat_pct, cfg)
        engine.check_settings(data, goal_settings(body), cfg)
    except engine.SettingsRuleError as exc:
        raise settings_error(exc) from None
    return data


async def put_settings(
    session: AsyncSession, member: Member, body: GoalSettingsIn, settings: Settings
) -> DiaryGoalSettings:
    """Validate, then upsert the member's one row (never commits)."""
    check_input(member, body, settings)
    cfg = load_config()
    rate = _dec(body.rate_pct_bw_per_week)
    if body.direction == "maintain":
        rate = None
    elif rate is None:
        # Omitted means "the default": stored as that value, so a client can show the choice.
        rate = _dec(cfg.targets["goal_rates"][body.direction]["default_pct_bw_per_week"])
    values = {
        "direction": body.direction,
        "rate_pct_bw_per_week": rate,
        "target_weight_kg": _dec(body.target_weight_kg),
        "activity_level": body.activity_level,
        "sex_reference": body.sex_reference,
        "pregnant_or_breastfeeding": body.pregnant_or_breastfeeding,
        "fat_pct_energy": _dec(body.fat_pct_energy),
        "energy_mode": body.energy_mode,
        "numbers_display": body.numbers_display,
        "summary_view": body.summary_view,
    }
    stmt = insert(DiaryGoalSettings).values(
        member_id=member.id, account_id=member.account_id, **values
    )
    await session.execute(
        stmt.on_conflict_do_update(
            index_elements=[DiaryGoalSettings.member_id],
            set_={**values, "updated_at": func.now()},
        )
    )
    await session.flush()
    row = await get_settings(session, member)
    assert row is not None
    return row


async def put_display(session: AsyncSession, member: Member, body: DisplayIn) -> DiaryGoalSettings:
    """Change only `numbers_display` and `summary_view` (Ruling D4). Stored settings are not
    revalidated, so hiding numbers never fails (never commits)."""
    row = await get_settings(session, member)
    if row is None:
        raise ApiError("goal_settings_not_found", 404)
    if body.numbers_display is not None:
        row.numbers_display = body.numbers_display
    if body.summary_view is not None:
        row.summary_view = body.summary_view
    row.updated_at = func.now()
    await session.flush()
    await session.refresh(row)
    return row


async def delete_settings(session: AsyncSession, member: Member) -> None:
    """Erase the member's settings (idempotent; never commits)."""
    await session.execute(
        delete(DiaryGoalSettings).where(
            DiaryGoalSettings.member_id == member.id,
            DiaryGoalSettings.account_id == member.account_id,
        )
    )
    await session.flush()


async def targets_for_today(
    session: AsyncSession,
    member: Member,
    cfg: ScoringConfig | None = None,
    *,
    today: date | None = None,
) -> tuple[engine.TargetResult | None, DiaryGoalSettings | None]:
    """Today's targets computed live from the stored settings (None without settings). Stored
    settings that stopped validating are computed as the engine says (maintenance, minor,
    pregnancy), never as an error. The caller has checked `health_data` consent. ``today`` is
    the account's local today (the age is as of that date)."""
    row = await get_settings(session, member)
    if row is None:
        return None, None
    result = engine.compute(body_data(member, today or today_ist()), goal_settings(row), cfg)
    return result, row
