from datetime import datetime
from typing import Annotated, Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, StringConstraints, field_validator

ReportReason = Literal["wrong_values", "wrong_ingredients", "wrong_product", "other"]
MAX_NOTE_CHARS = 500


class ReportCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    reason: ReportReason
    note: Annotated[
        str | None, StringConstraints(max_length=MAX_NOTE_CHARS, strip_whitespace=True)
    ] = None

    @field_validator("note")
    @classmethod
    def _blank_is_none(cls, value: str | None) -> str | None:
        return value or None


class ReportOut(BaseModel):
    id: UUID
    product_id: UUID
    reason: ReportReason
    status: Literal["open", "resolved"]
    created_at: datetime
