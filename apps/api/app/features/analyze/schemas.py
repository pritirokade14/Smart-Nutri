from typing import Any, Literal
from uuid import UUID

from pydantic import BaseModel, Field, model_validator

from app.core.errors import ApiError
from app.features.products.schemas import ProductOut

VerdictStatus = Literal["ok", "caution", "unknown", "avoid"]

# Plan 5: at most 10 members per account.
MAX_MEMBERS = 10


class AnalyzeRequest(BaseModel):
    """Exactly one product reference: our own ``product_id``, or a ``barcode`` (OFF products
    have no product_id). With no ``member_ids`` the account's primary member is used."""

    product_id: UUID | None = None
    barcode: str | None = Field(default=None, max_length=64)
    member_ids: list[UUID] | None = Field(default=None, max_length=MAX_MEMBERS)
    language: Literal["en", "hi", "mr"] = "en"  # reserved for explanations (M3); unused in M1

    @model_validator(mode="after")
    def _exactly_one_product_ref(self) -> "AnalyzeRequest":
        if (self.product_id is None) == (self.barcode is None):
            raise ApiError("invalid_product_ref", 422)
        return self


class ReasonOut(BaseModel):
    code: str
    severity: VerdictStatus
    params: dict[str, Any]


class VerdictOut(BaseModel):
    member_id: UUID
    member_name: str
    status: VerdictStatus
    reasons: list[ReasonOut]


class AnalyzeOut(BaseModel):
    scan_id: UUID
    product: ProductOut
    # Product-level report from the rules engine (same shape as the public report).
    report: dict
    # One verdict per member, in request order. Only from app.scoring.analyze.
    verdicts: list[VerdictOut]
    explanation: str | None = None  # filled from M3 (F7); always null in M1
    tips: list[str] = []
