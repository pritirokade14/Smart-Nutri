"""Custom foods, recipes and recipe ingredients (Plan 12 Task 10; spec 5.1, 5.6, 5.8, 5.9; G18-G22).

Revision ID: 0011_diary_custom_foods_recipes
Revises: 0010_diary_foods_units
Create Date: 2026-11-07

- `custom_foods`: a food the account typed from a label (account-owned). `per_100` holds the
  Nutrients field names, `entered` the values as typed. A blank stays unknown.
- `recipes` and `recipe_ingredients`: `per_100g` is the sum of the KNOWN parts and
  `incomplete_nutrients` names what at least one ingredient does not know (G19).
- `food_portions.custom_food_id`: the account's own grams per unit of a custom food.
- `meal_logs.custom_food_id` and `recipe_id` (ON DELETE SET NULL, G21): deleting a custom food
  or recipe keeps the entry (its `food_snapshot` holds the name and values). The ref check
  allows a NULL id for those two kinds.

Privileges and RLS exactly like 0009: the three new tables are owner-read for `authenticated`
(`account_id = auth.uid()`), written only by the service role, ENABLE + FORCE RLS.

Downgrade: deletes the `custom_food` and `recipe` entries and the user portions of custom foods,
restores the 0010 checks, drops the new columns and the three tables. Custom foods, recipes and
their entries are lost.
"""

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql as pg

from alembic import op

revision: str = "0011_diary_custom_foods_recipes"
down_revision: str | Sequence[str] | None = "0010_diary_foods_units"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

OWNER = "account_id = (SELECT auth.uid())"
NIL_UUID = "00000000-0000-0000-0000-000000000000"

_OLD_REF_CHECK = (
    "(source_kind = 'product' AND product_id IS NOT NULL AND off_barcode IS NULL "
    "AND food_id IS NULL AND grams IS NOT NULL) "
    "OR (source_kind = 'off' AND off_barcode IS NOT NULL AND product_id IS NULL "
    "AND food_id IS NULL AND grams IS NOT NULL) "
    "OR (source_kind = 'food' AND food_id IS NOT NULL AND product_id IS NULL "
    "AND off_barcode IS NULL AND grams IS NOT NULL) "
    "OR (source_kind = 'quick_add' AND product_id IS NULL AND off_barcode IS NULL "
    "AND food_id IS NULL AND grams IS NULL)"
)
_NO_NEW_REFS = "AND custom_food_id IS NULL AND recipe_id IS NULL"
_NEW_REF_CHECK = (
    "(source_kind = 'product' AND product_id IS NOT NULL AND off_barcode IS NULL "
    f"AND food_id IS NULL {_NO_NEW_REFS} AND grams IS NOT NULL) "
    "OR (source_kind = 'off' AND off_barcode IS NOT NULL AND product_id IS NULL "
    f"AND food_id IS NULL {_NO_NEW_REFS} AND grams IS NOT NULL) "
    "OR (source_kind = 'food' AND food_id IS NOT NULL AND product_id IS NULL "
    f"AND off_barcode IS NULL {_NO_NEW_REFS} AND grams IS NOT NULL) "
    "OR (source_kind = 'quick_add' AND product_id IS NULL AND off_barcode IS NULL "
    f"AND food_id IS NULL {_NO_NEW_REFS} AND grams IS NULL) "
    # custom_food and recipe: the id is NULL once the food or recipe was deleted (G21).
    "OR (source_kind IN ('custom_food', 'recipe') AND product_id IS NULL "
    "AND off_barcode IS NULL AND food_id IS NULL AND grams IS NOT NULL "
    "AND num_nonnulls(custom_food_id, recipe_id) <= 1 "
    "AND (source_kind = 'custom_food' OR custom_food_id IS NULL) "
    "AND (source_kind = 'recipe' OR recipe_id IS NULL))"
)
_ING_REF_CHECK = (
    "(source_kind = 'product' AND product_id IS NOT NULL AND off_barcode IS NULL "
    "AND food_id IS NULL AND custom_food_id IS NULL) "
    "OR (source_kind = 'off' AND off_barcode IS NOT NULL AND product_id IS NULL "
    "AND food_id IS NULL AND custom_food_id IS NULL) "
    "OR (source_kind = 'food' AND food_id IS NOT NULL AND product_id IS NULL "
    "AND off_barcode IS NULL AND custom_food_id IS NULL) "
    # NULL custom_food_id: the custom food was deleted (G21).
    "OR (source_kind = 'custom_food' AND product_id IS NULL AND off_barcode IS NULL "
    "AND food_id IS NULL)"
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


def _id() -> sa.Column:
    return sa.Column(
        "id", pg.UUID(as_uuid=True), nullable=False, server_default=sa.text("gen_random_uuid()")
    )


def _now() -> sa.TextClause:
    return sa.text("now()")


def upgrade() -> None:
    # ---- custom_foods
    op.create_table(
        "custom_foods",
        _id(),
        sa.Column("account_id", pg.UUID(as_uuid=True), nullable=False),
        sa.Column("name", sa.Text(), nullable=False),
        sa.Column("brand", sa.Text(), nullable=True),
        sa.Column("basis", sa.Text(), nullable=False),
        sa.Column("per_100", pg.JSONB(), nullable=False),
        sa.Column("entered", pg.JSONB(), nullable=False),
        sa.Column("serving_g", sa.Numeric(), nullable=True),
        sa.Column("density_g_per_ml", sa.Numeric(), nullable=True),
        sa.Column("barcode", sa.Text(), nullable=True),
        sa.Column("client_id", pg.UUID(as_uuid=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=_now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=_now()),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_custom_foods")),
        sa.ForeignKeyConstraint(
            ["account_id"],
            ["accounts.id"],
            name=op.f("fk_custom_foods_account_id_accounts"),
            ondelete="CASCADE",
        ),
        sa.UniqueConstraint("account_id", "barcode", name="uq_custom_foods_account_id_barcode"),
        sa.UniqueConstraint("account_id", "client_id", name="uq_custom_foods_account_id_client_id"),
        sa.CheckConstraint("char_length(name) between 1 and 80", name=op.f("ck_custom_foods_name")),
        sa.CheckConstraint(
            "brand is null or char_length(brand) between 1 and 80",
            name=op.f("ck_custom_foods_brand"),
        ),
        sa.CheckConstraint("basis in ('g', 'ml')", name=op.f("ck_custom_foods_basis")),
        sa.CheckConstraint(
            "serving_g is null or serving_g > 0", name=op.f("ck_custom_foods_serving_g")
        ),
        sa.CheckConstraint(
            "density_g_per_ml is null or (density_g_per_ml >= 0.2 and density_g_per_ml <= 2.0)",
            name=op.f("ck_custom_foods_density"),
        ),
    )
    op.create_index(op.f("ix_custom_foods_account_id"), "custom_foods", ["account_id"])
    _lock_down("custom_foods")

    # ---- recipes
    op.create_table(
        "recipes",
        _id(),
        sa.Column("account_id", pg.UUID(as_uuid=True), nullable=False),
        sa.Column("name", sa.Text(), nullable=False),
        sa.Column("servings", sa.Numeric(), nullable=True),
        sa.Column("cooked_weight_g", sa.Numeric(), nullable=True),
        sa.Column("total_raw_g", sa.Numeric(), nullable=True),
        sa.Column("per_100g", pg.JSONB(), nullable=False),
        sa.Column(
            "incomplete_nutrients",
            pg.ARRAY(sa.Text()),
            nullable=False,
            server_default=sa.text("'{}'::text[]"),
        ),
        sa.Column("client_id", pg.UUID(as_uuid=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=_now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=_now()),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_recipes")),
        sa.ForeignKeyConstraint(
            ["account_id"],
            ["accounts.id"],
            name=op.f("fk_recipes_account_id_accounts"),
            ondelete="CASCADE",
        ),
        sa.UniqueConstraint("account_id", "client_id", name="uq_recipes_account_id_client_id"),
        sa.CheckConstraint("char_length(name) between 1 and 80", name=op.f("ck_recipes_name")),
        sa.CheckConstraint(
            "servings is null or (servings > 0 and servings <= 100)",
            name=op.f("ck_recipes_servings"),
        ),
        sa.CheckConstraint(
            "cooked_weight_g is null or (cooked_weight_g > 0 and cooked_weight_g <= 20000)",
            name=op.f("ck_recipes_cooked_weight_g"),
        ),
    )
    op.create_index(op.f("ix_recipes_account_id"), "recipes", ["account_id"])
    _lock_down("recipes")

    # ---- recipe_ingredients
    op.create_table(
        "recipe_ingredients",
        _id(),
        sa.Column("recipe_id", pg.UUID(as_uuid=True), nullable=False),
        sa.Column("account_id", pg.UUID(as_uuid=True), nullable=False),
        sa.Column("position", sa.Integer(), nullable=False),
        sa.Column("source_kind", sa.Text(), nullable=False),
        sa.Column("product_id", pg.UUID(as_uuid=True), nullable=True),
        sa.Column("off_barcode", sa.Text(), nullable=True),
        sa.Column("food_id", pg.UUID(as_uuid=True), nullable=True),
        sa.Column("custom_food_id", pg.UUID(as_uuid=True), nullable=True),
        sa.Column("name", sa.Text(), nullable=False),
        sa.Column("quantity", sa.Numeric(), nullable=False),
        sa.Column("unit", sa.Text(), nullable=False),
        sa.Column("grams", sa.Numeric(), nullable=False),
        sa.Column("basis", sa.Text(), nullable=False),
        sa.Column("weight_g", sa.Numeric(), nullable=True),
        sa.Column("per_100", pg.JSONB(), nullable=False),
        sa.Column("attribution", sa.Text(), nullable=True),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_recipe_ingredients")),
        sa.ForeignKeyConstraint(
            ["recipe_id"],
            ["recipes.id"],
            name=op.f("fk_recipe_ingredients_recipe_id_recipes"),
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["account_id"],
            ["accounts.id"],
            name=op.f("fk_recipe_ingredients_account_id_accounts"),
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["product_id"],
            ["products.id"],
            name=op.f("fk_recipe_ingredients_product_id_products"),
        ),
        sa.ForeignKeyConstraint(
            ["food_id"], ["foods.id"], name=op.f("fk_recipe_ingredients_food_id_foods")
        ),
        sa.ForeignKeyConstraint(
            ["custom_food_id"],
            ["custom_foods.id"],
            name=op.f("fk_recipe_ingredients_custom_food_id_custom_foods"),
            ondelete="SET NULL",
        ),
        sa.ForeignKeyConstraint(
            ["unit"],
            ["household_units.code"],
            name=op.f("fk_recipe_ingredients_unit_household_units"),
        ),
        sa.UniqueConstraint(
            "recipe_id", "position", name="uq_recipe_ingredients_recipe_id_position"
        ),
        sa.CheckConstraint(
            "source_kind in ('product', 'off', 'food', 'custom_food')",
            name=op.f("ck_recipe_ingredients_source_kind"),
        ),
        sa.CheckConstraint(_ING_REF_CHECK, name=op.f("ck_recipe_ingredients_ref")),
        sa.CheckConstraint('"position" >= 0', name=op.f("ck_recipe_ingredients_position")),
        sa.CheckConstraint("quantity > 0", name=op.f("ck_recipe_ingredients_quantity")),
        sa.CheckConstraint("grams > 0 and grams <= 5000", name=op.f("ck_recipe_ingredients_grams")),
        sa.CheckConstraint("basis in ('g', 'ml')", name=op.f("ck_recipe_ingredients_basis")),
        sa.CheckConstraint(
            "weight_g is null or weight_g > 0", name=op.f("ck_recipe_ingredients_weight_g")
        ),
    )
    op.create_index(op.f("ix_recipe_ingredients_account_id"), "recipe_ingredients", ["account_id"])
    _lock_down("recipe_ingredients")

    # ---- food_portions: the account's own grams for a custom food
    op.add_column(
        "food_portions", sa.Column("custom_food_id", pg.UUID(as_uuid=True), nullable=True)
    )
    op.create_foreign_key(
        op.f("fk_food_portions_custom_food_id_custom_foods"),
        "food_portions",
        "custom_foods",
        ["custom_food_id"],
        ["id"],
        ondelete="CASCADE",
    )
    op.drop_constraint(op.f("ck_food_portions_ref"), "food_portions", type_="check")
    op.create_check_constraint(
        op.f("ck_food_portions_ref"),
        "food_portions",
        "num_nonnulls(food_id, product_id, off_barcode, custom_food_id) = 1",
    )
    op.create_index(
        "uq_food_portions_custom_food",
        "food_portions",
        [sa.text(f"coalesce(account_id, '{NIL_UUID}'::uuid)"), "custom_food_id", "unit"],
        unique=True,
        postgresql_where=sa.text("custom_food_id IS NOT NULL"),
    )

    # ---- meal_logs: the custom-food and recipe entries
    op.add_column("meal_logs", sa.Column("custom_food_id", pg.UUID(as_uuid=True), nullable=True))
    op.add_column("meal_logs", sa.Column("recipe_id", pg.UUID(as_uuid=True), nullable=True))
    op.create_foreign_key(
        op.f("fk_meal_logs_custom_food_id_custom_foods"),
        "meal_logs",
        "custom_foods",
        ["custom_food_id"],
        ["id"],
        ondelete="SET NULL",
    )
    op.create_foreign_key(
        op.f("fk_meal_logs_recipe_id_recipes"),
        "meal_logs",
        "recipes",
        ["recipe_id"],
        ["id"],
        ondelete="SET NULL",
    )
    op.drop_constraint(op.f("ck_meal_logs_ref"), "meal_logs", type_="check")
    op.create_check_constraint(op.f("ck_meal_logs_ref"), "meal_logs", _NEW_REF_CHECK)
    op.drop_constraint(op.f("ck_meal_logs_source_kind"), "meal_logs", type_="check")
    op.create_check_constraint(
        op.f("ck_meal_logs_source_kind"),
        "meal_logs",
        "source_kind in ('product', 'off', 'food', 'custom_food', 'recipe', 'quick_add')",
    )


def downgrade() -> None:
    # These entries cannot satisfy the 0010 checks; the portions need the table they point at.
    op.execute("DELETE FROM meal_logs WHERE source_kind IN ('custom_food', 'recipe')")
    op.execute("DELETE FROM food_portions WHERE custom_food_id IS NOT NULL")
    op.drop_constraint(op.f("ck_meal_logs_source_kind"), "meal_logs", type_="check")
    op.create_check_constraint(
        op.f("ck_meal_logs_source_kind"),
        "meal_logs",
        "source_kind in ('product', 'off', 'food', 'quick_add')",
    )
    op.drop_constraint(op.f("ck_meal_logs_ref"), "meal_logs", type_="check")
    op.create_check_constraint(op.f("ck_meal_logs_ref"), "meal_logs", _OLD_REF_CHECK)
    op.drop_constraint(op.f("fk_meal_logs_recipe_id_recipes"), "meal_logs", type_="foreignkey")
    op.drop_constraint(
        op.f("fk_meal_logs_custom_food_id_custom_foods"), "meal_logs", type_="foreignkey"
    )
    op.drop_column("meal_logs", "recipe_id")
    op.drop_column("meal_logs", "custom_food_id")

    op.drop_index("uq_food_portions_custom_food", table_name="food_portions")
    op.drop_constraint(op.f("ck_food_portions_ref"), "food_portions", type_="check")
    op.create_check_constraint(
        op.f("ck_food_portions_ref"),
        "food_portions",
        "num_nonnulls(food_id, product_id, off_barcode) = 1",
    )
    op.drop_constraint(
        op.f("fk_food_portions_custom_food_id_custom_foods"), "food_portions", type_="foreignkey"
    )
    op.drop_column("food_portions", "custom_food_id")

    op.drop_table("recipe_ingredients")
    op.drop_table("recipes")
    op.drop_table("custom_foods")
