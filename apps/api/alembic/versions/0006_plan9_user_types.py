"""Account user types (Plan 9 Task 1, rulings P9-R1..R4).

Revision ID: 0006_plan9_user_types
Revises: 0005_plan8_tombstone_auth
Create Date: 2026-11-04

One row per account: the user types the account holder picked (up to 3, in tap order), the
follow-up answers, and the active focused mode. Kept out of `accounts` so the
health-revealing preference is not in the row every request loads (P9-R1).

A user type is presentation only: scoring, analyze, meals, alternatives, search, compare and
the prompts never read this table.

Privileges and RLS exactly like `members`: SELECT only for `authenticated` (filtered to the
caller's own row), ALL for `service_role`, nothing for anon. ENABLE + FORCE row-level security.
Erased by `DELETE /v1/me` (ACCOUNT_OWNED_TABLES) and by the FK cascade.
"""

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql as pg

from alembic import op

revision: str = "0006_plan9_user_types"
down_revision: str | Sequence[str] | None = "0005_plan8_tombstone_auth"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

OWNER = "account_id = (SELECT auth.uid())"


def upgrade() -> None:
    op.create_table(
        "account_user_types",
        sa.Column("account_id", pg.UUID(as_uuid=True), nullable=False),
        sa.Column(
            "types",
            pg.ARRAY(sa.Text()),
            nullable=False,
            server_default=sa.text("'{}'::text[]"),
        ),
        sa.Column(
            "follow_ups",
            pg.JSONB(),
            nullable=False,
            server_default=sa.text("'{}'::jsonb"),
        ),
        sa.Column("active_type", sa.Text(), nullable=True),
        sa.Column(
            "answered_at",
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
        sa.PrimaryKeyConstraint("account_id", name=op.f("pk_account_user_types")),
        sa.ForeignKeyConstraint(
            ["account_id"],
            ["accounts.id"],
            name=op.f("fk_account_user_types_account_id_accounts"),
            ondelete="CASCADE",
        ),
        sa.CheckConstraint(
            "cardinality(types) <= 3 and types <@ array['health_condition', 'family', "
            "'weight_loss', 'gym', 'allergy_diet', 'eat_better']::text[]",
            name=op.f("ck_account_user_types_user_types"),
        ),
        sa.CheckConstraint(
            "active_type is null or active_type = any(types)",
            name=op.f("ck_account_user_types_active_type"),
        ),
    )
    # Supabase default privileges grant ALL to anon/authenticated on new tables: tighten.
    op.execute("REVOKE ALL ON account_user_types FROM PUBLIC, anon, authenticated")
    op.execute("GRANT SELECT ON account_user_types TO authenticated")
    op.execute("GRANT ALL ON account_user_types TO service_role")
    op.execute("ALTER TABLE account_user_types ENABLE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE account_user_types FORCE ROW LEVEL SECURITY")
    op.execute(
        "CREATE POLICY account_user_types_owner ON account_user_types FOR ALL TO authenticated "
        f"USING ({OWNER}) WITH CHECK ({OWNER})"
    )


def downgrade() -> None:
    op.drop_table("account_user_types")  # drops its policy too
