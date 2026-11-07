"""Favourites: a member's starred foods and saved meals (Plan 12 Task 17, migration 0012).

A food favourite points at one food (kept with a name snapshot and an optional default
portion). A meal favourite has no reference: it keeps the entries of one slot and day as they
were (`items`), so logging it again never reads the foods afresh (the copy rules). The meal
name is user text: stored exactly as typed, never sent to analytics, logs or prompts.
"""

import uuid
from datetime import datetime
from decimal import Decimal
from typing import Any

from sqlalchemy import (
    CheckConstraint,
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
from sqlalchemy.dialects.postgresql import ARRAY, JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.features.custom_foods import models as _custom_foods_models  # noqa: F401  (FK targets)
from app.features.foods import models as _foods_models  # noqa: F401  (FK targets)
from app.features.recipes import models as _recipes_models  # noqa: F401  (FK targets)

MAX_FAVOURITES = 200
REFS = ("product_id", "off_barcode", "food_id", "custom_food_id", "recipe_id")


class Favourite(Base):
    __tablename__ = "favourites"
    __table_args__ = (
        ForeignKeyConstraint(
            ["member_id", "account_id"],
            ["members.id", "members.account_id"],
            name="fk_favourites_member_id_members",
            ondelete="CASCADE",
        ),
        UniqueConstraint("account_id", "client_id", name="uq_favourites_account_id_client_id"),
        CheckConstraint("kind in ('food', 'meal')", name="kind"),
        CheckConstraint(
            "source_kind is null or source_kind in "
            "('product', 'off', 'food', 'custom_food', 'recipe')",
            name="source_kind",
        ),
        CheckConstraint(
            "(kind = 'food' AND items IS NULL AND source_kind IS NOT NULL "
            "AND num_nonnulls(product_id, off_barcode, food_id, custom_food_id, recipe_id) = 1 "
            "AND ((source_kind = 'product' AND product_id IS NOT NULL) "
            "OR (source_kind = 'off' AND off_barcode IS NOT NULL) "
            "OR (source_kind = 'food' AND food_id IS NOT NULL) "
            "OR (source_kind = 'custom_food' AND custom_food_id IS NOT NULL) "
            "OR (source_kind = 'recipe' AND recipe_id IS NOT NULL))) "
            "OR (kind = 'meal' AND items IS NOT NULL AND source_kind IS NULL "
            "AND num_nonnulls(product_id, off_barcode, food_id, custom_food_id, recipe_id) = 0 "
            "AND default_quantity IS NULL AND default_unit IS NULL)",
            name="shape",
        ),
        CheckConstraint("char_length(name) between 1 and 200", name="name"),
        CheckConstraint(
            "default_quantity is null or (default_quantity > 0 and default_quantity <= 5000)",
            name="default_quantity",
        ),
        CheckConstraint(
            "num_nonnulls(default_quantity, default_unit) in (0, 2)", name="default_portion"
        ),
        Index("ix_favourites_member_id_created_at", "member_id", "created_at"),
        *(
            Index(
                f"uq_favourites_member_id_{ref}",
                "member_id",
                ref,
                unique=True,
                postgresql_where=text(f"{ref} IS NOT NULL"),
            )
            for ref in REFS
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()")
    )
    account_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("accounts.id", ondelete="CASCADE"), index=True
    )
    member_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True))
    kind: Mapped[str] = mapped_column(Text)
    source_kind: Mapped[str | None] = mapped_column(Text)
    product_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("products.id")
    )
    off_barcode: Mapped[str | None] = mapped_column(Text)
    food_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("foods.id"))
    custom_food_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("custom_foods.id", ondelete="CASCADE")
    )
    recipe_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("recipes.id", ondelete="CASCADE")
    )
    name: Mapped[str] = mapped_column(Text)
    default_quantity: Mapped[Decimal | None] = mapped_column(Numeric(asdecimal=True))
    default_unit: Mapped[str | None] = mapped_column(Text, ForeignKey("household_units.code"))
    items: Mapped[list[dict[str, Any]] | None] = mapped_column(JSONB)
    attributions: Mapped[list[str]] = mapped_column(
        ARRAY(Text), server_default=text("'{}'::text[]")
    )
    client_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
