import uuid
from datetime import datetime

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Integer,
    Numeric,
    Text,
    func,
    text,
)
from sqlalchemy.dialects.postgresql import ARRAY, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base

RELATIONS = ("self", "child", "parent", "spouse", "other")
DIETS = ("veg", "eggetarian", "vegan", "jain", "non_veg")
SEXES = ("female", "male", "other")


class Member(Base):
    __tablename__ = "members"
    __table_args__ = (
        CheckConstraint(
            "relation in ('self', 'child', 'parent', 'spouse', 'other')", name="relation"
        ),
        CheckConstraint("diet in ('veg', 'eggetarian', 'vegan', 'jain', 'non_veg')", name="diet"),
        CheckConstraint("sex in ('female', 'male', 'other')", name="sex"),
        CheckConstraint("birth_year between 1900 and 2100", name="birth_year"),
        CheckConstraint("height_cm > 0 and height_cm <= 300", name="height_cm"),
        CheckConstraint("weight_kg > 0 and weight_kg <= 500", name="weight_kg"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()")
    )
    account_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("accounts.id", ondelete="CASCADE"), index=True
    )
    name: Mapped[str] = mapped_column(Text)
    relation: Mapped[str] = mapped_column(Text)
    birth_year: Mapped[int | None] = mapped_column(Integer)
    sex: Mapped[str | None] = mapped_column(Text)
    height_cm: Mapped[float | None] = mapped_column(Numeric(asdecimal=False))
    weight_kg: Mapped[float | None] = mapped_column(Numeric(asdecimal=False))
    diet: Mapped[str] = mapped_column(Text, server_default="non_veg")
    allergens: Mapped[list[str]] = mapped_column(ARRAY(Text), server_default="{}")
    conditions: Mapped[list[str]] = mapped_column(ARRAY(Text), server_default="{}")
    custom_alerts: Mapped[list[str]] = mapped_column(ARRAY(Text), server_default="{}")
    goal: Mapped[str | None] = mapped_column(Text)
    is_primary: Mapped[bool] = mapped_column(Boolean, server_default=text("false"))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
