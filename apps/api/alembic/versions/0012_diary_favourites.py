"""Favourites: foods and saved meals (Plan 12 Task 17; spec 5.10, 6.4; G21, G23).

Revision ID: 0012_diary_favourites
Revises: 0011_diary_custom_foods_recipes
Create Date: 2026-11-07

- `favourites` is member-scoped (composite FK to `members(id, account_id)`, ON DELETE CASCADE).
  `kind = 'food'` holds exactly one reference matching `source_kind`, a name snapshot and an
  optional default portion; `kind = 'meal'` holds no reference and the entry snapshots in
  `items` (a copy of the entries of one slot and day, kept as they were).
- `custom_food_id` and `recipe_id` cascade: deleting the custom food or recipe removes its
  favourite (a favourite meal keeps its snapshots, and logs a gone ref as NULL, G21).
- `attributions` snapshots the data credits of a food favourite (Open Food Facts is ODbL).
- Partial unique indexes: a member has a given food at most once.

Privileges and RLS exactly like 0009 and 0011: owner-read for `authenticated`, written only by
the service role, ENABLE + FORCE RLS.

Downgrade drops the table: favourites are lost.
"""

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql as pg

from alembic import op

revision: str = "0012_diary_favourites"
down_revision: str | Sequence[str] | None = "0011_diary_custom_foods_recipes"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

OWNER = "account_id = (SELECT auth.uid())"
REFS = ("product_id", "off_barcode", "food_id", "custom_food_id", "recipe_id")

_KIND_CHECK = (
    "(kind = 'food' AND items IS NULL AND source_kind IS NOT NULL "
    "AND num_nonnulls(product_id, off_barcode, food_id, custom_food_id, recipe_id) = 1 "
    "AND ((source_kind = 'product' AND product_id IS NOT NULL) "
    "OR (source_kind = 'off' AND off_barcode IS NOT NULL) "
    "OR (source_kind = 'food' AND food_id IS NOT NULL) "
    "OR (source_kind = 'custom_food' AND custom_food_id IS NOT NULL) "
    "OR (source_kind = 'recipe' AND recipe_id IS NOT NULL))) "
    "OR (kind = 'meal' AND items IS NOT NULL AND source_kind IS NULL "
    "AND jsonb_typeof(items) = 'array' AND jsonb_array_length(items) BETWEEN 1 AND 50 "
    "AND num_nonnulls(product_id, off_barcode, food_id, custom_food_id, recipe_id) = 0 "
    "AND default_quantity IS NULL AND default_unit IS NULL)"
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


def upgrade() -> None:
    op.create_table(
        "favourites",
        sa.Column(
            "id",
            pg.UUID(as_uuid=True),
            nullable=False,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column("account_id", pg.UUID(as_uuid=True), nullable=False),
        sa.Column("member_id", pg.UUID(as_uuid=True), nullable=False),
        sa.Column("kind", sa.Text(), nullable=False),
        sa.Column("source_kind", sa.Text(), nullable=True),
        sa.Column("product_id", pg.UUID(as_uuid=True), nullable=True),
        sa.Column("off_barcode", sa.Text(), nullable=True),
        sa.Column("food_id", pg.UUID(as_uuid=True), nullable=True),
        sa.Column("custom_food_id", pg.UUID(as_uuid=True), nullable=True),
        sa.Column("recipe_id", pg.UUID(as_uuid=True), nullable=True),
        sa.Column("name", sa.Text(), nullable=False),
        sa.Column("default_quantity", sa.Numeric(), nullable=True),
        sa.Column("default_unit", sa.Text(), nullable=True),
        sa.Column("items", pg.JSONB(), nullable=True),
        sa.Column(
            "attributions",
            pg.ARRAY(sa.Text()),
            nullable=False,
            server_default=sa.text("'{}'::text[]"),
        ),
        sa.Column("client_id", pg.UUID(as_uuid=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_favourites")),
        sa.ForeignKeyConstraint(
            ["account_id"],
            ["accounts.id"],
            name=op.f("fk_favourites_account_id_accounts"),
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["member_id", "account_id"],
            ["members.id", "members.account_id"],
            name=op.f("fk_favourites_member_id_members"),
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["product_id"], ["products.id"], name=op.f("fk_favourites_product_id_products")
        ),
        sa.ForeignKeyConstraint(
            ["food_id"], ["foods.id"], name=op.f("fk_favourites_food_id_foods")
        ),
        sa.ForeignKeyConstraint(
            ["custom_food_id"],
            ["custom_foods.id"],
            name=op.f("fk_favourites_custom_food_id_custom_foods"),
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["recipe_id"],
            ["recipes.id"],
            name=op.f("fk_favourites_recipe_id_recipes"),
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["default_unit"],
            ["household_units.code"],
            name=op.f("fk_favourites_default_unit_household_units"),
        ),
        sa.UniqueConstraint("account_id", "client_id", name="uq_favourites_account_id_client_id"),
        sa.CheckConstraint("kind in ('food', 'meal')", name=op.f("ck_favourites_kind")),
        sa.CheckConstraint(
            "source_kind is null or source_kind in "
            "('product', 'off', 'food', 'custom_food', 'recipe')",
            name=op.f("ck_favourites_source_kind"),
        ),
        sa.CheckConstraint(_KIND_CHECK, name=op.f("ck_favourites_shape")),
        sa.CheckConstraint("char_length(name) between 1 and 200", name=op.f("ck_favourites_name")),
        sa.CheckConstraint(
            "default_quantity is null or (default_quantity > 0 and default_quantity <= 5000)",
            name=op.f("ck_favourites_default_quantity"),
        ),
        sa.CheckConstraint(
            "num_nonnulls(default_quantity, default_unit) in (0, 2)",
            name=op.f("ck_favourites_default_portion"),
        ),
    )
    op.create_index(op.f("ix_favourites_account_id"), "favourites", ["account_id"])
    op.create_index("ix_favourites_member_id_created_at", "favourites", ["member_id", "created_at"])
    for ref in REFS:
        op.create_index(
            f"uq_favourites_member_id_{ref}",
            "favourites",
            ["member_id", ref],
            unique=True,
            postgresql_where=sa.text(f"{ref} IS NOT NULL"),
        )
    _lock_down("favourites")


def downgrade() -> None:
    op.drop_table("favourites")
