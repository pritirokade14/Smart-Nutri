"""Deletion tombstones (Plan 8, safety ruling D1/B1).

Revision ID: 0004_plan8_deleted_accounts
Revises: 0003_plan6_meal_logs_off
Create Date: 2026-11-04

`DELETE /v1/me` erases the account, but the caller's access token stays valid until it
expires. Without a record of the erasure, the next authenticated call would re-create the
`accounts` row (`ensure_account`). `deleted_accounts` holds one row per erased account id,
written in the same transaction as the erasure; `ensure_account` and the rate limiter refuse
those ids with 401 `auth_invalid`. The retention job purges tombstones after 7 days.

Server-only: no grant to anon or authenticated and no policy, so the Data API cannot read
or write it. ENABLE + FORCE row-level security like every other table.
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "0004_plan8_deleted_accounts"
down_revision: str | Sequence[str] | None = "0003_plan6_meal_logs_off"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "deleted_accounts",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column(
            "deleted_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.PrimaryKeyConstraint("id", name="pk_deleted_accounts"),
    )
    # Supabase default privileges grant ALL to anon/authenticated on new tables: revoke them.
    op.execute("REVOKE ALL ON deleted_accounts FROM PUBLIC, anon, authenticated")
    op.execute("GRANT ALL ON deleted_accounts TO service_role")
    op.execute("ALTER TABLE deleted_accounts ENABLE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE deleted_accounts FORCE ROW LEVEL SECURITY")
    # No policies: server-only (the API connects with a BYPASSRLS role).


def downgrade() -> None:
    op.drop_table("deleted_accounts")
