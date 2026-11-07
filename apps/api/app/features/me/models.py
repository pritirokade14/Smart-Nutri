import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, Text, func, text
from sqlalchemy.dialects.postgresql import ARRAY, JSONB, UUID
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
    # IANA zone for local diary dates (Plan 11 Ruling E7). Validated by the API, not the DB.
    timezone: Mapped[str] = mapped_column(Text, server_default="Asia/Kolkata")
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


class AccountUserTypes(Base):
    """The account holder's user types (Plan 9, P9-R1..R4, migration 0006). One row per
    account; no row means "not asked yet".

    Presentation only: scoring, analyze, meals and the prompts never read it. `types` is the
    tap order (at most 3). `active_type` is null or one of `types`; the API resolves null to
    the highest-priority chosen type, or `eat_better`.
    """

    __tablename__ = "account_user_types"
    __table_args__ = (
        CheckConstraint(
            "cardinality(types) <= 3 and types <@ array['health_condition', 'family', "
            "'weight_loss', 'gym', 'allergy_diet', 'eat_better']::text[]",
            name="user_types",
        ),
        CheckConstraint("active_type is null or active_type = any(types)", name="active_type"),
    )

    account_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("accounts.id", ondelete="CASCADE"), primary_key=True
    )
    types: Mapped[list[str]] = mapped_column(ARRAY(Text), server_default=text("'{}'::text[]"))
    follow_ups: Mapped[dict[str, Any]] = mapped_column(JSONB, server_default=text("'{}'::jsonb"))
    active_type: Mapped[str | None] = mapped_column(Text)
    answered_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
