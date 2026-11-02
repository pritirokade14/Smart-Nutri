from __future__ import annotations

import json
from pathlib import Path

from app.scoring.models import Category, Diet, Member, Nutrients, Product

FIXTURES = Path(__file__).parents[4] / "packages" / "test-fixtures"


def _read(kind: str, name: str) -> dict:
    return json.loads((FIXTURES / kind / f"{name}.json").read_text(encoding="utf-8"))


def load_product(name: str) -> Product:
    d = _read("products", name)
    return Product(
        name=d["name"],
        category=Category(d.get("category", "general")),
        per_100g=Nutrients(**d.get("per_100g", {})),
        serving_size_g=d.get("serving_size_g"),
        ingredients=tuple(d.get("ingredients", ())),
        allergen_statement=d.get("allergen_statement"),
        may_contain_statement=d.get("may_contain_statement"),
        claims=tuple(d.get("claims", ())),
        veg_mark=d.get("veg_mark"),
        contains_sweeteners=d.get("contains_sweeteners", False),
    )


def load_member(member_id: str) -> Member:
    d = _read("members", member_id)
    return Member(
        id=d["id"],
        name=d["name"],
        age=d.get("age"),
        diet=Diet(d.get("diet", "non_veg")),
        allergens=tuple(d.get("allergens", ())),
        conditions=tuple(d.get("conditions", ())),
        goal=d.get("goal"),
    )


def expected_cases() -> list[tuple[str, str, dict]]:
    cases = []
    for path in sorted((FIXTURES / "expected").glob("*.json")):
        product, member = path.stem.split(".", 1)
        cases.append((product, member, json.loads(path.read_text(encoding="utf-8"))))
    return cases
