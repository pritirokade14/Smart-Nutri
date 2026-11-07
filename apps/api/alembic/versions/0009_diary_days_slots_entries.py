"""Diary days, meal slots and diary-entry columns (Plan 11 Task 1; Rulings E1-E4, E7).

Revision ID: 0009_diary_days_slots_entries
Revises: 0008_diary_goal_settings
Create Date: 2026-11-07

- `accounts.timezone` (IANA name, default Asia/Kolkata; the API validates it).
- `diary_days`: the frozen daily target and the partial-day flag (spec 5.3).
- `meal_slots`: member-scoped slots; the four defaults are rows (spec 5.12). The default
  windows (Ruling E4) are the constants below, equal to `meal_slots/defaults.yaml` (tested).
- `meal_logs` becomes the diary entry: `local_date`, `meal_slot_id`, `source_kind`
  (`product`, `off`, `quick_add`), `food_snapshot`, `updated_at`, nullable `grams`
  (quick add only), `ck_meal_logs_ref` replacing `ck_meal_logs_product_ref`. The entry -> slot
  FK is NO ACTION, not RESTRICT (Ruling E3): RESTRICT is checked row by row inside a cascade,
  so deleting a member would fail; NO ACTION still refuses a hard delete of a used slot.

Back-fill: every member (family included) gets the four default slots; each legacy entry gets
`local_date = (eaten_at AT TIME ZONE 'Asia/Kolkata')::date` and the slot whose IST window
contains its wall-clock minute; `source_kind` is `off` when `product_id IS NULL`, else `product`.

Privileges and RLS for the two new tables exactly like 0008. The `meal_logs_owner` policy is
unchanged.

Downgrade: deletes the `quick_add` rows (they cannot satisfy the old checks), restores the old
checks and NOT NULL `grams`, drops the new columns, `meal_slots` and `diary_days`. Custom slot
names and slot assignments are lost, and so are the frozen daily targets.
"""

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql as pg

from alembic import op

revision: str = "0009_diary_days_slots_entries"
down_revision: str | Sequence[str] | None = "0008_diary_goal_settings"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

OWNER = "account_id = (SELECT auth.uid())"

# (label_key, position, window start, window end), the Ruling E4 bands. Copied from
# meal_slots/defaults.yaml: tests/unit/meal_slots/test_defaults.py keeps them equal.
DEFAULT_SLOT_ROWS: tuple[tuple[str, int, str, str], ...] = (
    ("diary.slot.breakfast", 0, "04:00", "10:59"),
    ("diary.slot.lunch", 1, "11:00", "15:59"),
    ("diary.slot.snack", 2, "16:00", "18:59"),
    ("diary.slot.dinner", 3, "19:00", "03:59"),
)

_REF_CHECK = (
    "(source_kind = 'product' AND product_id IS NOT NULL AND off_barcode IS NULL "
    "AND grams IS NOT NULL) "
    "OR (source_kind = 'off' AND off_barcode IS NOT NULL AND product_id IS NULL "
    "AND grams IS NOT NULL) "
    "OR (source_kind = 'quick_add' AND product_id IS NULL AND off_barcode IS NULL "
    "AND grams IS NULL)"
)


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


def _minutes(hhmm: str) -> int:
    hh, mm = hhmm.split(":")
    return int(hh) * 60 + int(mm)


def upgrade() -> None:
    op.add_column(
        "accounts",
        sa.Column("timezone", sa.Text(), nullable=False, server_default="Asia/Kolkata"),
    )

    # ---- diary_days
    op.create_table(
        "diary_days",
        sa.Column("member_id", pg.UUID(as_uuid=True), nullable=False),
        sa.Column("local_date", sa.Date(), nullable=False),
        sa.Column("account_id", pg.UUID(as_uuid=True), nullable=False),
        sa.Column("status", sa.Text(), nullable=False),
        sa.Column("energy_kcal", sa.Numeric(), nullable=True),
        sa.Column("protein_g", sa.Numeric(), nullable=True),
        sa.Column("fat_g", sa.Numeric(), nullable=True),
        sa.Column("carbs_g", sa.Numeric(), nullable=True),
        sa.Column("basis", sa.Text(), nullable=True),
        sa.Column("direction", sa.Text(), nullable=True),
        sa.Column("rate_pct_bw_per_week", sa.Numeric(), nullable=True),
        sa.Column("inputs", pg.JSONB(), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column(
            "flags", pg.ARRAY(sa.Text()), nullable=False, server_default=sa.text("'{}'::text[]")
        ),
        sa.Column("partial_logged", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column(
            "computed_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.PrimaryKeyConstraint("member_id", "local_date", name=op.f("pk_diary_days")),
        sa.ForeignKeyConstraint(
            ["account_id"],
            ["accounts.id"],
            name=op.f("fk_diary_days_account_id_accounts"),
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["member_id", "account_id"],
            ["members.id", "members.account_id"],
            name=op.f("fk_diary_days_member_id_members"),
            ondelete="CASCADE",
        ),
        sa.CheckConstraint(
            "status in ('ready', 'needs_body_data', 'not_available_minor', "
            "'paused_pregnancy', 'none')",
            name=op.f("ck_diary_days_status"),
        ),
        sa.CheckConstraint(
            "basis is null or basis in ('formula', 'adaptive')",
            name=op.f("ck_diary_days_basis"),
        ),
        sa.CheckConstraint(
            "direction is null or direction in ('lose', 'maintain', 'gain')",
            name=op.f("ck_diary_days_direction"),
        ),
    )
    op.create_index(op.f("ix_diary_days_account_id"), "diary_days", ["account_id"])
    _lock_down("diary_days")

    # ---- meal_slots
    op.create_table(
        "meal_slots",
        sa.Column(
            "id",
            pg.UUID(as_uuid=True),
            nullable=False,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column("account_id", pg.UUID(as_uuid=True), nullable=False),
        sa.Column("member_id", pg.UUID(as_uuid=True), nullable=False),
        sa.Column("position", sa.Integer(), nullable=False),
        sa.Column("label_key", sa.Text(), nullable=True),
        sa.Column("custom_label", sa.Text(), nullable=True),
        sa.Column("default_time_window", pg.JSONB(), nullable=True),
        sa.Column("is_default", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("archived_at", sa.DateTime(timezone=True), nullable=True),
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
        sa.PrimaryKeyConstraint("id", name=op.f("pk_meal_slots")),
        sa.ForeignKeyConstraint(
            ["account_id"],
            ["accounts.id"],
            name=op.f("fk_meal_slots_account_id_accounts"),
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["member_id", "account_id"],
            ["members.id", "members.account_id"],
            name=op.f("fk_meal_slots_member_id_members"),
            ondelete="CASCADE",
        ),
        sa.UniqueConstraint("id", "member_id", name="uq_meal_slots_id_member_id"),
        sa.UniqueConstraint("account_id", "client_id", name="uq_meal_slots_account_id_client_id"),
        sa.CheckConstraint(
            "label_key is not null or custom_label is not null",
            name=op.f("ck_meal_slots_label_present"),
        ),
        sa.CheckConstraint(
            "custom_label is null or char_length(custom_label) between 1 and 30",
            name=op.f("ck_meal_slots_custom_label_length"),
        ),
        sa.CheckConstraint(
            "label_key is null or label_key in ('diary.slot.breakfast', 'diary.slot.lunch', "
            "'diary.slot.snack', 'diary.slot.dinner')",
            name=op.f("ck_meal_slots_label_key"),
        ),
        sa.CheckConstraint('"position" >= 0', name=op.f("ck_meal_slots_position")),
    )
    op.create_index(op.f("ix_meal_slots_account_id"), "meal_slots", ["account_id"])
    op.create_index(
        "uq_meal_slots_member_default",
        "meal_slots",
        ["member_id", "label_key"],
        unique=True,
        postgresql_where=sa.text("is_default"),
    )
    op.create_index(
        "uq_meal_slots_member_label",
        "meal_slots",
        ["member_id", sa.text("lower(custom_label)")],
        unique=True,
        postgresql_where=sa.text("archived_at IS NULL AND custom_label IS NOT NULL"),
    )
    _lock_down("meal_slots")

    # ---- back-fill 1: the four default slots for every member
    values = ", ".join(
        f"('{key}', {pos}, '{start}', '{end}')" for key, pos, start, end in DEFAULT_SLOT_ROWS
    )
    op.execute(
        "INSERT INTO meal_slots (account_id, member_id, position, label_key, "
        "default_time_window, is_default) "
        "SELECT m.account_id, m.id, d.position, d.label_key, "
        "jsonb_build_object('start', d.s, 'end', d.e), true "
        f"FROM members m CROSS JOIN (VALUES {values}) AS d(label_key, position, s, e)"
    )

    # ---- meal_logs: new columns (nullable first), then the back-fill
    op.add_column("meal_logs", sa.Column("local_date", sa.Date(), nullable=True))
    op.add_column("meal_logs", sa.Column("meal_slot_id", pg.UUID(as_uuid=True), nullable=True))
    op.add_column(
        "meal_logs",
        sa.Column("source_kind", sa.Text(), nullable=False, server_default="product"),
    )
    op.add_column("meal_logs", sa.Column("food_snapshot", pg.JSONB(), nullable=True))
    op.add_column(
        "meal_logs",
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
    )
    op.alter_column("meal_logs", "grams", existing_type=sa.Numeric(), nullable=True)

    op.execute(
        "UPDATE meal_logs SET "
        "local_date = (eaten_at AT TIME ZONE 'Asia/Kolkata')::date, "
        "source_kind = CASE WHEN product_id IS NULL THEN 'off' ELSE 'product' END"
    )
    # Slot by the IST wall-clock minute (inclusive windows, wrapping past midnight).
    cases = " ".join(
        f"WHEN ({_minutes(s)} <= {_minutes(e)} AND t.minute BETWEEN {_minutes(s)} AND {_minutes(e)}) "
        f"OR ({_minutes(s)} > {_minutes(e)} AND (t.minute >= {_minutes(s)} "
        f"OR t.minute <= {_minutes(e)})) THEN '{key}'"
        for key, _pos, s, e in DEFAULT_SLOT_ROWS
    )
    op.execute(
        "UPDATE meal_logs ml SET meal_slot_id = s.id "
        "FROM (SELECT l.id AS log_id, l.member_id, "
        "  (extract(hour from l.eaten_at AT TIME ZONE 'Asia/Kolkata')::int * 60 "
        "   + extract(minute from l.eaten_at AT TIME ZONE 'Asia/Kolkata')::int) AS minute "
        "  FROM meal_logs l) t "
        "JOIN meal_slots s ON s.member_id = t.member_id AND s.is_default AND s.label_key = "
        f"(CASE {cases} END) "
        "WHERE ml.id = t.log_id"
    )
    op.alter_column("meal_logs", "local_date", existing_type=sa.Date(), nullable=False)
    op.alter_column(
        "meal_logs", "meal_slot_id", existing_type=pg.UUID(as_uuid=True), nullable=False
    )

    # ---- meal_logs: constraints and index
    # The baseline names go through the naming convention (the DB name is
    # ck_meal_logs_ck_meal_logs_grams): drop by the same plain name, create with op.f.
    op.drop_constraint("ck_meal_logs_grams", "meal_logs", type_="check")
    op.create_check_constraint(
        op.f("ck_meal_logs_grams"), "meal_logs", "grams is null or (grams > 0 and grams <= 5000)"
    )
    op.drop_constraint("ck_meal_logs_product_ref", "meal_logs", type_="check")
    op.create_check_constraint(op.f("ck_meal_logs_ref"), "meal_logs", _REF_CHECK)
    op.create_check_constraint(
        op.f("ck_meal_logs_source_kind"),
        "meal_logs",
        "source_kind in ('product', 'off', 'quick_add')",
    )
    op.create_foreign_key(
        op.f("fk_meal_logs_meal_slot_id_meal_slots"),
        "meal_logs",
        "meal_slots",
        ["meal_slot_id", "member_id"],
        ["id", "member_id"],
    )  # NO ACTION (Ruling E3)
    op.create_index(
        "ix_meal_logs_member_id_local_date",
        "meal_logs",
        ["member_id", "local_date", "meal_slot_id"],
    )


def downgrade() -> None:
    # Quick adds have no product and no grams: they cannot satisfy the old checks.
    op.execute("DELETE FROM meal_logs WHERE source_kind = 'quick_add'")
    op.drop_index("ix_meal_logs_member_id_local_date", table_name="meal_logs")
    op.drop_constraint(
        op.f("fk_meal_logs_meal_slot_id_meal_slots"), "meal_logs", type_="foreignkey"
    )
    op.drop_constraint(op.f("ck_meal_logs_source_kind"), "meal_logs", type_="check")
    op.drop_constraint(op.f("ck_meal_logs_ref"), "meal_logs", type_="check")
    op.create_check_constraint(
        "ck_meal_logs_product_ref", "meal_logs", "num_nonnulls(product_id, off_barcode) = 1"
    )
    op.drop_constraint(op.f("ck_meal_logs_grams"), "meal_logs", type_="check")
    op.alter_column("meal_logs", "grams", existing_type=sa.Numeric(), nullable=False)
    # Plain names: the naming convention gives the baseline's doubled DB names back.
    op.create_check_constraint("ck_meal_logs_grams", "meal_logs", "grams > 0 and grams <= 5000")
    for col in ("updated_at", "food_snapshot", "source_kind", "meal_slot_id", "local_date"):
        op.drop_column("meal_logs", col)
    op.drop_table("meal_slots")
    op.drop_table("diary_days")
    op.drop_column("accounts", "timezone")
