"""Meal logs for Open Food Facts products (Plan 6 T2; CROSS-PLAN-NOTES 11; ADR 0017).

Revision ID: 0003_plan6_meal_logs_off
Revises: 0002_scans_path_unique
Create Date: 2026-11-03

Most scanned products come from Open Food Facts and have no ``products`` row (OFF data stays
in ``off_product_cache``, ODbL). A meal log therefore references EITHER our own product
(``product_id``) OR an OFF barcode (``off_barcode``), never both. ``product_name`` and
``grade`` are snapshots taken at log time, like ``nutrients``, so history never depends on a
cache entry that may expire. No new table, so RLS and grants are unchanged (the baseline
``meal_logs_owner`` policy still applies).
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "0003_plan6_meal_logs_off"
down_revision: str | Sequence[str] | None = "0002_scans_path_unique"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("meal_logs", sa.Column("off_barcode", sa.Text(), nullable=True))
    op.add_column("meal_logs", sa.Column("product_name", sa.Text(), nullable=True))
    op.add_column("meal_logs", sa.Column("grade", sa.Text(), nullable=True))
    op.alter_column("meal_logs", "product_id", existing_type=sa.UUID(), nullable=True)
    op.create_check_constraint(
        "ck_meal_logs_product_ref", "meal_logs", "num_nonnulls(product_id, off_barcode) = 1"
    )
    op.create_check_constraint(
        "ck_meal_logs_grade", "meal_logs", "grade in ('A', 'B', 'C', 'D', 'E')"
    )


def downgrade() -> None:
    # OFF-only logs cannot satisfy NOT NULL product_id: they are removed on downgrade.
    op.execute("DELETE FROM meal_logs WHERE product_id IS NULL")
    op.drop_constraint("ck_meal_logs_grade", "meal_logs", type_="check")
    op.drop_constraint("ck_meal_logs_product_ref", "meal_logs", type_="check")
    op.alter_column("meal_logs", "product_id", existing_type=sa.UUID(), nullable=False)
    op.drop_column("meal_logs", "grade")
    op.drop_column("meal_logs", "product_name")
    op.drop_column("meal_logs", "off_barcode")
