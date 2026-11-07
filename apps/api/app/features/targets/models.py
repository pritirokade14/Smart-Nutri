"""Daily-guide settings (Plan 10 Task 3, migration 0008). One row per member.

Health data: the direction, the pregnancy answer and the target weight. Targets are
information, never verdicts: scoring, analyze and the prompts never read this table.
"""

import uuid
from datetime import datetime
from decimal import Decimal

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    DateTime,
    ForeignKey,
    ForeignKeyConstraint,
    Numeric,
    Text,
    func,
    text,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class DiaryGoalSettings(Base):
    __tablename__ = "diary_goal_settings"
    __table_args__ = (
        ForeignKeyConstraint(
            ["member_id", "account_id"],
            ["members.id", "members.account_id"],
            ondelete="CASCADE",
        ),
        CheckConstraint("direction in ('lose', 'maintain', 'gain')", name="direction"),
        CheckConstraint(
            "activity_level in ('sedentary', 'light', 'moderate', 'very')", name="activity_level"
        ),
        CheckConstraint(
            "sex_reference is null or sex_reference in ('male', 'female', 'average')",
            name="sex_reference",
        ),
        CheckConstraint(
            "target_weight_kg is null or (target_weight_kg >= 2 and target_weight_kg <= 300)",
            name="target_weight_kg",
        ),
        CheckConstraint("energy_mode in ('formula', 'adaptive')", name="energy_mode"),
        CheckConstraint(
            "numbers_display in ('show', 'hide_energy', 'hide_all')", name="numbers_display"
        ),
        CheckConstraint("summary_view in ('remaining', 'consumed')", name="summary_view"),
    )

    member_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True)
    account_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("accounts.id", ondelete="CASCADE"), index=True
    )
    direction: Mapped[str] = mapped_column(Text)
    rate_pct_bw_per_week: Mapped[Decimal | None] = mapped_column(Numeric(asdecimal=True))
    target_weight_kg: Mapped[Decimal | None] = mapped_column(Numeric(asdecimal=True))
    activity_level: Mapped[str] = mapped_column(Text)
    sex_reference: Mapped[str | None] = mapped_column(Text)
    pregnant_or_breastfeeding: Mapped[bool] = mapped_column(Boolean, server_default=text("false"))
    fat_pct_energy: Mapped[Decimal | None] = mapped_column(Numeric(asdecimal=True))
    energy_mode: Mapped[str] = mapped_column(Text, server_default="formula")
    numbers_display: Mapped[str] = mapped_column(Text, server_default="show")
    summary_view: Mapped[str] = mapped_column(Text, server_default="remaining")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
