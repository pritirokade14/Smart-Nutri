"""Household units, generic foods and per-food portions (Plan 12 Task 1, migration 0010).

`household_units` and `foods` are reference tables (readable by every signed-in user, written
by the service role). `food_portions` holds our grams per unit (global rows) and the account's
own overrides. Every value is PENDING DIETITIAN REVIEW (ADR 0024).
"""

import uuid
from datetime import datetime
from decimal import Decimal
from typing import Any

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
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

_NIL = "00000000-0000-0000-0000-000000000000"


class HouseholdUnit(Base):
    __tablename__ = "household_units"
    __table_args__ = (
        CheckConstraint(
            "(kind = 'mass' AND grams > 0 AND ml IS NULL) "
            "OR (kind = 'volume' AND ml > 0 AND grams IS NULL) "
            "OR (kind = 'count' AND ml IS NULL AND grams IS NULL)",
            name="kind_values",
        ),
        CheckConstraint("kind in ('mass', 'volume', 'count')", name="kind"),
    )

    code: Mapped[str] = mapped_column(Text, primary_key=True)
    kind: Mapped[str] = mapped_column(Text)
    ml: Mapped[Decimal | None] = mapped_column(Numeric(asdecimal=True))
    grams: Mapped[Decimal | None] = mapped_column(Numeric(asdecimal=True))
    sort: Mapped[int] = mapped_column(Integer)


class Food(Base):
    __tablename__ = "foods"
    __table_args__ = (
        UniqueConstraint("source", "source_code", name="uq_foods_source_source_code"),
        CheckConstraint("source in ('usda_fdc', 'smartnutri_recipe')", name="source"),
        CheckConstraint("basis in ('g', 'ml')", name="basis"),
        CheckConstraint("density_g_per_ml is null or density_g_per_ml > 0", name="density"),
        CheckConstraint("serving_g is null or serving_g > 0", name="serving_g"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()")
    )
    source: Mapped[str] = mapped_column(Text)
    source_code: Mapped[str] = mapped_column(Text)
    name_en: Mapped[str] = mapped_column(Text)
    name_hi: Mapped[str | None] = mapped_column(Text)
    name_mr: Mapped[str | None] = mapped_column(Text)
    aliases: Mapped[list[str]] = mapped_column(ARRAY(Text), server_default=text("'{}'::text[]"))
    search_text: Mapped[str] = mapped_column(Text)
    basis: Mapped[str] = mapped_column(Text)
    per_100: Mapped[dict[str, Any]] = mapped_column(JSONB)
    density_g_per_ml: Mapped[Decimal | None] = mapped_column(Numeric(asdecimal=True))
    density_source: Mapped[str | None] = mapped_column(Text)
    serving_g: Mapped[Decimal | None] = mapped_column(Numeric(asdecimal=True))
    recipe: Mapped[dict[str, Any] | None] = mapped_column(JSONB)
    licence: Mapped[str] = mapped_column(Text)
    data_version: Mapped[str] = mapped_column(Text)
    review_status: Mapped[str] = mapped_column(Text, server_default="pending_dietitian_review")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


def _unique_per_owner(name: str, ref: str) -> Index:
    return Index(
        name,
        text(f"coalesce(account_id, '{_NIL}'::uuid)"),
        ref,
        "unit",
        unique=True,
        postgresql_where=text(f"{ref} IS NOT NULL"),
    )


class FoodPortion(Base):
    __tablename__ = "food_portions"
    __table_args__ = (
        CheckConstraint("num_nonnulls(food_id, product_id, off_barcode) = 1", name="ref"),
        CheckConstraint("grams_per_unit > 0 and grams_per_unit <= 2000", name="grams"),
        CheckConstraint(
            "source in ('smartnutri_measured', 'reference_table', 'user', 'label')",
            name="source",
        ),
        CheckConstraint("(account_id IS NULL) = (source <> 'user')", name="owner"),
        _unique_per_owner("uq_food_portions_food", "food_id"),
        _unique_per_owner("uq_food_portions_product", "product_id"),
        _unique_per_owner("uq_food_portions_off", "off_barcode"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()")
    )
    account_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("accounts.id", ondelete="CASCADE"), index=True
    )
    food_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("foods.id", ondelete="CASCADE")
    )
    product_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("products.id", ondelete="CASCADE")
    )
    off_barcode: Mapped[str | None] = mapped_column(Text)
    unit: Mapped[str] = mapped_column(Text, ForeignKey("household_units.code"))
    grams_per_unit: Mapped[Decimal] = mapped_column(Numeric(asdecimal=True))
    source: Mapped[str] = mapped_column(Text)
    csv_key: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
