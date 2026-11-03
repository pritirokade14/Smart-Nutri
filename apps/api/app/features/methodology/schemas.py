from enum import StrEnum
from typing import Any

from pydantic import BaseModel, Field


class MethodologyLanguage(StrEnum):
    EN = "en"
    HI = "hi"
    MR = "mr"


class MethodologySource(BaseModel):
    id: str
    title: str = Field(description="Document title as published (a citation, not UI prose).")
    url: str | None
    url_verified: bool = Field(
        description="False until a person has checked the link. Clients must not present an "
        "unverified link as authoritative."
    )


class MethodologySection(BaseModel):
    """One part of "How we score". Clients render `methodology.section.<id>.*` strings; the
    API sends no prose."""

    id: str
    threshold_sources: list[str] | None = Field(
        description="Source ids for the numbers. Null: a member preference with nothing to cite."
    )
    rationale_sources: list[str] | None = Field(
        description="Source ids for why the rule exists. Null as for threshold_sources."
    )
    thresholds: dict[str, Any] = Field(
        description="The live rule values from the rules engine config (shape differs per "
        "section). Never written by hand."
    )


class Methodology(BaseModel):
    version: str = Field(description="Changes whenever any shown value changes.")
    language: MethodologyLanguage
    pending_clinician_review: bool
    sections: list[MethodologySection]
    sources: list[MethodologySource]
