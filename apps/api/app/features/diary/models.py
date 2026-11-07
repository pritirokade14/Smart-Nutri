"""Frozen daily targets and day status (Plan 11 Task 1, migration 0009; spec 5.3; ADR 0023).

One row per member and local day. Today's row is recomputed on read; a past row is never
recomputed (only `partial_logged` changes). Health data: the targets come from body data.
Targets are information, never verdicts: scoring and analyze never read this table.
"""

import uuid
from datetime import date, datetime
from decimal import Decimal
from typing import Any

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Date,
    DateTime,
    ForeignKey,
    ForeignKeyConstraint,
    Numeric,
    Text,
    func,
    text,
)
from sqlalchemy.dialects.postgresql import ARRAY, JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class DiaryDay(Base):
    __tablename__ = "diary_days"
    __table_args__ = (
        ForeignKeyConstraint(
            ["member_id", "account_id"],
            ["members.id", "members.account_id"],
            name="fk_diary_days_member_id_members",
            ondelete="CASCADE",
        ),
        CheckConstraint(
            "status in ('ready', 'needs_body_data', 'not_available_minor', "
            "'paused_pregnancy', 'none')",
            name="status",
        ),
        CheckConstraint("basis is null or basis in ('formula', 'adaptive')", name="basis"),
        CheckConstraint(
            "direction is null or direction in ('lose', 'maintain', 'gain')", name="direction"
        ),
    )

    member_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True)
    local_date: Mapped[date] = mapped_column(Date, primary_key=True)
    account_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("accounts.id", ondelete="CASCADE"), index=True
    )
    status: Mapped[str] = mapped_column(Text)
    energy_kcal: Mapped[Decimal | None] = mapped_column(Numeric(asdecimal=True))
    protein_g: Mapped[Decimal | None] = mapped_column(Numeric(asdecimal=True))
    fat_g: Mapped[Decimal | None] = mapped_column(Numeric(asdecimal=True))
    carbs_g: Mapped[Decimal | None] = mapped_column(Numeric(asdecimal=True))
    basis: Mapped[str | None] = mapped_column(Text)
    direction: Mapped[str | None] = mapped_column(Text)
    rate_pct_bw_per_week: Mapped[Decimal | None] = mapped_column(Numeric(asdecimal=True))
    inputs: Mapped[dict[str, Any]] = mapped_column(JSONB, server_default=text("'{}'::jsonb"))
    flags: Mapped[list[str]] = mapped_column(ARRAY(Text), server_default=text("'{}'::text[]"))
    partial_logged: Mapped[bool] = mapped_column(Boolean, server_default=text("false"))
    computed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
