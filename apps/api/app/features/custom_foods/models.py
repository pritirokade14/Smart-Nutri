"""Custom foods: a food the account typed from a label (Plan 12 Task 10, migration 0011; spec 5.8).

Account-owned. `per_100` uses the `Nutrients` field names (a value left blank is absent: never
0); `entered` keeps what was typed, so the edit form shows it back. Names and values are user
text and health-adjacent data: never sent to analytics, logs or prompts. A custom food is never
in the public catalogue and never reaches `analyze`.
"""

import uuid
from datetime import datetime
from decimal import Decimal
from typing import Any

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    ForeignKey,
    Numeric,
    Text,
    UniqueConstraint,
    func,
    text,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class CustomFood(Base):
    __tablename__ = "custom_foods"
    __table_args__ = (
        UniqueConstraint("account_id", "barcode", name="uq_custom_foods_account_id_barcode"),
        UniqueConstraint("account_id", "client_id", name="uq_custom_foods_account_id_client_id"),
        CheckConstraint("char_length(name) between 1 and 80", name="name"),
        CheckConstraint("brand is null or char_length(brand) between 1 and 80", name="brand"),
        CheckConstraint("basis in ('g', 'ml')", name="basis"),
        CheckConstraint("serving_g is null or serving_g > 0", name="serving_g"),
        CheckConstraint(
            "density_g_per_ml is null or (density_g_per_ml >= 0.2 and density_g_per_ml <= 2.0)",
            name="density",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()")
    )
    account_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("accounts.id", ondelete="CASCADE"), index=True
    )
    name: Mapped[str] = mapped_column(Text)
    brand: Mapped[str | None] = mapped_column(Text)
    basis: Mapped[str] = mapped_column(Text)
    per_100: Mapped[dict[str, Any]] = mapped_column(JSONB)
    entered: Mapped[dict[str, Any]] = mapped_column(JSONB)
    serving_g: Mapped[Decimal | None] = mapped_column(Numeric(asdecimal=True))
    density_g_per_ml: Mapped[Decimal | None] = mapped_column(Numeric(asdecimal=True))
    barcode: Mapped[str | None] = mapped_column(Text)
    client_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
