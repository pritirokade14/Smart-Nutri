"""Write the golden API responses for packages/test-fixtures (read by the Android and web tests).

Run from apps/api:
  uv run python scripts/export_fixture_responses.py

Writes packages/test-fixtures/responses/:
  index.json                 fixture name -> fixed UUID (products, members, scans), reference date
  analyze/<product>.json     POST /v1/analyze for the product and EVERY fixture member
                             (verdicts in sorted member-name order)
  public/<product>.json      GET /v1/products/{barcode}/public for the product

The responses come from the same service functions the endpoints run (in-memory records, no
database), so they cannot drift from the API. Output is deterministic: fixed UUIDs
(uuid5(NAMESPACE_URL, ...)), a fixed reference date for ages, sorted keys, indent 2 and a
trailing newline. Never edit the files by hand; tests/api/analyze/test_shared_fixtures.py
fails when they are stale.
"""

from __future__ import annotations

import json
import shutil
import sys
from dataclasses import fields
from datetime import date
from pathlib import Path
from uuid import NAMESPACE_URL, UUID, uuid5

sys.path.insert(0, str(Path(__file__).parents[1]))

from app.features.analyze import service as analyze_service
from app.features.members.models import Member
from app.features.products import service as products_service
from app.features.products.models import Product
from tests.fixtures.loader import FIXTURES, load_member, load_product

# Ages in members/*.json are turned into birth years against this fixed date, and the same
# date is used as "today" for the engine, so the golden files never change on 1 January.
REFERENCE_DATE = date(2026, 1, 1)


def fixture_id(kind: str, name: str) -> UUID:
    return uuid5(NAMESPACE_URL, f"https://smartnutri.app/test-fixtures/{kind}/{name}")


FIXTURE_ACCOUNT_ID = fixture_id("account", "family")


def fixture_product_record(name: str, fixtures: Path = FIXTURES) -> Product:
    """An in-memory `products` row (own catalogue, verified) for products/<name>.json."""
    p = load_product(name, fixtures)
    if p.contains_sweeteners:
        raise ValueError(f"{name}: the products table has no contains_sweeteners column")
    per_100g = {
        f.name: getattr(p.per_100g, f.name)
        for f in fields(p.per_100g)
        if getattr(p.per_100g, f.name) is not None
    }
    record = Product(
        id=fixture_id("product", name),
        barcode=None,
        name=p.name,
        brand=None,
        category=p.category.value,
        per_100g=per_100g,
        serving_size_g=p.serving_size_g,
        ingredients_text=", ".join(p.ingredients) or None,
        allergen_statement=p.allergen_statement,
        may_contain_statement=p.may_contain_statement,
        claims=list(p.claims),
        veg_mark=p.veg_mark,
        source="user",
        extraction_confidence=p.extraction_confidence,
        verification_status="verified",
    )
    if products_service.record_to_product(record) != p:
        raise ValueError(f"{name}: does not survive the products-table round trip")
    return record


def fixture_member_record(
    member_id: str,
    *,
    account_id: UUID = FIXTURE_ACCOUNT_ID,
    reference: date = REFERENCE_DATE,
    fixtures: Path = FIXTURES,
) -> Member:
    """An in-memory `members` row for members/<member_id>.json (birth_year = reference - age)."""
    m = load_member(member_id, fixtures)
    return Member(
        id=fixture_id("member", member_id),
        account_id=account_id,
        name=m.name,
        relation="other",
        birth_year=None if m.age is None else reference.year - m.age,
        diet=m.diet.value,
        allergens=list(m.allergens),
        conditions=list(m.conditions),
        custom_alerts=[],
        goal=m.goal,
        is_primary=False,
    )


def _dump(data: object) -> str:
    return json.dumps(data, indent=2, sort_keys=True, ensure_ascii=False) + "\n"


def build(fixtures: Path = FIXTURES) -> dict[str, str]:
    """Relative path -> file content for every golden response."""
    products = sorted(p.stem for p in (fixtures / "products").glob("*.json"))
    member_names = sorted(m.stem for m in (fixtures / "members").glob("*.json"))
    members = [fixture_member_record(m, fixtures=fixtures) for m in member_names]
    out: dict[str, str] = {}
    for name in products:
        found = products_service.lookup_from_record(fixture_product_record(name, fixtures))
        result = analyze_service.evaluate(found, members, today=REFERENCE_DATE)
        analyzed = analyze_service.to_analyze_out(
            found, members, result, scan_id=fixture_id("scan", name)
        )
        out[f"analyze/{name}.json"] = _dump(analyzed.model_dump(mode="json"))
        public = products_service.to_public_out(found)
        out[f"public/{name}.json"] = _dump(public.model_dump(mode="json"))
    out["index.json"] = _dump(
        {
            "reference_date": REFERENCE_DATE.isoformat(),
            "account_id": str(FIXTURE_ACCOUNT_ID),
            "products": {p: str(fixture_id("product", p)) for p in products},
            "members": {m: str(fixture_id("member", m)) for m in member_names},
            "scans": {p: str(fixture_id("scan", p)) for p in products},
        }
    )
    return out


def write(out_dir: Path, fixtures: Path = FIXTURES) -> list[str]:
    """Replace ``out_dir`` with the golden responses; returns the relative paths written."""
    files = build(fixtures)
    if out_dir.exists():
        shutil.rmtree(out_dir)
    for rel, content in files.items():
        path = out_dir / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
    return sorted(files)


def main() -> int:
    written = write(FIXTURES / "responses")
    print(f"wrote {len(written)} files to packages/test-fixtures/responses/")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
