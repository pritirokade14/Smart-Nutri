"""Loads the bundled rule data (YAML) for the scoring engine."""

from __future__ import annotations

import functools
from collections.abc import Mapping
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml

_DEFAULT_DIR = Path(__file__).parent / "data"


@dataclass(frozen=True)
class ScoringConfig:
    allergens: Mapping[str, Mapping[str, list[str]]]
    diet: Mapping[str, list[str]]
    # Term lists, plus `custom_alerts`: {key: {"terms": [...], "exclude": [...]}}.
    ingredient_lists: Mapping[str, Any]
    thresholds: Mapping[str, Any]
    # Daily-guide constants (targets.yaml). Read only by app.scoring.targets, never by verdicts.
    targets: Mapping[str, Any] = field(default_factory=lambda: _load_default_targets())


def _read(path: Path) -> Any:
    with path.open(encoding="utf-8") as f:
        return yaml.safe_load(f)


def _load(data_dir: Path) -> ScoringConfig:
    return ScoringConfig(
        allergens=_read(data_dir / "allergens.yaml"),
        diet=_read(data_dir / "diet.yaml"),
        ingredient_lists=_read(data_dir / "ingredients.yaml"),
        thresholds=_read(data_dir / "thresholds.yaml"),
        targets=_read(data_dir / "targets.yaml"),
    )


@functools.cache
def _load_default_targets() -> Mapping[str, Any]:
    return _read(_DEFAULT_DIR / "targets.yaml")


@functools.cache
def _load_default() -> ScoringConfig:
    return _load(_DEFAULT_DIR)


def load_config(data_dir: Path | None = None) -> ScoringConfig:
    """Load config; the default bundled data is cached."""
    if data_dir is None:
        return _load_default()
    return _load(data_dir)
