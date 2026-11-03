import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import DateTime, ForeignKey, Index, Text, func, text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base

# One scan per uploaded label photo per account (R21d; migration 0002_scans_path_unique).
SCAN_PATH_INDEX = "uq_scans_account_id_image_path"


class Scan(Base):
    __tablename__ = "scans"
    __table_args__ = (
        Index(
            SCAN_PATH_INDEX,
            "account_id",
            "image_path",
            unique=True,
            postgresql_where=text("image_path IS NOT NULL"),
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()")
    )
    account_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("accounts.id", ondelete="CASCADE"), index=True
    )
    product_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("products.id", ondelete="SET NULL")
    )
    image_path: Mapped[str | None] = mapped_column(Text)
    image_sha256: Mapped[str | None] = mapped_column(Text, index=True)
    analysis: Mapped[dict[str, Any] | None] = mapped_column(JSONB)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
