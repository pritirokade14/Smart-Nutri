"""Meal slots (Plan 11 Task 1, migration 0009; spec 5.12). Member-scoped.

The four defaults are rows too, so every diary entry points at a slot id. Custom labels are
user text: never translated, never sent to analytics, logs or prompts.
"""

import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    DateTime,
    ForeignKey,
    ForeignKeyConstraint,
    Index,
    Integer,
    Text,
    UniqueConstraint,
    func,
    text,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class MealSlot(Base):
    __tablename__ = "meal_slots"
    __table_args__ = (
        ForeignKeyConstraint(
            ["member_id", "account_id"],
            ["members.id", "members.account_id"],
            name="fk_meal_slots_member_id_members",
            ondelete="CASCADE",
        ),
        UniqueConstraint("id", "member_id", name="uq_meal_slots_id_member_id"),
        UniqueConstraint("account_id", "client_id", name="uq_meal_slots_account_id_client_id"),
        CheckConstraint("label_key is not null or custom_label is not null", name="label_present"),
        CheckConstraint(
            "custom_label is null or char_length(custom_label) between 1 and 30",
            name="custom_label_length",
        ),
        CheckConstraint(
            "label_key is null or label_key in ('diary.slot.breakfast', 'diary.slot.lunch', "
            "'diary.slot.snack', 'diary.slot.dinner')",
            name="label_key",
        ),
        CheckConstraint('"position" >= 0', name="position"),
        Index(
            "uq_meal_slots_member_default",
            "member_id",
            "label_key",
            unique=True,
            postgresql_where=text("is_default"),
        ),
        Index(
            "uq_meal_slots_member_label",
            "member_id",
            text("lower(custom_label)"),
            unique=True,
            postgresql_where=text("archived_at IS NULL AND custom_label IS NOT NULL"),
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()")
    )
    account_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("accounts.id", ondelete="CASCADE"), index=True
    )
    member_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True))
    position: Mapped[int] = mapped_column(Integer)
    label_key: Mapped[str | None] = mapped_column(Text)
    custom_label: Mapped[str | None] = mapped_column(Text)
    default_time_window: Mapped[dict[str, Any] | None] = mapped_column(JSONB)
    is_default: Mapped[bool] = mapped_column(Boolean, server_default=text("false"))
    archived_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    client_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
