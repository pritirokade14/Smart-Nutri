"""Weight log: one manual weigh-in per member and local day (Plan 12 Task 21, migration 0013).

`weight_kg` is health data. It never goes to logs, analytics or prompts. The trend and the
projection are computed from these rows (`app.scoring.weight_trend`), never stored.
"""

import uuid
from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import (
    CheckConstraint,
    Date,
    DateTime,
    ForeignKey,
    ForeignKeyConstraint,
    Numeric,
    Text,
    UniqueConstraint,
    func,
    text,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class WeightLog(Base):
    __tablename__ = "weight_logs"
    __table_args__ = (
        ForeignKeyConstraint(
            ["member_id", "account_id"],
            ["members.id", "members.account_id"],
            name="fk_weight_logs_member_id_members",
            ondelete="CASCADE",
        ),
        UniqueConstraint("member_id", "local_date", name="uq_weight_logs_member_id_local_date"),
        UniqueConstraint("account_id", "client_id", name="uq_weight_logs_account_id_client_id"),
        CheckConstraint("weight_kg >= 2 and weight_kg <= 300", name="weight_kg"),
        CheckConstraint("source in ('manual')", name="source"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()")
    )
    account_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("accounts.id", ondelete="CASCADE"), index=True
    )
    member_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True))
    local_date: Mapped[date] = mapped_column(Date)
    weight_kg: Mapped[Decimal] = mapped_column(Numeric(asdecimal=True))
    measured_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    source: Mapped[str] = mapped_column(Text, server_default=text("'manual'"))
    client_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
