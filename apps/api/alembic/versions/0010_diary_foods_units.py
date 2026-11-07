"""Household units, generic foods, food portions and the food entry (Plan 12 Task 1; G1-G4, G12).

Revision ID: 0010_diary_foods_units
Revises: 0009_diary_days_slots_entries
Create Date: 2026-11-07

- `household_units`: the 17 unit codes (reference table). Seeded here from `UNIT_ROWS`, equal to
  `app/features/foods/data/household_units.yaml` (tested). Katori is 200 ml (Q6b).
- `foods`: generic foods and documented dishes (reference table). Empty here: the idempotent job
  `python -m app.jobs.seed_foods` loads them, so food ids stay stable across reseeds.
- `food_portions`: grams per unit for one food, product or OFF barcode. A global row
  (`account_id` NULL) is ours; a `user` row is the account's own override.
- `meal_logs` gains `food_id`, `quantity` and `unit`; `source_kind` gains `food`.

Privileges and RLS like 0008/0009. `foods` and `household_units` are readable by everyone
signed in; `food_portions` shows global rows and the caller's own. Writes are service-role only.

Downgrade: deletes the `meal_logs` rows with `source_kind = 'food'` (they cannot satisfy the
0009 checks; product and quick-add entries stay), restores the 0009 checks, drops the new
columns and the three tables. Foods, portion overrides and entries of generic foods are lost.
"""

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql as pg

from alembic import op

revision: str = "0010_diary_foods_units"
down_revision: str | Sequence[str] | None = "0009_diary_days_slots_entries"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

OWNER = "account_id = (SELECT auth.uid())"
NIL_UUID = "00000000-0000-0000-0000-000000000000"

# (code, kind, ml, grams, sort), the G4 order. Copied from household_units.yaml:
# tests/unit/foods/test_unit_rows.py keeps them equal.
UNIT_ROWS: tuple[tuple[str, str, str | None, str | None, int], ...] = (
    ("g", "mass", None, "1", 0),
    ("ml", "volume", "1", None, 1),
    ("serving", "count", None, None, 2),
    ("piece", "count", None, None, 3),
    ("piece_small", "count", None, None, 4),
    ("piece_medium", "count", None, None, 5),
    ("piece_large", "count", None, None, 6),
    ("roti", "count", None, None, 7),
    ("slice", "count", None, None, 8),
    ("katori", "volume", "200", None, 9),
    ("katori_small", "volume", "115", None, 10),
    ("katori_medium", "volume", "155", None, 11),
    ("katori_large", "volume", "360", None, 12),
    ("cup", "volume", "200", None, 13),
    ("glass", "volume", "250", None, 14),
    ("tbsp", "volume", "15", None, 15),
    ("tsp", "volume", "5", None, 16),
)

_OLD_REF_CHECK = (
    "(source_kind = 'product' AND product_id IS NOT NULL AND off_barcode IS NULL "
    "AND grams IS NOT NULL) "
    "OR (source_kind = 'off' AND off_barcode IS NOT NULL AND product_id IS NULL "
    "AND grams IS NOT NULL) "
    "OR (source_kind = 'quick_add' AND product_id IS NULL AND off_barcode IS NULL "
    "AND grams IS NULL)"
)
_NEW_REF_CHECK = (
    "(source_kind = 'product' AND product_id IS NOT NULL AND off_barcode IS NULL "
    "AND food_id IS NULL AND grams IS NOT NULL) "
    "OR (source_kind = 'off' AND off_barcode IS NOT NULL AND product_id IS NULL "
    "AND food_id IS NULL AND grams IS NOT NULL) "
    "OR (source_kind = 'food' AND food_id IS NOT NULL AND product_id IS NULL "
    "AND off_barcode IS NULL AND grams IS NOT NULL) "
    "OR (source_kind = 'quick_add' AND product_id IS NULL AND off_barcode IS NULL "
    "AND food_id IS NULL AND grams IS NULL)"
)


def _lock_down_reference(table: str, read_policy: str) -> None:
    # Supabase default privileges grant ALL to anon/authenticated on new tables: tighten.
    op.execute(f"REVOKE ALL ON {table} FROM PUBLIC, anon, authenticated")
    op.execute(f"GRANT SELECT ON {table} TO authenticated")
    op.execute(f"GRANT ALL ON {table} TO service_role")
    op.execute(f"ALTER TABLE {table} ENABLE ROW LEVEL SECURITY")
    op.execute(f"ALTER TABLE {table} FORCE ROW LEVEL SECURITY")
    op.execute(
        f"CREATE POLICY {table}_read ON {table} FOR SELECT TO authenticated USING ({read_policy})"
    )


def _now() -> sa.TextClause:
    return sa.text("now()")


def upgrade() -> None:
    # ---- household_units
    op.create_table(
        "household_units",
        sa.Column("code", sa.Text(), nullable=False),
        sa.Column("kind", sa.Text(), nullable=False),
        sa.Column("ml", sa.Numeric(), nullable=True),
        sa.Column("grams", sa.Numeric(), nullable=True),
        sa.Column("sort", sa.Integer(), nullable=False),
        sa.PrimaryKeyConstraint("code", name=op.f("pk_household_units")),
        sa.CheckConstraint(
            "(kind = 'mass' AND grams > 0 AND ml IS NULL) "
            "OR (kind = 'volume' AND ml > 0 AND grams IS NULL) "
            "OR (kind = 'count' AND ml IS NULL AND grams IS NULL)",
            name=op.f("ck_household_units_kind_values"),
        ),
        sa.CheckConstraint(
            "kind in ('mass', 'volume', 'count')", name=op.f("ck_household_units_kind")
        ),
    )
    _lock_down_reference("household_units", "true")
    for code, kind, ml, grams, sort in UNIT_ROWS:
        op.execute(
            sa.text(
                "INSERT INTO household_units (code, kind, ml, grams, sort) "
                "VALUES (:code, :kind, CAST(:ml AS numeric), CAST(:grams AS numeric), :sort)"
            ).bindparams(code=code, kind=kind, ml=ml, grams=grams, sort=sort)
        )

    # ---- foods
    op.create_table(
        "foods",
        sa.Column(
            "id", pg.UUID(as_uuid=True), nullable=False, server_default=sa.text("gen_random_uuid()")
        ),
        sa.Column("source", sa.Text(), nullable=False),
        sa.Column("source_code", sa.Text(), nullable=False),
        sa.Column("name_en", sa.Text(), nullable=False),
        sa.Column("name_hi", sa.Text(), nullable=True),
        sa.Column("name_mr", sa.Text(), nullable=True),
        sa.Column(
            "aliases", pg.ARRAY(sa.Text()), nullable=False, server_default=sa.text("'{}'::text[]")
        ),
        sa.Column("search_text", sa.Text(), nullable=False),
        sa.Column("basis", sa.Text(), nullable=False),
        sa.Column("per_100", pg.JSONB(), nullable=False),
        sa.Column("density_g_per_ml", sa.Numeric(), nullable=True),
        sa.Column("density_source", sa.Text(), nullable=True),
        sa.Column("serving_g", sa.Numeric(), nullable=True),
        sa.Column("recipe", pg.JSONB(), nullable=True),
        sa.Column("licence", sa.Text(), nullable=False),
        sa.Column("data_version", sa.Text(), nullable=False),
        sa.Column(
            "review_status",
            sa.Text(),
            nullable=False,
            server_default="pending_dietitian_review",
        ),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=_now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=_now()),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_foods")),
        sa.UniqueConstraint("source", "source_code", name="uq_foods_source_source_code"),
        sa.CheckConstraint(
            "source in ('usda_fdc', 'smartnutri_recipe')", name=op.f("ck_foods_source")
        ),
        sa.CheckConstraint("basis in ('g', 'ml')", name=op.f("ck_foods_basis")),
        sa.CheckConstraint(
            "density_g_per_ml is null or density_g_per_ml > 0", name=op.f("ck_foods_density")
        ),
        sa.CheckConstraint("serving_g is null or serving_g > 0", name=op.f("ck_foods_serving_g")),
    )
    _lock_down_reference("foods", "true")

    # ---- food_portions
    op.create_table(
        "food_portions",
        sa.Column(
            "id", pg.UUID(as_uuid=True), nullable=False, server_default=sa.text("gen_random_uuid()")
        ),
        sa.Column("account_id", pg.UUID(as_uuid=True), nullable=True),
        sa.Column("food_id", pg.UUID(as_uuid=True), nullable=True),
        sa.Column("product_id", pg.UUID(as_uuid=True), nullable=True),
        sa.Column("off_barcode", sa.Text(), nullable=True),
        sa.Column("unit", sa.Text(), nullable=False),
        sa.Column("grams_per_unit", sa.Numeric(), nullable=False),
        sa.Column("source", sa.Text(), nullable=False),
        sa.Column("csv_key", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=_now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=_now()),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_food_portions")),
        sa.ForeignKeyConstraint(
            ["account_id"],
            ["accounts.id"],
            name=op.f("fk_food_portions_account_id_accounts"),
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["food_id"],
            ["foods.id"],
            name=op.f("fk_food_portions_food_id_foods"),
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["product_id"],
            ["products.id"],
            name=op.f("fk_food_portions_product_id_products"),
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["unit"], ["household_units.code"], name=op.f("fk_food_portions_unit_household_units")
        ),
        sa.CheckConstraint(
            "num_nonnulls(food_id, product_id, off_barcode) = 1", name=op.f("ck_food_portions_ref")
        ),
        sa.CheckConstraint(
            "grams_per_unit > 0 and grams_per_unit <= 2000", name=op.f("ck_food_portions_grams")
        ),
        sa.CheckConstraint(
            "source in ('smartnutri_measured', 'reference_table', 'user', 'label')",
            name=op.f("ck_food_portions_source"),
        ),
        sa.CheckConstraint(
            "(account_id IS NULL) = (source <> 'user')", name=op.f("ck_food_portions_owner")
        ),
    )
    op.create_index(op.f("ix_food_portions_account_id"), "food_portions", ["account_id"])
    owner = f"coalesce(account_id, '{NIL_UUID}'::uuid)"
    for name, ref in (
        ("uq_food_portions_food", "food_id"),
        ("uq_food_portions_product", "product_id"),
        ("uq_food_portions_off", "off_barcode"),
    ):
        op.create_index(
            name,
            "food_portions",
            [sa.text(owner), ref, "unit"],
            unique=True,
            postgresql_where=sa.text(f"{ref} IS NOT NULL"),
        )
    _lock_down_reference("food_portions", f"account_id IS NULL OR {OWNER}")

    # ---- meal_logs: the food entry
    op.add_column("meal_logs", sa.Column("food_id", pg.UUID(as_uuid=True), nullable=True))
    op.add_column("meal_logs", sa.Column("quantity", sa.Numeric(), nullable=True))
    op.add_column("meal_logs", sa.Column("unit", sa.Text(), nullable=True))
    op.create_foreign_key(
        op.f("fk_meal_logs_food_id_foods"), "meal_logs", "foods", ["food_id"], ["id"]
    )  # NO ACTION: a food in use is never hard-deleted (the seed upserts)
    op.create_foreign_key(
        op.f("fk_meal_logs_unit_household_units"),
        "meal_logs",
        "household_units",
        ["unit"],
        ["code"],
    )
    op.create_check_constraint(
        op.f("ck_meal_logs_quantity"),
        "meal_logs",
        "quantity is null or (quantity > 0 and quantity <= 5000)",
    )
    op.create_check_constraint(
        op.f("ck_meal_logs_quantity_unit"), "meal_logs", "num_nonnulls(quantity, unit) in (0, 2)"
    )
    op.drop_constraint(op.f("ck_meal_logs_ref"), "meal_logs", type_="check")
    op.create_check_constraint(op.f("ck_meal_logs_ref"), "meal_logs", _NEW_REF_CHECK)
    op.drop_constraint(op.f("ck_meal_logs_source_kind"), "meal_logs", type_="check")
    op.create_check_constraint(
        op.f("ck_meal_logs_source_kind"),
        "meal_logs",
        "source_kind in ('product', 'off', 'food', 'quick_add')",
    )


def downgrade() -> None:
    # Food entries have no product and cannot satisfy the 0009 checks.
    op.execute("DELETE FROM meal_logs WHERE source_kind = 'food'")
    op.drop_constraint(op.f("ck_meal_logs_source_kind"), "meal_logs", type_="check")
    op.create_check_constraint(
        op.f("ck_meal_logs_source_kind"),
        "meal_logs",
        "source_kind in ('product', 'off', 'quick_add')",
    )
    op.drop_constraint(op.f("ck_meal_logs_ref"), "meal_logs", type_="check")
    op.create_check_constraint(op.f("ck_meal_logs_ref"), "meal_logs", _OLD_REF_CHECK)
    op.drop_constraint(op.f("ck_meal_logs_quantity_unit"), "meal_logs", type_="check")
    op.drop_constraint(op.f("ck_meal_logs_quantity"), "meal_logs", type_="check")
    op.drop_constraint(op.f("fk_meal_logs_unit_household_units"), "meal_logs", type_="foreignkey")
    op.drop_constraint(op.f("fk_meal_logs_food_id_foods"), "meal_logs", type_="foreignkey")
    for col in ("unit", "quantity", "food_id"):
        op.drop_column("meal_logs", col)
    op.drop_table("food_portions")
    op.drop_table("foods")
    op.drop_table("household_units")
