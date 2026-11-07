"""The default meal slots, loaded from `defaults.yaml` (Plan 11 Ruling E4)."""

from dataclasses import dataclass
from datetime import time
from pathlib import Path

import yaml


@dataclass(frozen=True, slots=True)
class DefaultSlot:
    label_key: str
    position: int
    start: time
    end: time


def _hhmm(value: str) -> time:
    hh, mm = value.split(":")
    return time(int(hh), int(mm))


def _load() -> tuple[tuple[DefaultSlot, ...], int, int]:
    raw = yaml.safe_load((Path(__file__).parent / "defaults.yaml").read_text(encoding="utf-8"))
    slots = tuple(
        DefaultSlot(s["label_key"], i, _hhmm(s["start"]), _hhmm(s["end"]))
        for i, s in enumerate(raw["slots"])
    )
    return slots, int(raw["max_active"]), int(raw["label_max_chars"])


DEFAULT_SLOTS, MAX_ACTIVE_SLOTS, LABEL_MAX_CHARS = _load()
