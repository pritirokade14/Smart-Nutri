"""One scan per uploaded label photo per account (Ruling R21d).

Revision ID: 0002_scans_path_unique
Revises: 0001_baseline
Create Date: 2026-11-03

A unique partial index on scans (account_id, image_path) where image_path is not null, so
concurrent first posts of the same upload path cannot create two scan rows (the API returns
the existing scan when its insert hits this index). Barcode scans (no path) are not
constrained. An index only: no table, so no RLS or grant change (ADR 0009).

Before applying to a database that already has duplicate (account_id, image_path) rows, keep
the oldest of each and delete the rest; dev had none when this was written.
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "0002_scans_path_unique"
down_revision: str | Sequence[str] | None = "0001_baseline"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

INDEX = "uq_scans_account_id_image_path"


def upgrade() -> None:
    op.create_index(
        INDEX,
        "scans",
        ["account_id", "image_path"],
        unique=True,
        postgresql_where=sa.text("image_path IS NOT NULL"),
    )


def downgrade() -> None:
    op.drop_index(INDEX, table_name="scans")
