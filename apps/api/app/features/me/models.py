import uuid
from datetime import datetime

from sqlalchemy import CheckConstraint, DateTime, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base

LANGUAGES = ("en", "hi", "mr")


class Account(Base):
    """One row per Supabase auth user; ``id`` equals ``auth.users.id``.

    There is no FK to ``auth.users`` so the schema also runs on vanilla Postgres in tests.
    """

    __tablename__ = "accounts"
    __table_args__ = (CheckConstraint("language in ('en', 'hi', 'mr')", name="language"),)

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True)
    display_name: Mapped[str | None] = mapped_column(Text)
    language: Mapped[str] = mapped_column(Text, server_default="en")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class DeletedAccount(Base):
    """Tombstone of an erased account (ruling D1/B1, migration 0004).

    Written in the erasure transaction of `DELETE /v1/me`. While it exists, a still-valid
    access token for this id gets 401 `auth_invalid` and never re-creates the account.
    Server-only (no client grant). The retention job purges it after 7 days, and only once
    `auth_deleted_at` is set (m2, migration 0005): until the Supabase auth user is removed,
    the sign-in could still mint tokens. NULL means not confirmed; the job retries.
    """

    __tablename__ = "deleted_accounts"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True)
    deleted_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    auth_deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
