from typing import Literal

from pydantic import BaseModel


class ConsentIn(BaseModel):
    purpose: Literal["terms", "health_data", "ai_processing"]
    version: str
    granted: bool


class ConsentState(BaseModel):
    purpose: str
    version: str | None
    granted: bool
    current_version: str
