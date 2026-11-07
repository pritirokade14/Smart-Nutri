"""Which slot a new entry goes to (Plan 11 Task 2; spec 5.12). Pure."""

from collections.abc import Sequence
from dataclasses import dataclass
from datetime import time
from uuid import UUID


@dataclass(frozen=True, slots=True)
class SlotWindow:
    start: time
    end: time  # inclusive minutes; start > end wraps past midnight


@dataclass(frozen=True, slots=True)
class SlotChoice:
    id: UUID
    position: int
    window: SlotWindow | None


def _minute(t: time) -> int:
    return t.hour * 60 + t.minute


def window_contains(w: SlotWindow, at: time) -> bool:
    start, end, minute = _minute(w.start), _minute(w.end), _minute(at)
    if start <= end:
        return start <= minute <= end
    return minute >= start or minute <= end


def pick_slot(active: Sequence[SlotChoice], at: time) -> UUID:
    """The default slot for a wall-clock time (spec 5.12), in order:

    1. the active slot whose window contains ``at`` (lowest position on overlap);
    2. else the active slot whose window starts latest before ``at`` on the same clock day;
    3. else the lowest-position active slot.

    A slot without a window is only ever picked by rule 3. ValueError for no active slot.
    """
    if not active:
        raise ValueError("no active meal slot")
    ordered = sorted(active, key=lambda s: (s.position, str(s.id)))
    for slot in ordered:
        if slot.window is not None and window_contains(slot.window, at):
            return slot.id
    minute = _minute(at)
    before = [s for s in ordered if s.window is not None and _minute(s.window.start) <= minute]
    if before:
        # max() keeps the first (lowest position) of equal starts.
        return max(before, key=lambda s: _minute(s.window.start)).id  # type: ignore[union-attr]
    return ordered[0].id
