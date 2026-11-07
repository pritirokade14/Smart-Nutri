"""Weight logs: one manual weigh-in per member and local day (Plan 12 Task 21; spec 5.4, 5.11;
G26, Q4).

Revision ID: 0013_diary_weight_logs
Revises: 0012_diary_favourites
Create Date: 2026-11-07

- `weight_logs` is member-scoped (composite FK to `members(id, account_id)`, ON DELETE CASCADE),
  unique per `(member_id, local_date)`. `weight_kg` is 2 to 300. `source` is `manual` only
  (Q4: no device or import). `client_id` makes a retried offline write idempotent per account.
- Back-fill: one row per member whose `members.weight_kg` is within 2 to 300, dated by the
  member's `updated_at` in the account's time zone, so the profile and the log agree (G26).
  A weight outside the range (a legacy value) gets no row and stays on the member.

Privileges and RLS exactly like 0009 and 0012: owner-read for `authenticated`, written only by
the service role, ENABLE + FORCE RLS.

Downgrade drops the table: weigh-ins are lost; `members.weight_kg` keeps the latest.
"""

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql as pg

from alembic import op

revision: str = "0013_diary_weight_logs"
down_revision: str | Sequence[str] | None = "0012_diary_favourites"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

OWNER = "account_id = (SELECT auth.uid())"


def _lock_down(table: str) -> None:
    # Supabase default privileges grant ALL to anon/authenticated on new tables: tighten.
    op.execute(f"REVOKE ALL ON {table} FROM PUBLIC, anon, authenticated")
    op.execute(f"GRANT SELECT ON {table} TO authenticated")
    op.execute(f"GRANT ALL ON {table} TO service_role")
    op.execute(f"ALTER TABLE {table} ENABLE ROW LEVEL SECURITY")
    op.execute(f"ALTER TABLE {table} FORCE ROW LEVEL SECURITY")
    op.execute(
        f"CREATE POLICY {table}_owner ON {table} FOR ALL TO authenticated "
        f"USING ({OWNER}) WITH CHECK ({OWNER})"
    )


def upgrade() -> None:
    op.create_table(
        "weight_logs",
        sa.Column(
            "id",
            pg.UUID(as_uuid=True),
            nullable=False,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column("account_id", pg.UUID(as_uuid=True), nullable=False),
        sa.Column("member_id", pg.UUID(as_uuid=True), nullable=False),
        sa.Column("local_date", sa.Date(), nullable=False),
        sa.Column("weight_kg", sa.Numeric(), nullable=False),
        sa.Column("measured_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("source", sa.Text(), nullable=False, server_default=sa.text("'manual'")),
        sa.Column("client_id", pg.UUID(as_uuid=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_weight_logs")),
        sa.ForeignKeyConstraint(
            ["account_id"],
            ["accounts.id"],
            name=op.f("fk_weight_logs_account_id_accounts"),
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["member_id", "account_id"],
            ["members.id", "members.account_id"],
            name=op.f("fk_weight_logs_member_id_members"),
            ondelete="CASCADE",
        ),
        sa.UniqueConstraint("member_id", "local_date", name="uq_weight_logs_member_id_local_date"),
        sa.UniqueConstraint("account_id", "client_id", name="uq_weight_logs_account_id_client_id"),
        sa.CheckConstraint(
            "weight_kg >= 2 and weight_kg <= 300", name=op.f("ck_weight_logs_weight_kg")
        ),
        sa.CheckConstraint("source in ('manual')", name=op.f("ck_weight_logs_source")),
    )
    op.create_index(op.f("ix_weight_logs_account_id"), "weight_logs", ["account_id"])
    _lock_down("weight_logs")
    op.execute(
        """
        INSERT INTO weight_logs (account_id, member_id, local_date, weight_kg, measured_at, source)
        SELECT m.account_id, m.id, (m.updated_at AT TIME ZONE a.timezone)::date, m.weight_kg,
               m.updated_at, 'manual'
        FROM members m JOIN accounts a ON a.id = m.account_id
        WHERE m.weight_kg IS NOT NULL AND m.weight_kg >= 2 AND m.weight_kg <= 300
        """
    )


def downgrade() -> None:
    op.drop_table("weight_logs")
