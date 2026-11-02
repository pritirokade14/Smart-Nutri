import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    Numeric,
    UniqueConstraint,
    func,
    text,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class MealLog(Base):
    """What a member ate. ``nutrients`` is a snapshot taken at log time.

    ``account_id`` (for RLS) and ``client_id`` (offline idempotency) are additions to
    spec §4 (CROSS-PLAN-NOTES item 3).
    """

    __tablename__ = "meal_logs"
    __table_args__ = (
        CheckConstraint("grams > 0 and grams <= 5000", name="grams"),
        UniqueConstraint("account_id", "client_id", name="uq_meal_logs_account_id_client_id"),
        Index("ix_meal_logs_member_id_eaten_at", "member_id", text("eaten_at DESC")),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()")
    )
    account_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("accounts.id", ondelete="CASCADE")
    )
    member_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("members.id", ondelete="CASCADE")
    )
    product_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("products.id"))
    grams: Mapped[float] = mapped_column(Numeric(asdecimal=False))
    eaten_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    nutrients: Mapped[dict[str, Any]] = mapped_column(JSONB)
    client_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
