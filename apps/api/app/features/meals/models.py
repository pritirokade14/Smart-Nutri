import uuid
from datetime import date, datetime
from decimal import Decimal
from typing import Any

from sqlalchemy import (
    CheckConstraint,
    Date,
    DateTime,
    ForeignKey,
    ForeignKeyConstraint,
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
from app.features.custom_foods import models as _custom_foods_models  # noqa: F401  (FK targets)
from app.features.foods import models as _foods_models  # noqa: F401  (FK targets)
from app.features.recipes import models as _recipes_models  # noqa: F401  (FK targets)


class MealLog(Base):
    """What a member ate. ``nutrients``, ``product_name`` and ``grade`` are snapshots taken at
    log time; later product edits never rewrite history.

    Plan 11 widens it to the diary entry (migration 0009): see the columns below.

    ``account_id`` (for RLS) and ``client_id`` (offline idempotency) are additions to
    spec §4 (CROSS-PLAN-NOTES item 3). A log references either our own product
    (``product_id``) or an Open Food Facts barcode (``off_barcode``), exactly one
    (CROSS-PLAN-NOTES item 11, ADR 0017; migration 0003_plan6_meal_logs_off).
    """

    __tablename__ = "meal_logs"
    __table_args__ = (
        CheckConstraint("grams is null or (grams > 0 and grams <= 5000)", name="grams"),
        CheckConstraint(
            "(source_kind = 'product' AND product_id IS NOT NULL AND off_barcode IS NULL "
            "AND food_id IS NULL AND custom_food_id IS NULL AND recipe_id IS NULL "
            "AND grams IS NOT NULL) "
            "OR (source_kind = 'off' AND off_barcode IS NOT NULL AND product_id IS NULL "
            "AND food_id IS NULL AND custom_food_id IS NULL AND recipe_id IS NULL "
            "AND grams IS NOT NULL) "
            "OR (source_kind = 'food' AND food_id IS NOT NULL AND product_id IS NULL "
            "AND off_barcode IS NULL AND custom_food_id IS NULL AND recipe_id IS NULL "
            "AND grams IS NOT NULL) "
            "OR (source_kind = 'quick_add' AND product_id IS NULL AND off_barcode IS NULL "
            "AND food_id IS NULL AND custom_food_id IS NULL AND recipe_id IS NULL "
            "AND grams IS NULL) "
            "OR (source_kind IN ('custom_food', 'recipe') AND product_id IS NULL "
            "AND off_barcode IS NULL AND food_id IS NULL AND grams IS NOT NULL "
            "AND num_nonnulls(custom_food_id, recipe_id) <= 1 "
            "AND (source_kind = 'custom_food' OR custom_food_id IS NULL) "
            "AND (source_kind = 'recipe' OR recipe_id IS NULL))",
            name="ref",
        ),
        CheckConstraint("quantity is null or (quantity > 0 and quantity <= 5000)", name="quantity"),
        CheckConstraint("num_nonnulls(quantity, unit) in (0, 2)", name="quantity_unit"),
        CheckConstraint(
            "source_kind in ('product', 'off', 'food', 'custom_food', 'recipe', 'quick_add')",
            name="source_kind",
        ),
        ForeignKeyConstraint(
            ["meal_slot_id", "member_id"],
            ["meal_slots.id", "meal_slots.member_id"],
            name="fk_meal_logs_meal_slot_id_meal_slots",
        ),
        CheckConstraint("grade in ('A', 'B', 'C', 'D', 'E')", name="grade"),
        UniqueConstraint("account_id", "client_id", name="uq_meal_logs_account_id_client_id"),
        Index("ix_meal_logs_member_id_eaten_at", "member_id", text("eaten_at DESC")),
        Index("ix_meal_logs_member_id_local_date", "member_id", "local_date", "meal_slot_id"),
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
    grams: Mapped[float | None] = mapped_column(Numeric(asdecimal=False))
    eaten_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    nutrients: Mapped[dict[str, Any]] = mapped_column(JSONB)
    client_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    # Plan 11 (migration 0009): the entry's local day, its meal slot, how it was entered, the
    # food as it was at log time, and the last edit.
    local_date: Mapped[date] = mapped_column(Date)
    meal_slot_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True))
    source_kind: Mapped[str] = mapped_column(Text, server_default="product")
    food_snapshot: Mapped[dict[str, Any] | None] = mapped_column(JSONB)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    # Plan 12 (migration 0010): a generic food or dish, and the portion as typed
    # (``quantity`` x ``unit``). Legacy rows keep quantity and unit NULL.
    food_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("foods.id"))
    quantity: Mapped[Decimal | None] = mapped_column(Numeric(asdecimal=True))
    unit: Mapped[str | None] = mapped_column(Text, ForeignKey("household_units.code"))
    # Plan 12 slice 4 (migration 0011): a custom food or recipe. NULL once it was deleted: the
    # entry keeps its name and values in `food_snapshot`.
    custom_food_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("custom_foods.id", ondelete="SET NULL")
    )
    recipe_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("recipes.id", ondelete="SET NULL")
    )
