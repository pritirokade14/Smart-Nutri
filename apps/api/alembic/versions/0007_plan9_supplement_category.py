"""Products may be a `supplement` (Plan 9 Task 7, P9-R10).

Revision ID: 0007_plan9_supplement_category
Revises: 0005_plan8_tombstone_auth
Create Date: 2026-11-04

Widens `ck_products_category` with 'supplement' (protein powders, whey, health supplements:
never graded, never suggested). The user picks it on the confirm screen; Open Food Facts
products get it from their category tags (that data lives in `off_product_cache`, not here).

The downgrade maps `supplement` rows to `general` first, so the old constraint holds. That
loses the supplement marker (they are graded again), which is the only safe fallback for a
schema without the value.

No new table, so grants and RLS are unchanged. The controller re-chains `down_revision`
after the user-types migration (0006) at merge.
"""

from collections.abc import Sequence

from alembic import op

revision: str = "0007_plan9_supplement_category"
down_revision: str | Sequence[str] | None = "0006_plan9_user_types"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

_OLD = "category in ('general', 'beverage', 'water', 'cheese', 'fat')"
_NEW = "category in ('general', 'beverage', 'water', 'cheese', 'fat', 'supplement')"


def upgrade() -> None:
    op.drop_constraint("ck_products_category", "products", type_="check")
    op.create_check_constraint("ck_products_category", "products", _NEW)


def downgrade() -> None:
    op.execute("update products set category = 'general' where category = 'supplement'")
    op.drop_constraint("ck_products_category", "products", type_="check")
    op.create_check_constraint("ck_products_category", "products", _OLD)
