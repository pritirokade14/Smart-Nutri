"""Loads the bundled rule data (YAML) for the scoring engine."""

from __future__ import annotations

import functools
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

_DEFAULT_DIR = Path(__file__).parent / "data"


@dataclass(frozen=True)
class ScoringConfig:
    allergens: Mapping[str, Mapping[str, list[str]]]
    diet: Mapping[str, list[str]]
    ingredient_lists: Mapping[str, list[str]]
    thresholds: Mapping[str, Any]


def _read(path: Path) -> Any:
    with path.open(encoding="utf-8") as f:
        return yaml.safe_load(f)


def _load(data_dir: Path) -> ScoringConfig:
    return ScoringConfig(
        allergens=_read(data_dir / "allergens.yaml"),
        diet=_read(data_dir / "diet.yaml"),
        ingredient_lists=_read(data_dir / "ingredients.yaml"),
        thresholds=_read(data_dir / "thresholds.yaml"),
    )


@functools.cache
def _load_default() -> ScoringConfig:
    return _load(_DEFAULT_DIR)


def load_config(data_dir: Path | None = None) -> ScoringConfig:
    """Load config; the default bundled data is cached."""
    if data_dir is None:
        return _load_default()
    return _load(data_dir)
