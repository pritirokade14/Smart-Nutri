import importlib.util
from datetime import time
from pathlib import Path

from app.features.meal_slots.defaults import (
    DEFAULT_SLOTS,
    LABEL_MAX_CHARS,
    MAX_ACTIVE_SLOTS,
    DefaultSlot,
)


def _in(slot: DefaultSlot, minute: int) -> bool:
    s = slot.start.hour * 60 + slot.start.minute
    e = slot.end.hour * 60 + slot.end.minute
    return s <= minute <= e if s <= e else minute >= s or minute <= e


def test_defaults_cover_every_minute_once():
    for minute in range(1440):
        hits = [s.label_key for s in DEFAULT_SLOTS if _in(s, minute)]
        assert len(hits) == 1, (minute, hits)


def test_default_bands_and_limits():
    bands = {s.label_key: (s.start, s.end) for s in DEFAULT_SLOTS}
    assert bands == {
        "diary.slot.breakfast": (time(4, 0), time(10, 59)),
        "diary.slot.lunch": (time(11, 0), time(15, 59)),
        "diary.slot.snack": (time(16, 0), time(18, 59)),
        "diary.slot.dinner": (time(19, 0), time(3, 59)),
    }
    assert [s.position for s in DEFAULT_SLOTS] == [0, 1, 2, 3]
    assert MAX_ACTIVE_SLOTS == 6
    assert LABEL_MAX_CHARS == 30


def test_migration_constants_equal_yaml():
    path = Path(__file__).resolve().parents[3] / "alembic/versions/0009_diary_days_slots_entries.py"
    spec = importlib.util.spec_from_file_location("migration_0009", path)
    mig = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mig)
    from_yaml = tuple(
        (s.label_key, s.position, s.start.strftime("%H:%M"), s.end.strftime("%H:%M"))
        for s in DEFAULT_SLOTS
    )
    assert mig.DEFAULT_SLOT_ROWS == from_yaml
