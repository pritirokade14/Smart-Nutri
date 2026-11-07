"""Daily-guide settings and `members.body_fat_pct` (Plan 10 Task 3; Ruling D1).

Revision ID: 0008_diary_goal_settings
Revises: 0007_plan9_supplement_category
Create Date: 2026-11-07

- `members.body_fat_pct` (numeric, NULL = unknown, never 0): an optional, user-entered health
  field, 3 to 70 (a backstop for the API check, which reads the same limits from targets.yaml).
- `uq_members_id_account_id (id, account_id)` on `members`, the target of composite FKs, so a
  member-scoped row can never carry another account's id.
- `diary_goal_settings`: one row per member (spec 5.2). Health data (direction, pregnancy
  answer, target weight). `diary_days` and `accounts.timezone` are slice 2 (Ruling D1).

Privileges and RLS exactly like `0006_plan9_user_types`: SELECT only for `authenticated`
(filtered to the caller's own rows), ALL for `service_role`, nothing for anon. ENABLE + FORCE
row-level security. Erased by `DELETE /v1/me` (ACCOUNT_OWNED_TABLES, before `members`) and by
the FK cascades.
"""

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql as pg

from alembic import op

revision: str = "0008_diary_goal_settings"
down_revision: str | Sequence[str] | None = "0007_plan9_supplement_category"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

OWNER = "account_id = (SELECT auth.uid())"
TABLE = "diary_goal_settings"


def upgrade() -> None:
    op.add_column("members", sa.Column("body_fat_pct", sa.Numeric(), nullable=True))
    op.create_check_constraint(
        op.f("ck_members_body_fat_pct"),
        "members",
        "body_fat_pct is null or (body_fat_pct >= 3 and body_fat_pct <= 70)",
    )
    op.create_unique_constraint("uq_members_id_account_id", "members", ["id", "account_id"])

    op.create_table(
        TABLE,
        sa.Column("member_id", pg.UUID(as_uuid=True), nullable=False),
        sa.Column("account_id", pg.UUID(as_uuid=True), nullable=False),
        sa.Column("direction", sa.Text(), nullable=False),
        sa.Column("rate_pct_bw_per_week", sa.Numeric(), nullable=True),
        sa.Column("target_weight_kg", sa.Numeric(), nullable=True),
        sa.Column("activity_level", sa.Text(), nullable=False),
        sa.Column("sex_reference", sa.Text(), nullable=True),
        sa.Column(
            "pregnant_or_breastfeeding",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("false"),
        ),
        sa.Column("fat_pct_energy", sa.Numeric(), nullable=True),
        sa.Column("energy_mode", sa.Text(), nullable=False, server_default="formula"),
        sa.Column("numbers_display", sa.Text(), nullable=False, server_default="show"),
        sa.Column("summary_view", sa.Text(), nullable=False, server_default="remaining"),
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
        sa.PrimaryKeyConstraint("member_id", name=op.f(f"pk_{TABLE}")),
        sa.ForeignKeyConstraint(
            ["account_id"],
            ["accounts.id"],
            name=op.f(f"fk_{TABLE}_account_id_accounts"),
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["member_id", "account_id"],
            ["members.id", "members.account_id"],
            name=op.f(f"fk_{TABLE}_member_id_members"),
            ondelete="CASCADE",
        ),
        sa.CheckConstraint(
            "direction in ('lose', 'maintain', 'gain')", name=op.f(f"ck_{TABLE}_direction")
        ),
        sa.CheckConstraint(
            "activity_level in ('sedentary', 'light', 'moderate', 'very')",
            name=op.f(f"ck_{TABLE}_activity_level"),
        ),
        sa.CheckConstraint(
            "sex_reference is null or sex_reference in ('male', 'female', 'average')",
            name=op.f(f"ck_{TABLE}_sex_reference"),
        ),
        sa.CheckConstraint(
            "target_weight_kg is null or (target_weight_kg >= 2 and target_weight_kg <= 300)",
            name=op.f(f"ck_{TABLE}_target_weight_kg"),
        ),
        sa.CheckConstraint(
            "energy_mode in ('formula', 'adaptive')", name=op.f(f"ck_{TABLE}_energy_mode")
        ),
        sa.CheckConstraint(
            "numbers_display in ('show', 'hide_energy', 'hide_all')",
            name=op.f(f"ck_{TABLE}_numbers_display"),
        ),
        sa.CheckConstraint(
            "summary_view in ('remaining', 'consumed')", name=op.f(f"ck_{TABLE}_summary_view")
        ),
    )
    op.create_index(op.f(f"ix_{TABLE}_account_id"), TABLE, ["account_id"])
    # Supabase default privileges grant ALL to anon/authenticated on new tables: tighten.
    op.execute(f"REVOKE ALL ON {TABLE} FROM PUBLIC, anon, authenticated")
    op.execute(f"GRANT SELECT ON {TABLE} TO authenticated")
    op.execute(f"GRANT ALL ON {TABLE} TO service_role")
    op.execute(f"ALTER TABLE {TABLE} ENABLE ROW LEVEL SECURITY")
    op.execute(f"ALTER TABLE {TABLE} FORCE ROW LEVEL SECURITY")
    op.execute(
        f"CREATE POLICY {TABLE}_owner ON {TABLE} FOR ALL TO authenticated "
        f"USING ({OWNER}) WITH CHECK ({OWNER})"
    )


def downgrade() -> None:
    op.drop_table(TABLE)  # drops its policy and index too
    op.drop_constraint("uq_members_id_account_id", "members", type_="unique")
    op.drop_constraint(op.f("ck_members_body_fat_pct"), "members", type_="check")
    op.drop_column("members", "body_fat_pct")
