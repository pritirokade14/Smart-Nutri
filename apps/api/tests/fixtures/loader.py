from __future__ import annotations

import json
from dataclasses import fields
from pathlib import Path

from app.scoring.models import Category, Diet, Member, Nutrients, Product

FIXTURES = Path(__file__).parents[4] / "packages" / "test-fixtures"

PRODUCT_META_KEYS = frozenset({"source"})
MEMBER_META_KEYS: frozenset[str] = frozenset()


def _names(cls: type) -> set[str]:
    return {f.name for f in fields(cls)}


def _read(kind: str, name: str, base: Path | None = None) -> tuple[dict, Path]:
    path = (base or FIXTURES) / kind / f"{name}.json"
    return json.loads(path.read_text(encoding="utf-8")), path


def _check_keys(d: dict, allowed: set[str] | frozenset[str], path: Path, where: str = "") -> None:
    unknown = sorted(set(d) - set(allowed))
    if unknown:
        raise ValueError(f"{path}: unknown key(s) {unknown}{where}")


def _require(d: dict, key: str, path: Path) -> str:
    if key not in d:
        raise ValueError(f"{path}: missing required key '{key}'")
    return d[key]


def load_product(name: str, base: Path | None = None) -> Product:
    d, path = _read("products", name, base)
    _check_keys(d, _names(Product) | PRODUCT_META_KEYS, path)
    _check_keys(d.get("per_100g", {}), _names(Nutrients), path, " in per_100g")
    kwargs = {k: v for k, v in d.items() if k not in PRODUCT_META_KEYS}
    kwargs["category"] = Category(_require(d, "category", path))
    kwargs["per_100g"] = Nutrients(**d.get("per_100g", {}))
    for key in ("ingredients", "claims"):
        if key in kwargs:
            kwargs[key] = tuple(kwargs[key])
    return Product(**kwargs)


def load_member(member_id: str, base: Path | None = None) -> Member:
    d, path = _read("members", member_id, base)
    _check_keys(d, _names(Member) | MEMBER_META_KEYS, path)
    kwargs = dict(d)
    kwargs["diet"] = Diet(_require(d, "diet", path))
    for key in ("allergens", "conditions", "custom_alerts"):
        if key in kwargs:
            kwargs[key] = tuple(kwargs[key])
    return Member(**kwargs)


def expected_cases() -> list[tuple[str, str, dict]]:
    cases = []
    for path in sorted((FIXTURES / "expected").glob("*.json")):
        product, member = path.stem.split(".", 1)
        cases.append((product, member, json.loads(path.read_text(encoding="utf-8"))))
    return cases
