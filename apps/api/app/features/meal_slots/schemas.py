from typing import Literal
from uuid import UUID

from pydantic import BaseModel, Field

_HHMM = r"^([01]\d|2[0-3]):[0-5]\d$"


class TimeWindow(BaseModel):
    start: str = Field(pattern=_HHMM)
    end: str = Field(pattern=_HHMM)


class MealSlotOut(BaseModel):
    id: UUID
    member_id: UUID
    position: int
    label_key: str | None  # an i18n key for a default slot
    custom_label: str | None  # user text: shown as typed, never translated
    default_time_window: TimeWindow | None
    is_default: bool
    archived: bool


class MealSlotsOut(BaseModel):
    items: list[MealSlotOut]
    suggested_slot_id: UUID  # the server's pick for the current moment: clients preselect it


class MealSlotCreateIn(BaseModel):
    member_id: UUID | None = None
    custom_label: str  # user text, 1-30 code points after trimming (never echoed in errors)
    default_time_window: TimeWindow | None = None
    client_id: UUID | None = None  # offline idempotency


class MealSlotRenameIn(BaseModel):
    """Partial update: null means unchanged (Ruling E10); use the clear flags to remove."""

    custom_label: str | None = None
    default_time_window: TimeWindow | None = None
    clear_custom_label: bool = False  # a default slot goes back to its translated name
    clear_time_window: bool = False


class MealSlotsOrderIn(BaseModel):
    member_id: UUID | None = None
    ids: list[UUID] = Field(min_length=1, max_length=6)  # every active slot, once, in order


class MealSlotsListOut(BaseModel):
    items: list[MealSlotOut]


class ArchiveOut(BaseModel):
    result: Literal["archived", "deleted"]
