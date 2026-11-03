from typing import Literal

from pydantic import BaseModel, Field


class ConsentIn(BaseModel):
    purpose: Literal["terms", "health_data", "ai_processing"]
    version: str
    granted: bool


class ConsentState(BaseModel):
    purpose: str
    version: str | None
    granted: bool
    current_version: str
    needs_update: bool = Field(
        description=(
            "True when the latest grant is unwithdrawn but at an older version: the client "
            "shows the updated text and asks again. False when never granted or withdrawn."
        )
    )
