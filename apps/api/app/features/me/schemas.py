from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel


class MeOut(BaseModel):
    id: UUID
    email: str | None
    display_name: str | None
    language: Literal["en", "hi", "mr"]
    created_at: datetime
