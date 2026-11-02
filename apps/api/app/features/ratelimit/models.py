import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import CheckConstraint, DateTime, Integer, Text, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class RateLimitCounter(Base):
    """Per-key request counters for fixed UTC windows. Server-only (no RLS policies)."""

    __tablename__ = "rate_limit_counters"

    key: Mapped[str] = mapped_column(Text, primary_key=True)
    bucket: Mapped[str] = mapped_column(Text, primary_key=True)
    window_start: Mapped[datetime] = mapped_column(DateTime(timezone=True), primary_key=True)
    count: Mapped[int] = mapped_column(Integer, server_default="0")


class ExplanationCache(Base):
    """Cached LLM explanations keyed by product and an anonymised profile hash. Server-only.

    ``product_id`` has no FK: products resolved from Open Food Facts have no ``products`` row.
    """

    __tablename__ = "explanation_cache"
    __table_args__ = (CheckConstraint("language in ('en', 'hi', 'mr')", name="language"),)

    product_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True)
    profile_hash: Mapped[str] = mapped_column(Text, primary_key=True)
    language: Mapped[str] = mapped_column(Text, primary_key=True)
    payload: Mapped[dict[str, Any]] = mapped_column(JSONB)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
