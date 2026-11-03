"""Tombstones record when the auth user was removed (final fix batch m2).

Revision ID: 0005_plan8_tombstone_auth
Revises: 0004_plan8_deleted_accounts
Create Date: 2026-11-04

`DELETE /v1/me` erases the rows (and writes the tombstone) before it removes the Supabase
auth user. If that last step fails, the sign-in can still mint access tokens, so the
tombstone must stay until the auth user is gone. `auth_deleted_at` is set when the removal
succeeds; the retention job retries the removal for tombstones without it and purges only
tombstones that have it.

Existing rows keep NULL (unknown): the job retries those, and the admin API counts an
already-removed user (404) as success. No new table, so grants and RLS are unchanged
(server-only, no policies).
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "0005_plan8_tombstone_auth"
down_revision: str | Sequence[str] | None = "0004_plan8_deleted_accounts"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "deleted_accounts",
        sa.Column("auth_deleted_at", sa.DateTime(timezone=True), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("deleted_accounts", "auth_deleted_at")
