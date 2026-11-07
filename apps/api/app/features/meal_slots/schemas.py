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
