"""The weight the daily guides use (Plan 12 Task 23, G25).

With at least `trend.min_weigh_ins_for_trend` non-outlier weigh-ins up to the date, the trend
weight on that date; otherwise the member's stored weight. It returns where the number came
from, so the explanation can say so. Imports only the store, so `targets` can use it.
"""

from datetime import date
from decimal import Decimal
from typing import Literal

from sqlalchemy.ext.asyncio import AsyncSession

from app.features.members.models import Member
from app.features.weights import store
from app.scoring import weight_trend
from app.scoring.config import ScoringConfig


async def weight_in_use(
    session: AsyncSession, member: Member, day: date, cfg: ScoringConfig | None = None
) -> tuple[Decimal | None, Literal["trend", "latest"] | None]:
    rows = await store.list_weigh_ins(session, member, until=day)
    trend = weight_trend.weight_for_targets(
        [weight_trend.WeighIn(r.local_date, Decimal(r.weight_kg)) for r in rows], day, cfg
    )
    if trend is not None:
        return trend, "trend"
    if member.weight_kg is None:
        return None, None
    return Decimal(str(member.weight_kg)), "latest"
