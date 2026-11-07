"""Recipes and their ingredients (Plan 12 Task 10, migration 0011; spec 5.9; G19-G22).

`per_100g` is the sum of the KNOWN parts per 100 g of the basis weight (unrounded);
`incomplete_nutrients` names every nutrient at least one ingredient does not know, so the
screen can say "at least". A nutrient no ingredient knows is null, never 0. Each ingredient
keeps a snapshot of its own per-100 values, so a recipe never changes when a food does.
"""

import uuid
from datetime import datetime
from decimal import Decimal
from typing import Any

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    ForeignKey,
    Integer,
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


class Recipe(Base):
    __tablename__ = "recipes"
    __table_args__ = (
        UniqueConstraint("account_id", "client_id", name="uq_recipes_account_id_client_id"),
        CheckConstraint("char_length(name) between 1 and 80", name="name"),
        CheckConstraint("servings is null or (servings > 0 and servings <= 100)", name="servings"),
        CheckConstraint(
            "cooked_weight_g is null or (cooked_weight_g > 0 and cooked_weight_g <= 20000)",
            name="cooked_weight_g",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()")
    )
    account_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("accounts.id", ondelete="CASCADE"), index=True
    )
    name: Mapped[str] = mapped_column(Text)
    servings: Mapped[Decimal | None] = mapped_column(Numeric(asdecimal=True))
    cooked_weight_g: Mapped[Decimal | None] = mapped_column(Numeric(asdecimal=True))
    total_raw_g: Mapped[Decimal | None] = mapped_column(Numeric(asdecimal=True))
    per_100g: Mapped[dict[str, Any]] = mapped_column(JSONB)
    incomplete_nutrients: Mapped[list[str]] = mapped_column(
        ARRAY(Text), server_default=text("'{}'::text[]")
    )
    client_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class RecipeIngredient(Base):
    __tablename__ = "recipe_ingredients"
    __table_args__ = (
        UniqueConstraint("recipe_id", "position", name="uq_recipe_ingredients_recipe_id_position"),
        CheckConstraint(
            "source_kind in ('product', 'off', 'food', 'custom_food')", name="source_kind"
        ),
        CheckConstraint(
            "(source_kind = 'product' AND product_id IS NOT NULL AND off_barcode IS NULL "
            "AND food_id IS NULL AND custom_food_id IS NULL) "
            "OR (source_kind = 'off' AND off_barcode IS NOT NULL AND product_id IS NULL "
            "AND food_id IS NULL AND custom_food_id IS NULL) "
            "OR (source_kind = 'food' AND food_id IS NOT NULL AND product_id IS NULL "
            "AND off_barcode IS NULL AND custom_food_id IS NULL) "
            "OR (source_kind = 'custom_food' AND product_id IS NULL AND off_barcode IS NULL "
            "AND food_id IS NULL)",
            name="ref",
        ),
        CheckConstraint('"position" >= 0', name="position"),
        CheckConstraint("quantity > 0", name="quantity"),
        CheckConstraint("grams > 0 and grams <= 5000", name="grams"),
        CheckConstraint("basis in ('g', 'ml')", name="basis"),
        CheckConstraint("weight_g is null or weight_g > 0", name="weight_g"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()")
    )
    recipe_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("recipes.id", ondelete="CASCADE")
    )
    account_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("accounts.id", ondelete="CASCADE"), index=True
    )
    position: Mapped[int] = mapped_column(Integer)
    source_kind: Mapped[str] = mapped_column(Text)
    product_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("products.id")
    )
    off_barcode: Mapped[str | None] = mapped_column(Text)
    food_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("foods.id"))
    custom_food_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("custom_foods.id", ondelete="SET NULL")
    )
    name: Mapped[str] = mapped_column(Text)
    quantity: Mapped[Decimal] = mapped_column(Numeric(asdecimal=True))
    unit: Mapped[str] = mapped_column(Text, ForeignKey("household_units.code"))
    grams: Mapped[Decimal] = mapped_column(Numeric(asdecimal=True))
    basis: Mapped[str] = mapped_column(Text)
    weight_g: Mapped[Decimal | None] = mapped_column(Numeric(asdecimal=True))
    per_100: Mapped[dict[str, Any]] = mapped_column(JSONB)
    attribution: Mapped[str | None] = mapped_column(Text)
