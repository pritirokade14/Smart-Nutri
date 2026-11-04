import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    Numeric,
    Text,
    UniqueConstraint,
    func,
    text,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class MealLog(Base):
    """What a member ate. ``nutrients``, ``product_name`` and ``grade`` are snapshots taken at
    log time; later product edits never rewrite history.

    ``account_id`` (for RLS) and ``client_id`` (offline idempotency) are additions to
    spec §4 (CROSS-PLAN-NOTES item 3). A log references either our own product
    (``product_id``) or an Open Food Facts barcode (``off_barcode``), exactly one
    (CROSS-PLAN-NOTES item 11, ADR 0017; migration 0003_plan6_meal_logs_off).
    """

    __tablename__ = "meal_logs"
    __table_args__ = (
        CheckConstraint("grams > 0 and grams <= 5000", name="grams"),
        CheckConstraint("num_nonnulls(product_id, off_barcode) = 1", name="product_ref"),
        CheckConstraint("grade in ('A', 'B', 'C', 'D', 'E')", name="grade"),
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
    product_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("products.id")
    )
    off_barcode: Mapped[str | None] = mapped_column(Text)
    product_name: Mapped[str | None] = mapped_column(Text)
    grade: Mapped[str | None] = mapped_column(Text)
    grams: Mapped[float] = mapped_column(Numeric(asdecimal=False))
    eaten_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    nutrients: Mapped[dict[str, Any]] = mapped_column(JSONB)
    client_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
