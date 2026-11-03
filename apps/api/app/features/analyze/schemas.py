from typing import Any, Literal
from uuid import UUID

from pydantic import BaseModel, Field, field_validator, model_validator

from app.core.errors import ApiError
from app.features.members.schemas import Relation
from app.features.products.schemas import ProductOut

VerdictStatus = Literal["ok", "caution", "unknown", "avoid"]
Language = Literal["en", "hi", "mr"]

# Plan 5: at most 10 members per account.
MAX_MEMBERS = 10


class AnalyzeRequest(BaseModel):
    """Exactly one product reference: our own ``product_id``, or a ``barcode`` (OFF products
    have no product_id). With no ``member_ids`` every member of the account is analysed, the
    primary (the account holder) first. Any unknown or foreign id is a 404."""

    product_id: UUID | None = None
    barcode: str | None = Field(default=None, max_length=64)
    member_ids: list[UUID] | None = Field(default=None, max_length=MAX_MEMBERS)
    # Language of the AI explanation (F7). Verdicts and reasons are codes, never prose.
    language: Language = "en"

    @field_validator("member_ids")
    @classmethod
    def _unique_member_ids(cls, value: list[UUID] | None) -> list[UUID] | None:
        if value is not None and len(set(value)) != len(value):
            raise ValueError("member_ids must be unique")
        return value

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
    relation: Relation = Field(description="Display only (headline wording); never affects status.")
    is_primary: bool = Field(
        description="The account holder: clients say 'for you'. Display only; never affects status."
    )
    status: VerdictStatus
    reasons: list[ReasonOut]
    profile_set_up: bool = Field(
        description=(
            "False: age/allergies/diet may not be set; clients show a 'profile not set up' "
            "note. Display metadata only; never changes status or reasons."
        )
    )


class ExplanationOut(BaseModel):
    """The AI explanation (F7). It explains the verdicts and never changes them.

    `source == "unavailable"` (text null, no tips): no `ai_processing` consent, or the model
    failed, timed out or disagreed with the engine. Clients then hide the explanation.
    `text` and `tips` refer to people only as `member_1`, `member_2`, ...; clients replace
    each token with that member's name (or "you") using `member_refs`.
    """

    text: str | None
    tips: list[str] = Field(max_length=3)
    language: Language
    source: Literal["llm", "unavailable"]
    prompt_version: str
    member_refs: dict[str, UUID] = Field(
        description="`member_N` token -> member_id (a member in `verdicts`). Empty when unavailable."
    )


class AnalyzeOut(BaseModel):
    scan_id: UUID
    product: ProductOut
    # Product-level report from the rules engine (same shape as the public report).
    report: dict
    # One verdict per member: request order, or (no member_ids) the primary first, then the
    # other members in creation order. Reasons are most severe first. Only from
    # app.scoring.analyze.
    verdicts: list[VerdictOut]
    explanation: ExplanationOut
