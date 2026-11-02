import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import CheckConstraint, DateTime, Double, ForeignKey, Text, func, text
from sqlalchemy.dialects.postgresql import ARRAY, JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base

CATEGORIES = ("general", "beverage", "water", "cheese", "fat")
SOURCES = ("label", "user")
VERIFICATION_STATUSES = ("pending", "verified", "rejected")
VEG_MARKS = ("veg", "non_veg")


class Product(Base):
    """SmartNutri's own catalogue (label scans and user entries). Never holds OFF data."""

    __tablename__ = "products"
    __table_args__ = (
        CheckConstraint(
            "category in ('general', 'beverage', 'water', 'cheese', 'fat')", name="category"
        ),
        CheckConstraint("source in ('label', 'user')", name="source"),
        CheckConstraint(
            "verification_status in ('pending', 'verified', 'rejected')",
            name="verification_status",
        ),
        CheckConstraint("veg_mark in ('veg', 'non_veg')", name="veg_mark"),
        CheckConstraint(
            "extraction_confidence >= 0 and extraction_confidence <= 1",
            name="extraction_confidence",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()")
    )
    barcode: Mapped[str | None] = mapped_column(Text, unique=True)
    name: Mapped[str] = mapped_column(Text)
    brand: Mapped[str | None] = mapped_column(Text)
    category: Mapped[str] = mapped_column(Text, server_default="general")
    per_100g: Mapped[dict[str, Any]] = mapped_column(JSONB, server_default="{}")
    serving_size_g: Mapped[float | None] = mapped_column(Double)
    ingredients_text: Mapped[str | None] = mapped_column(Text)
    allergen_statement: Mapped[str | None] = mapped_column(Text)
    may_contain_statement: Mapped[str | None] = mapped_column(Text)
    claims: Mapped[list[str]] = mapped_column(ARRAY(Text), server_default="{}")
    veg_mark: Mapped[str | None] = mapped_column(Text)
    source: Mapped[str] = mapped_column(Text)
    extraction_confidence: Mapped[float | None] = mapped_column(Double)
    verification_status: Mapped[str] = mapped_column(Text, server_default="pending")
    created_by: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("accounts.id", ondelete="SET NULL")
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class OffProductCache(Base):
    """Open Food Facts payloads (ODbL), kept apart from ``products``. Server-only."""

    __tablename__ = "off_product_cache"

    barcode: Mapped[str] = mapped_column(Text, primary_key=True)
    payload: Mapped[dict[str, Any]] = mapped_column(JSONB)
    fetched_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
